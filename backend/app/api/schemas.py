import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# Auth
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = "recruiter"


# Candidates
class CandidateCreate(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    current_location: str | None = None
    preferred_location: str | None = None
    availability: str | None = None
    status: str = "Active Bench"
    total_experience: str | None = None
    primary_skill: str | None = None
    secondary_skills: list[str] = Field(default_factory=list)
    notes: str | None = None


class CandidateUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    current_location: str | None = None
    preferred_location: str | None = None
    availability: str | None = None
    status: str | None = None
    total_experience: str | None = None
    primary_skill: str | None = None
    secondary_skills: list[str] | None = None
    notes: str | None = None


class CandidateOut(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    current_location: str | None
    preferred_location: str | None
    availability: str | None
    status: str
    total_experience: str | None
    primary_skill: str | None
    secondary_skills: list | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    resume_count: int = 0

    model_config = {"from_attributes": True}


# Resumes
class ResumeOut(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    name: str
    resume_type: str
    parsed_text: str | None
    skills_extracted: list | None
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# Submissions
class SubmissionCreate(BaseModel):
    candidate_id: uuid.UUID
    resume_id: uuid.UUID
    job_description: str
    jd_title: str | None = None
    status: str = "Draft"


class SubmissionUpdate(BaseModel):
    status: str | None = None
    summary: str | None = None


class SubmissionOut(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    resume_id: uuid.UUID
    recruiter_id: uuid.UUID
    ats_score: int
    ats_score_before: int
    summary: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    candidate_name: str | None = None
    resume_name: str | None = None
    recruiter_name: str | None = None
    jd_title: str | None = None

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_candidates: int
    active_bench: int
    total_recruiters: int
    submissions_this_month: int
    interview_count: int
    placement_count: int


class ActivityOut(BaseModel):
    id: uuid.UUID
    action: str
    entity_type: str
    entity_id: str | None
    metadata_json: dict | None
    created_at: datetime
    user_name: str | None = None

    model_config = {"from_attributes": True}
