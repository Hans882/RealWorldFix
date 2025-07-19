import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
from . import models, database, auth, schemas
from fastapi import File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
from .clustering.embedder import embed_descriptions
from .clustering.clusterer import cluster_reports
import pymysql
import numpy as np

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from .database import get_db
from .utils.pdf_generator import generate_weekly_digest_pdf

router = APIRouter()


models.Base.metadata.create_all(bind=database.engine)

import os
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../backend/.env'))

os.makedirs("uploads", exist_ok=True)  # Ensure uploads/ exists


app = FastAPI()
get_db = auth.get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load ML model once at startup
model = load_model("report_classifier.keras")
classes = ['flood', 'garbage', 'road']


@app.get("/")
def root():
    return {"message": "Welcome to the API"}

@app.post("/signup", response_model=schemas.UserOut)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = auth.hash_password(user.password)
    new_user = models.User(name=user.name, email=user.email, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/vote", response_model=schemas.VoteResponse)
def vote(vote: schemas.VoteCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Check if vote already exists
    existing_vote = db.query(models.Vote).filter(models.Vote.user_id == current_user.id, models.Vote.report_id == vote.report_id).first()
    if existing_vote:
        raise HTTPException(status_code=400, detail="User has already voted for this report")
    new_vote = models.Vote(user_id=current_user.id, report_id=vote.report_id)
    db.add(new_vote)
    db.commit()
    db.refresh(new_vote)

    # Count votes for the report
    upvote_count = db.query(models.Vote).filter(models.Vote.report_id == vote.report_id).count()

    return {"upvotes": upvote_count}

@app.get("/has_voted/{report_id}")
def has_voted(report_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    vote = db.query(models.Vote).filter_by(user_id=current_user.id, report_id=report_id).first()
    return {"has_voted": vote is not None}

@app.get("/vote_count/{report_id}")
def vote_count(report_id: int, db: Session = Depends(get_db)):
    count = db.query(models.Vote).filter(models.Vote.report_id == report_id).count()
    return {"upvotes": count}


@app.post("/login", response_model=schemas.Token)
def login(login_data: schemas.LoginData, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if not user or not auth.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    logger.info(f"User {user.email} logged in with role: {user.role}")
    access_token = auth.create_access_token(data={"sub": user.email,"role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@app.get("/me", response_model=schemas.UserOut)
def get_me(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Count reports submitted by the user
    reports_count = db.query(models.Report).filter(models.Report.user_id == current_user.id).count()
    # Count votes (community support) given by the user
    votes_count = db.query(models.Vote).filter(models.Vote.user_id == current_user.id).count()

    # Return user data with counts
    return schemas.UserOut(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        reports_submitted=reports_count,
        community_support_given=votes_count
    )

from fastapi import File, UploadFile

from fastapi import Form

@app.post("/submit-report", response_model=schemas.ReportOut)
def submit_report(
    title: str = Form(...),
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    category: str = Form(None),
    status: str = Form("Pending"),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    logger.info(f"User {current_user.email} is submitting a report with title: {title} and category: {category}")
    # Save image locally
    image_path = f"uploads/{image.filename}"
    with open(image_path, "wb") as buffer:
        buffer.write(image.file.read())

    # Auto-predict category if not provided
    if not category:
        try:
            img = Image.open(image_path).convert("RGB").resize((224, 224))
            arr = np.expand_dims(np.array(img) / 255.0, axis=0)
            pred = model.predict(arr)
            category = classes[np.argmax(pred)]
            logger.info(f"Auto-predicted category: {category}")
        except Exception as e:
            logger.warning(f"ML prediction failed, defaulting to 'Uncategorized': {e}")
            category = "Uncategorized"

    # Store record
    new_report = models.Report(
        user_id=current_user.id,
        title=title,
        description=description,
        image_url=image_path,
        latitude=latitude,
        longitude=longitude,
        category=category,
        status=status,
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    # Add upvotes attribute for response schema compatibility
    new_report.upvotes = 0
    logger.info(f"Report {new_report.id} created successfully by user {current_user.email}")
    return new_report

@app.get("/reports", response_model=List[schemas.ReportOut])
def get_reports(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    reports = db.query(models.Report).all()
    report_data = []
    for report in reports:
        upvotes = db.query(models.Vote).filter(models.Vote.report_id == report.id).count()
        report_dict = report.__dict__.copy()
        if report_dict.get("image_url") and not report_dict["image_url"].startswith("http"):
            report_dict["image_url"] = "/" + report_dict["image_url"].lstrip("/")
        report_dict["upvotes"] = upvotes
        # Add cluster_id to the response dictionary
        report_dict["cluster_id"] = report.cluster_id
        report_data.append(report_dict)
    return report_data

@app.patch("/reports/{report_id}/status")
def update_status(report_id: int, status: str, db: Session = Depends(get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = status
    db.commit()
    return {"message": "Status updated"}

@app.patch("/reports/{report_id}/category")
def update_category(report_id: int, category: str, db: Session = Depends(get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.category = category
    db.commit()
    return {"message": "Category updated"}

@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    try:
        image = Image.open(file.file).convert("RGB").resize((224, 224))
        img_array = np.array(image) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        prediction = model.predict(img_array)
        predicted_class = classes[np.argmax(prediction)]
        confidence = float(np.max(prediction))

        return {
            "prediction": predicted_class,
            "confidence": round(confidence, 3)
        }

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")



def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="RealWorldFix API",
        version="1.0.0",
        description="JWT Auth + Swagger UI enabled",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", []).append({"bearerAuth": []})
    app.openapi_schema = openapi_schema
    return app.openapi_schema

load_dotenv()

def create_admin_user():
    db: Session = database.SessionLocal()
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        print("⚠️ Admin credentials not found in environment variables.")
        return

    existing = db.query(models.User).filter_by(email=admin_email).first()
    if not existing:
        new_admin = models.User(
            name="Admin",
            email=admin_email,
            hashed_password=auth.hash_password(admin_password),
            role="admin"
        )
        db.add(new_admin)
        db.commit()
        print("✅ Admin user created.")
    else:
        print("ℹ️ Admin user already exists.")

create_admin_user()

from fastapi import Depends
from sqlalchemy.orm import Session

def get_unclustered_descriptions(db: Session = Depends(get_db)):
    rows = db.query(models.Report.id, models.Report.description).filter(models.Report.cluster_id == None).all()
    ids = [row.id for row in rows]
    descriptions = [row.description for row in rows]
    return ids, descriptions

# Removed direct call to get_unclustered_descriptions() at module level

# Example embedding print removed from module level

def fetch_unclustered_reports(db: Session = Depends(get_db)):
    rows = db.query(models.Report.id, models.Report.description, models.Report.latitude, models.Report.longitude).filter(models.Report.cluster_id == None).all()
    return rows

# Step 2: Embed + Cluster
# Removed direct call to fetch_unclustered_reports() at module level

# Removed direct call to save_cluster_ids() at module level

print("✅ Clustering complete.")

from fastapi.responses import FileResponse

# Import send_digest_email utility
from .utils.email_utils import send_digest_email

@app.get("/admin/digest-pdf", response_class=FileResponse)
def download_digest_pdf(db: Session = Depends(get_db)):
    pdf_path = generate_weekly_digest_pdf(db)
    return FileResponse(pdf_path, media_type="application/pdf", filename="weekly_digest.pdf")


from fastapi import HTTPException   

@router.get("/admin/send-digest")
def email_weekly_digest(db: Session = Depends(get_db)):
    logger.info("Received request to /admin/send-digest")
    pdf_path = generate_weekly_digest_pdf(db)
    logger.info(f"Generated PDF at path: {pdf_path}")
    result = send_digest_email(pdf_path)
    logger.info(f"Email sending result: {result}")
    if result.get("success"):
        return {"message": result.get("message", "✅ Digest emailed to city officials")}
    else:
        logger.error(f"Failed to send email: {result.get('message')}")
        raise HTTPException(status_code=500, detail=result.get("message", "Failed to send email"))


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:3000", "http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routes import admin_cluster
app.include_router(admin_cluster.router)
app.include_router(router)



app.openapi = custom_openapi

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

