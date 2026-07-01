import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.schemas import CandidateCreate, CandidateOut, CandidateUpdate
from app.auth.deps import get_current_user, require_admin
from app.db.models import Candidate, CandidateStatus, Resume, User
from app.db.session import get_db
from app.services.audit import log_activity
from app.storage.local import storage

router = APIRouter(prefix="/candidates", tags=["candidates"])


def _candidate_out(c: Candidate, db: Session) -> CandidateOut:
    count = db.query(func.count(Resume.id)).filter(Resume.candidate_id == c.id).scalar() or 0
    out = CandidateOut.model_validate(c)
    out.status = c.status.value if hasattr(c.status, "value") else str(c.status)
    out.resume_count = count
    return out


@router.get("", response_model=list[CandidateOut])
def list_candidates(
    q: str | None = Query(None),
    skill: str | None = Query(None),
    location: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Candidate)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Candidate.first_name.ilike(like),
                Candidate.last_name.ilike(like),
                Candidate.email.ilike(like),
                Candidate.primary_skill.ilike(like),
            )
        )
    if skill:
        query = query.filter(Candidate.primary_skill.ilike(f"%{skill}%"))
    if location:
        query = query.filter(
            or_(
                Candidate.current_location.ilike(f"%{location}%"),
                Candidate.preferred_location.ilike(f"%{location}%"),
            )
        )
    if status:
        try:
            query = query.filter(Candidate.status == CandidateStatus(status))
        except ValueError:
            pass
    candidates = query.order_by(Candidate.updated_at.desc()).all()
    return [_candidate_out(c, db) for c in candidates]


@router.post("", response_model=CandidateOut)
def create_candidate(
    body: CandidateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    try:
        st = CandidateStatus(body.status)
    except ValueError:
        st = CandidateStatus.active_bench
    c = Candidate(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        phone=body.phone,
        current_location=body.current_location,
        preferred_location=body.preferred_location,
        availability=body.availability,
        status=st,
        total_experience=body.total_experience,
        primary_skill=body.primary_skill,
        secondary_skills=body.secondary_skills,
        notes=body.notes,
        created_by_id=user.id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    log_activity(db, user, "create_candidate", "candidate", c.id, {"name": f"{c.first_name} {c.last_name}"})
    return _candidate_out(c, db)


@router.get("/{candidate_id}", response_model=CandidateOut)
def get_candidate(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = db.get(Candidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    return _candidate_out(c, db)


@router.patch("/{candidate_id}", response_model=CandidateOut)
def update_candidate(
    candidate_id: uuid.UUID,
    body: CandidateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    c = db.get(Candidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    data = body.model_dump(exclude_unset=True)
    if "status" in data and data["status"]:
        try:
            data["status"] = CandidateStatus(data["status"])
        except ValueError:
            del data["status"]
    for k, v in data.items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    log_activity(db, user, "update_candidate", "candidate", c.id)
    return _candidate_out(c, db)


@router.delete("/{candidate_id}")
def delete_candidate(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    c = db.get(Candidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    name = f"{c.first_name} {c.last_name}"
    for resume in list(c.resumes):
        for key in (resume.storage_key_docx, resume.storage_key_pdf):
            if key:
                try:
                    storage.delete(key)
                except OSError:
                    pass
    db.delete(c)
    db.commit()
    log_activity(db, user, "delete_candidate", "candidate", candidate_id, {"name": name})
    return {"ok": True}
