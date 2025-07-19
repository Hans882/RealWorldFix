# backend/app/utils/pdf_generator.py

from fpdf import FPDF
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .. import models
from sqlalchemy import func

class DigestPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Weekly Civic Issue Digest", ln=True, align="C")
        self.ln(5)

    def add_area_section(self, area_name, reports):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, f"Area: {area_name}", ln=True)
        self.set_font("Arial", "", 10)
        for report, vote_count in reports:
            self.multi_cell(0, 8,
                f"- [{report.category}] {report.description[:100]}...\n"
                f"  Votes: {vote_count} | Cluster: {report.cluster_id or 'N/A'}",
                border=0
            )
        self.ln(5)

import os

def generate_weekly_digest_pdf(db: Session, file_path="weekly_digest.pdf"):
    uploads_dir = os.path.join(os.path.dirname(__file__), "../../uploads")
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    file_path = os.path.join(uploads_dir, "weekly_digest.pdf")

    pdf = DigestPDF()
    pdf.add_page()

    # Add date range
    today = datetime.today()
    start_date = (today - timedelta(days=7)).strftime("%B %d")
    end_date = today.strftime("%B %d, %Y")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"Date Range: {start_date} - {end_date}", ln=True)
    pdf.ln(5)

    # Query top reports by latitude and longitude (group by location)
    locations = db.query(models.Report.latitude, models.Report.longitude).distinct().all()
    for (latitude, longitude) in locations:
        top_reports = (
            db.query(models.Report, func.count(models.Vote.id).label("vote_count"))
            .filter(models.Report.latitude == latitude, models.Report.longitude == longitude)
            .outerjoin(models.Vote, models.Vote.report_id == models.Report.id)
            .group_by(models.Report.id)
            .order_by(func.count(models.Vote.id).desc())
            .limit(5)
            .all()
        )
        area_name = f"Lat: {latitude:.4f}, Lon: {longitude:.4f}"
        pdf.add_area_section(area_name, top_reports)

    # Save
    pdf.output(file_path)
    return file_path
