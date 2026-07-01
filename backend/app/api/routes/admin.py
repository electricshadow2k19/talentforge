from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.api.schemas import ActivityOut, DashboardStats, UserCreate, UserOut
from app.auth.deps import get_current_user, require_admin
from app.auth.security import hash_password
from app.db.models import Activity, Candidate, CandidateStatus, Submission, SubmissionStatus, User, UserRole
from app.db.session import get_db
from app.services.audit import log_activity

router = APIRouter(tags=["admin"])


def _stats(db: Session) -> DashboardStats:
    now = datetime.now(timezone.utc)
    month = now.month
    year = now.year
    return DashboardStats(
        total_candidates=db.query(func.count(Candidate.id)).scalar() or 0,
        active_bench=db.query(func.count(Candidate.id))
        .filter(Candidate.status == CandidateStatus.active_bench)
        .scalar()
        or 0,
        total_recruiters=db.query(func.count(User.id)).filter(User.role == UserRole.recruiter).scalar() or 0,
        submissions_this_month=db.query(func.count(Submission.id))
        .filter(extract("month", Submission.created_at) == month)
        .filter(extract("year", Submission.created_at) == year)
        .scalar()
        or 0,
        interview_count=db.query(func.count(Submission.id))
        .filter(Submission.status.in_([SubmissionStatus.interview, SubmissionStatus.submitted]))
        .scalar()
        or 0,
        placement_count=db.query(func.count(Submission.id))
        .filter(Submission.status == SubmissionStatus.placed)
        .scalar()
        or 0,
    )


@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _stats(db)


@router.get("/activities", response_model=list[ActivityOut])
def list_activities(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    rows = db.query(Activity).order_by(Activity.created_at.desc()).limit(50).all()
    out = []
    for a in rows:
        o = ActivityOut.model_validate(a)
        o.user_name = a.user.name if a.user else None
        out.append(o)
    return out


@router.get("/recruiters", response_model=list[UserOut])
def list_recruiters(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    rows = db.query(User).filter(User.role == UserRole.recruiter).order_by(User.name).all()
    return [_user_out(r) for r in rows]


@router.post("/recruiters", response_model=UserOut)
def create_recruiter(body: UserCreate, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(400, "Email already exists")
    r = User(
        email=body.email.lower(),
        name=body.name,
        role=UserRole.recruiter,
        password_hash=hash_password(body.password),
        is_active=True,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    log_activity(db, user, "create_recruiter", "user", r.id)
    return _user_out(r)


def _user_out(u: User) -> UserOut:
    out = UserOut.model_validate(u)
    out.role = u.role.value if hasattr(u.role, "value") else str(u.role)
    return out
