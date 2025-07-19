from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    reports_submitted: int = 0
    community_support_given: int = 0

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str 

class LoginData(BaseModel):
    email: str
    password: str

class ReportCreate(BaseModel):
    title: str
    description: str
    latitude: float
    longitude: float

class ReportOut(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    image_url: str
    latitude: float
    longitude: float
    created_at: datetime  # ← make sure this is a datetime, not str
    upvotes: int
    category: Optional[str]  # NEW
    status: Optional[str]    # NEW
    cluster_id: Optional[int] = None

    class Config:
        orm_mode = True

class VoteCreate(BaseModel):
    report_id: int

class VoteOut(BaseModel):
    id: int
    user_id: int
    report_id: int

    class Config:
        orm_mode = True

class VoteResponse(BaseModel):
    upvotes: int


