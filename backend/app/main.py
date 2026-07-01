import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, candidates, resumes, submissions
from app.config import settings
from app.models.schemas import GeneratePackageResponse, HealthResponse, TextInputRequest
from app.parsers.document import extract_text_from_bytes
from app.services.pipeline import run_pipeline


def _bootstrap_db() -> None:
    """Create tables and seed on cold start (serverless / first deploy)."""
    try:
        from app.db.base import Base
        from app.db import models  # noqa: F401
        from app.db.session import engine

        Base.metadata.create_all(bind=engine)

        from app.auth.security import hash_password
        from app.db.models import Candidate, CandidateStatus, Resume, User, UserRole
        from app.db.session import SessionLocal
        from app.services.analyzers import analyze_resume

        sample_resume = """RAJ KUMAR
Senior DevOps Engineer | raj.kumar@email.com | Dallas, TX
PROFESSIONAL SUMMARY
DevOps Engineer with 10 years in AWS, Kubernetes, Terraform, CI/CD.
SKILLS: AWS, Terraform, Kubernetes, Docker, Jenkins, Python
EXPERIENCE
Northrop Grumman — DevOps Engineer | 2020–2026
- Built CI/CD pipelines with Jenkins and Terraform on AWS EKS"""

        db = SessionLocal()
        try:
            if db.query(User).filter(User.email == "admin@genvenx.com").first():
                return
            admin = User(
                email="admin@genvenx.com",
                name="Admin User",
                role=UserRole.admin,
                password_hash=hash_password("admin123"),
            )
            recruiter = User(
                email="hira@genvenx.com",
                name="Hira Recruiter",
                role=UserRole.recruiter,
                password_hash=hash_password("recruiter123"),
            )
            db.add_all([admin, recruiter])
            db.flush()
            cand = Candidate(
                first_name="Raj",
                last_name="Kumar",
                email="raj.kumar@email.com",
                primary_skill="DevOps",
                status=CandidateStatus.active_bench,
                created_by_id=admin.id,
            )
            db.add(cand)
            db.flush()
            parsed = analyze_resume(sample_resume)
            db.add(
                Resume(
                    candidate_id=cand.id,
                    name="DevOps Resume",
                    resume_type="DevOps",
                    parsed_text=sample_resume,
                    skills_extracted=parsed.skills,
                    is_default=True,
                )
            )
            db.commit()
        finally:
            db.close()
    except Exception:
        pass  # never block API startup on bootstrap errors


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _bootstrap_db()
    yield


app = FastAPI(
    title="TalentForge API",
    description="AI-Powered Recruiter Operating System for Staffing Companies",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(candidates.router, prefix="/api")
app.include_router(resumes.router, prefix="/api")
app.include_router(submissions.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse)
def health():
    ai = bool(settings.openai_api_key and settings.use_ai)
    return HealthResponse(status="ok", ai_enabled=ai, model=settings.openai_model)


@app.post("/api/generate-package", response_model=GeneratePackageResponse)
async def generate_package(
    job_description: str | None = Form(None),
    resume: str | None = Form(None),
    jd_file: UploadFile | None = File(None),
    resume_file: UploadFile | None = File(None),
):
    """Legacy anonymous endpoint — prefer /api/submissions/analyze when authenticated."""
    start = time.perf_counter()
    jd_text = job_description or ""
    resume_text = resume or ""
    if jd_file and jd_file.filename:
        data = await jd_file.read()
        jd_text = extract_text_from_bytes(data, jd_file.filename)
    if resume_file and resume_file.filename:
        data = await resume_file.read()
        resume_text = extract_text_from_bytes(data, resume_file.filename)
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description is required")
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume is required")
    result, mode = run_pipeline(jd_text.strip(), resume_text.strip())
    elapsed = time.perf_counter() - start
    return GeneratePackageResponse(**result, processing_mode=mode, elapsed_seconds=round(elapsed, 2))


@app.post("/api/generate-package/json", response_model=GeneratePackageResponse)
def generate_package_json(body: TextInputRequest):
    start = time.perf_counter()
    result, mode = run_pipeline(body.job_description.strip(), body.resume.strip())
    elapsed = time.perf_counter() - start
    return GeneratePackageResponse(**result, processing_mode=mode, elapsed_seconds=round(elapsed, 2))
