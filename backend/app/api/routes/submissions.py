import time
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas import SubmissionOut, SubmissionUpdate
from app.api.serialize import to_jsonable
from app.auth.deps import get_current_user
from app.db.models import Candidate, JobDescription, Resume, Submission, SubmissionStatus, User
from app.db.session import get_db
from app.parsers.document import extract_text_from_bytes
from app.services.analyzers import analyze_jd
from app.services.audit import log_activity
from app.services.pipeline import run_pipeline

router = APIRouter(prefix="/submissions", tags=["submissions"])


def _submission_out(s: Submission, db: Session) -> SubmissionOut:
    cand = db.get(Candidate, s.candidate_id)
    res = db.get(Resume, s.resume_id)
    rec = db.get(User, s.recruiter_id)
    jd = s.job_description if hasattr(s, "job_description") else None
    jd_title = None
    if s.jd_id:
        from app.db.models import JobDescription as JD

        j = db.get(JD, s.jd_id)
        jd_title = j.title if j else None
    out = SubmissionOut.model_validate(s)
    out.status = s.status.value if hasattr(s.status, "value") else str(s.status)
    out.candidate_name = f"{cand.first_name} {cand.last_name}" if cand else None
    out.resume_name = res.name if res else None
    out.recruiter_name = rec.name if rec else None
    out.jd_title = jd_title
    return out


@router.get("", response_model=list[SubmissionOut])
def list_submissions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.query(Submission).order_by(Submission.created_at.desc()).limit(100).all()
    return [_submission_out(s, db) for s in rows]


@router.get("/{submission_id}", response_model=SubmissionOut)
def get_submission(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    s = db.get(Submission, submission_id)
    if not s:
        raise HTTPException(404, "Submission not found")
    return _submission_out(s, db)


@router.patch("/{submission_id}", response_model=SubmissionOut)
def update_submission(
    submission_id: uuid.UUID,
    body: SubmissionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    s = db.get(Submission, submission_id)
    if not s:
        raise HTTPException(404, "Submission not found")
    if body.status:
        try:
            s.status = SubmissionStatus(body.status)
        except ValueError:
            raise HTTPException(400, "Invalid status")
    if body.summary is not None:
        s.summary = body.summary
    db.commit()
    db.refresh(s)
    log_activity(db, user, "update_submission", "submission", s.id, {"status": body.status})
    return _submission_out(s, db)


@router.post("/analyze", response_model=dict)
async def analyze_and_create(
    candidate_id: str | None = Form(None),
    resume_id: str | None = Form(None),
    job_description: str | None = Form(None),
    resume_text: str | None = Form(None),
    resume_file: UploadFile | None = File(None),
    jd_file: UploadFile | None = File(None),
    status: str = Form("Draft"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Run full pipeline and persist submission record.

    Resume source (one of):
      - candidate_id + resume_id (from database)
      - resume_text (paste)
      - resume_file (DOCX/PDF/TXT upload)
    """
    jd_text = job_description or ""
    jd_filename = None
    if jd_file and jd_file.filename:
        data = await jd_file.read()
        jd_text = extract_text_from_bytes(data, jd_file.filename)
        jd_filename = jd_file.filename

    if not jd_text.strip():
        raise HTTPException(400, "Job description required")

    # Resolve resume text
    cand: Candidate | None = None
    resume: Resume | None = None
    parsed_resume = ""

    if candidate_id and resume_id:
        try:
            cid = uuid.UUID(candidate_id)
            rid = uuid.UUID(resume_id)
        except ValueError:
            raise HTTPException(400, "Invalid candidate or resume ID")
        cand = db.get(Candidate, cid)
        resume = db.query(Resume).filter(Resume.id == rid, Resume.candidate_id == cid).first()
        if not cand or not resume:
            raise HTTPException(404, "Candidate or resume not found")
        if not resume.parsed_text:
            raise HTTPException(400, "Resume has no parsed text")
        parsed_resume = resume.parsed_text.strip()
    elif resume_text and resume_text.strip():
        parsed_resume = resume_text.strip()
    elif resume_file and resume_file.filename:
        data = await resume_file.read()
        parsed_resume = extract_text_from_bytes(data, resume_file.filename).strip()
    else:
        raise HTTPException(400, "Resume required: select from database, paste text, or upload file")

    if not parsed_resume:
        raise HTTPException(400, "Resume text is empty")

    start = time.perf_counter()
    result, mode = run_pipeline(jd_text.strip(), parsed_resume)
    elapsed = time.perf_counter() - start

    jd_analysis = result["jd_analysis"]
    jd_row = JobDescription(
        title=jd_analysis.title,
        raw_text=jd_text.strip(),
        structured_json=to_jsonable(jd_analysis),
        source_filename=jd_filename,
        created_by_id=user.id,
    )
    db.add(jd_row)
    db.flush()

    try:
        st = SubmissionStatus(status)
    except ValueError:
        st = SubmissionStatus.draft

    package = to_jsonable({**result, "processing_mode": mode, "elapsed_seconds": round(elapsed, 2)})

    # Ad-hoc runs without DB candidate still create a submission when possible
    if not cand or not resume:
        # Use first candidate as placeholder or skip persistence for pure ad-hoc
        sub = None
        log_activity(
            db,
            user,
            "analyze_adhoc",
            "pipeline",
            None,
            {"ats": package.get("ats_score", {}).get("overall", 0), "mode": mode},
        )
        db.commit()
        return {"submission_id": None, **package}

    sub = Submission(
        candidate_id=cand.id,
        resume_id=resume.id,
        jd_id=jd_row.id,
        recruiter_id=user.id,
        ats_score=package.get("ats_score", {}).get("overall", 0),
        ats_score_before=package.get("ats_score_before", 0),
        package_json=package,
        summary=package.get("generated_sections", {}).get("client_submission_summary"),
        status=st,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    log_activity(
        db,
        user,
        "create_submission",
        "submission",
        sub.id,
        {"ats": sub.ats_score, "candidate": f"{cand.first_name} {cand.last_name}"},
    )

    return {"submission_id": str(sub.id), **package}


@router.get("/{submission_id}/package")
def get_submission_package(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    s = db.get(Submission, submission_id)
    if not s or not s.package_json:
        raise HTTPException(404, "Submission package not found")
    return s.package_json
