import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas import ResumeOut
from app.auth.deps import get_current_user, require_admin
from app.db.models import Candidate, Resume, User
from app.db.session import get_db
from app.parsers.document import extract_text_from_bytes
from app.services.analyzers import analyze_resume
from app.services.audit import log_activity
from app.storage.local import storage

router = APIRouter(prefix="/candidates/{candidate_id}/resumes", tags=["resumes"])


@router.get("", response_model=list[ResumeOut])
def list_resumes(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.get(Candidate, candidate_id):
        raise HTTPException(404, "Candidate not found")
    rows = db.query(Resume).filter(Resume.candidate_id == candidate_id).order_by(Resume.created_at.desc()).all()
    return [ResumeOut.model_validate(r) for r in rows]


@router.post("", response_model=ResumeOut)
async def upload_resume(
    candidate_id: uuid.UUID,
    name: str = Form(...),
    resume_type: str = Form(...),
    is_default: bool = Form(False),
    file: UploadFile | None = File(None),
    parsed_text: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    if not db.get(Candidate, candidate_id):
        raise HTTPException(404, "Candidate not found")

    text = parsed_text or ""
    docx_key = pdf_key = None

    if file and file.filename:
        data = await file.read()
        text = extract_text_from_bytes(data, file.filename)
        r = Resume(
            candidate_id=candidate_id,
            name=name,
            resume_type=resume_type,
            parsed_text=text,
            is_default=is_default,
        )
        db.add(r)
        db.flush()
        ext = file.filename.rsplit(".", 1)[-1].lower()
        key = storage.key_for_resume(candidate_id, r.id, ext)
        storage.save(key, data)
        if ext == "pdf":
            pdf_key = key
        else:
            docx_key = key
        r.storage_key_docx = docx_key
        r.storage_key_pdf = pdf_key
    else:
        if not text.strip():
            raise HTTPException(400, "Provide file or parsed_text")
        r = Resume(
            candidate_id=candidate_id,
            name=name,
            resume_type=resume_type,
            parsed_text=text,
            is_default=is_default,
        )
        db.add(r)

    profile = analyze_resume(text)
    r.skills_extracted = profile.skills

    if is_default:
        db.query(Resume).filter(Resume.candidate_id == candidate_id, Resume.id != r.id).update(
            {"is_default": False}
        )

    db.commit()
    db.refresh(r)
    log_activity(db, user, "upload_resume", "resume", r.id, {"candidate_id": str(candidate_id), "name": name})
    return ResumeOut.model_validate(r)


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(
    candidate_id: uuid.UUID,
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = db.query(Resume).filter(Resume.id == resume_id, Resume.candidate_id == candidate_id).first()
    if not r:
        raise HTTPException(404, "Resume not found")
    return ResumeOut.model_validate(r)


@router.get("/{resume_id}/file")
def download_resume_file(
    candidate_id: uuid.UUID,
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from fastapi.responses import Response

    r = db.query(Resume).filter(Resume.id == resume_id, Resume.candidate_id == candidate_id).first()
    if not r:
        raise HTTPException(404, "Resume not found")
    key = r.storage_key_docx or r.storage_key_pdf
    if not key:
        raise HTTPException(404, "No file stored for this resume")
    data = storage.read(key)
    ext = key.rsplit(".", 1)[-1].lower()
    media = "application/pdf" if ext == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return Response(content=data, media_type=media, headers={"Content-Disposition": f'inline; filename="{r.name}.{ext}"'})


@router.patch("/{resume_id}", response_model=ResumeOut)
def update_resume(
    candidate_id: uuid.UUID,
    resume_id: uuid.UUID,
    is_default: bool = Query(False),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    r = db.query(Resume).filter(Resume.id == resume_id, Resume.candidate_id == candidate_id).first()
    if not r:
        raise HTTPException(404, "Resume not found")
    if is_default:
        db.query(Resume).filter(Resume.candidate_id == candidate_id).update({"is_default": False})
        r.is_default = True
    db.commit()
    db.refresh(r)
    log_activity(db, user, "update_resume", "resume", r.id)
    return ResumeOut.model_validate(r)


@router.delete("/{resume_id}")
def delete_resume(
    candidate_id: uuid.UUID,
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    r = db.query(Resume).filter(Resume.id == resume_id, Resume.candidate_id == candidate_id).first()
    if not r:
        raise HTTPException(404, "Resume not found")
    for key in (r.storage_key_docx, r.storage_key_pdf):
        if key:
            try:
                storage.delete(key)
            except OSError:
                pass
    db.delete(r)
    db.commit()
    log_activity(db, user, "delete_resume", "resume", resume_id, {"candidate_id": str(candidate_id)})
    return {"ok": True}
