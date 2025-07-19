from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")  # "admin" or "user"


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(String)
    image_url = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    category = Column(String, default="Uncategorized")  # NEW
    status = Column(String, default="Pending")          # NEW
    cluster_id = Column(Integer, nullable=True)

class Vote(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    report_id = Column(Integer, ForeignKey("reports.id"))

    __table_args__ = (UniqueConstraint('user_id', 'report_id', name='_user_report_uc'),)


