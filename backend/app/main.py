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
    if settings.database_url.startswith("sqlite"):
        from app.db.base import Base
        from app.db import models  # noqa: F401
        from app.db.session import engine

        Base.metadata.create_all(bind=engine)
    else:
        import subprocess
        import sys

        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=False)
    try:
        from scripts.seed import seed

        seed()
    except Exception:
        pass


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
