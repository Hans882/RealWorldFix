# routes/admin_cluster.py

from fastapi import APIRouter, Depends, HTTPException
from backend.app.database import SessionLocal, engine, Base, get_db
from sqlalchemy.orm import Session
from ..clustering.embedder import embed_descriptions
from ..clustering.clusterer import cluster_reports
import numpy as np
from backend.app import models
from ..utils.pdf_generator import generate_weekly_digest_pdf
from ..utils.email_utils import send_digest_email
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/admin/run-clustering")
def run_clustering(db: Session = Depends(get_db)):
    try:
        # 1. Fetch reports that are unclustered
        rows = db.query(models.Report.id, models.Report.description, models.Report.latitude, models.Report.longitude).filter(models.Report.cluster_id == None).all()

        if not rows:
            return {"message": "No unclustered reports found."}

        ids = [r.id for r in rows]
        descriptions = [r.description for r in rows]
        latitudes = np.array([r.latitude for r in rows])
        longitudes = np.array([r.longitude for r in rows])

        embeddings = embed_descriptions(descriptions)
        labels = cluster_reports(embeddings, latitudes, longitudes)

        # 2. Save cluster IDs
        for report_id, cluster_id in zip(ids, labels):
            if cluster_id != -1:
                report = db.query(models.Report).filter(models.Report.id == report_id).first()
                if report:
                    report.cluster_id = int(cluster_id)
        db.commit()

        return {"message": f"Clustering complete. {len(set(labels)) - (1 if -1 in labels else 0)} clusters created."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during clustering: {e}")
    
@router.get("/admin/send-digest")
def email_weekly_digest(db: Session = Depends(get_db)):
    logger.info("Received request to /admin/send-digest")
    try:
        pdf_path = generate_weekly_digest_pdf(db)
        logger.info(f"Generated PDF at path: {pdf_path}")
        result = send_digest_email(pdf_path)
        logger.info(f"Email sending result: {result}")
        if result.get("success"):
            return {"message": result.get("message", "✅ Digest emailed to city officials")}
        else:
            logger.error(f"Failed to send email: {result.get('message')}")
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to send email"))
    except Exception as e:
        logger.error(f"Unexpected error in email_weekly_digest: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
