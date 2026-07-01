import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


class UserRole(str, enum.Enum):
    admin = "admin"
    recruiter = "recruiter"


class CandidateStatus(str, enum.Enum):
    active_bench = "Active Bench"
    submitted = "Submitted"
    interview_scheduled = "Interview Scheduled"
    client_interview = "Client Interview"
    offer = "Offer"
    placed = "Placed"
    inactive = "Inactive"


class SubmissionStatus(str, enum.Enum):
    draft = "Draft"
    ready = "Ready"
    submitted = "Submitted"
    interview = "Interview"
    rejected = "Rejected"
    offer = "Offer"
    placed = "Placed"


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.recruiter)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    clerk_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    submissions: Mapped[list["Submission"]] = relationship(back_populates="recruiter")
    activities: Mapped[list["Activity"]] = relationship(back_populates="user")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    availability: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus), default=CandidateStatus.active_bench
    )
    total_experience: Mapped[str | None] = mapped_column(String(50), nullable=True)
    primary_skill: Mapped[str | None] = mapped_column(String(120), nullable=True)
    secondary_skills: Mapped[list | None] = mapped_column(JSONType, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    resumes: Mapped[list["Resume"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="candidate")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    resume_type: Mapped[str] = mapped_column(String(120))
    parsed_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_extracted: Mapped[list | None] = mapped_column(JSONType, default=list)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    storage_key_docx: Mapped[str | None] = mapped_column(String(512), nullable=True)
    storage_key_pdf: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidate: Mapped["Candidate"] = relationship(back_populates="resumes")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="resume")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text)
    structured_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    submissions: Mapped[list["Submission"]] = relationship(back_populates="job_description")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id"))
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id"))
    jd_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("job_descriptions.id"), nullable=True)
    recruiter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    ats_score: Mapped[int] = mapped_column(Integer, default=0)
    ats_score_before: Mapped[int] = mapped_column(Integer, default=0)
    package_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.draft)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    candidate: Mapped["Candidate"] = relationship(back_populates="submissions")
    resume: Mapped["Resume"] = relationship(back_populates="submissions")
    job_description: Mapped["JobDescription | None"] = relationship(back_populates="submissions")
    recruiter: Mapped["User"] = relationship(back_populates="submissions")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User | None"] = relationship(back_populates="activities")


class AppSetting(Base):
    __tablename__ = "settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(120), unique=True)
    value: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
