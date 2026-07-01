"""TalentForge 10-step recruiter workflow orchestrator."""

import json
from typing import Any

from openai import OpenAI

from app.config import settings
from app.models.schemas import (
    EmailDrafts,
    GeneratedSections,
    InterviewQuestions,
    JDAnalysis,
    ResumeAnalysis,
    SubmissionPackage,
)
from app.services.analyzers import analyze_jd, analyze_resume, strip_optimizer_banner
from app.services.ats_engine import compute_ats_score
from app.services.documents import build_documents
from app.services.gap_analysis import build_gap_analysis
from app.services.generators import (
    build_dashboard,
    build_emails,
    build_generated_sections,
    build_interview_questions,
    build_submission_package,
)
from app.services.optimizer import OPTIMIZER_RULES, optimize_resume
from app.services.temporal_validator import filter_keywords_for_role, run_temporal_audit

AI_SYSTEM_PROMPT = f"""You are TalentForge, a recruiter productivity AI for IT staffing (GenvenX).
{OPTIMIZER_RULES}
Never invent employers, dates, certifications, projects, or tools.
Return valid JSON matching the exact schema requested."""


def _ai_client() -> OpenAI | None:
    if not settings.openai_api_key or not settings.use_ai:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def _run_core_pipeline(jd_text: str, resume_text: str) -> dict[str, Any]:
    # Step 2 — JD analysis
    jd = analyze_jd(jd_text)
    # Step 3 — Resume parse (original)
    resume = analyze_resume(resume_text)
    # Step 4 — ATS on original (visa/citizenship excluded from scoring)
    ats_before = compute_ats_score(jd, resume, jd_text, resume_text)
    # Step 5 — Gap analysis on original
    gap_before = build_gap_analysis(jd, resume, ats_before, resume_text)
    # Step 6 — Temporal due diligence
    temporal_audit = run_temporal_audit(jd_text, jd, resume)
    # Step 7 — Optimize resume (respects temporal blocks)
    optimized = optimize_resume(resume_text, jd, ats_before, temporal_audit)
    optimized_resume = strip_optimizer_banner(optimized)
    if ats_before.missing_keywords:
        optimized = optimize_resume(optimized_resume, jd, ats_before, temporal_audit)
        optimized_resume = strip_optimizer_banner(optimized)
    # Re-score optimized resume
    ats_after = compute_ats_score(jd, analyze_resume(optimized_resume), jd_text, optimized_resume)
    gap_after = build_gap_analysis(jd, resume, ats_after, optimized_resume)
    # Step 7 — Generated sections
    sections = build_generated_sections(jd, resume, ats_after)
    # Submission package
    pkg = build_submission_package(sections, gap_after, ats_after, ats_before.overall)
    # Step 8 & 9 — Interview questions
    questions = build_interview_questions(jd, resume)
    emails = build_emails(jd, resume, sections, pkg)
    # Dashboard
    dashboard = build_dashboard(ats_after, ats_before.overall, gap_after)
    # Step 10 — Documents
    docs = build_documents(optimized_resume, sections, questions, pkg)

    return {
        "jd_analysis": jd,
        "resume_analysis": resume,
        "ats_score": ats_after,
        "ats_score_before": ats_before.overall,
        "gap_analysis": gap_after,
        "generated_sections": sections,
        "dashboard": dashboard,
        "original_resume": resume_text.strip(),
        "optimized_resume": optimized_resume,
        "submission_package": pkg,
        "interview_questions": questions,
        "email_drafts": emails,
        "documents": docs,
        "temporal_audit": temporal_audit,
    }


def generate_package_ai(jd_text: str, resume_text: str) -> dict[str, Any]:
    client = _ai_client()
    if not client:
        return _run_core_pipeline(jd_text, resume_text)

    prompt = f"""Analyze JD and resume. Return JSON with:
jd_analysis (structured fields), resume_analysis, optimized_resume (full text, TECHNICAL SKILLS with JD keywords),
generated_sections (professional_summary, key_strengths, top_matching_skills, technical_highlights, client_submission_summary),
interview_questions (technical/scenario/behavioral/client_specific as {{question, difficulty}}, recruiter_screening as strings).

JOB DESCRIPTION:
{jd_text[:12000]}

RESUME:
{resume_text[:12000]}
"""
    try:
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": AI_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        base = _run_core_pipeline(jd_text, resume_text)

        if data.get("jd_analysis"):
            base["jd_analysis"] = JDAnalysis(**data["jd_analysis"])
        if data.get("resume_analysis"):
            base["resume_analysis"] = ResumeAnalysis(**data["resume_analysis"])

        optimized = data.get("optimized_resume") or base["optimized_resume"]
        optimized_clean = strip_optimizer_banner(optimized)
        jd = base["jd_analysis"]
        temporal_audit = base.get("temporal_audit", [])
        from app.services.ats_engine import compute_ats_score as score

        ats_after = score(jd, analyze_resume(optimized_clean), jd_text, optimized_clean)
        if ats_after.missing_keywords:
            optimized_clean = strip_optimizer_banner(
                optimize_resume(optimized_clean, jd, ats_after, temporal_audit)
            )
            ats_after = score(jd, analyze_resume(optimized_clean), jd_text, optimized_clean)
        base["ats_score"] = ats_after
        base["optimized_resume"] = optimized_clean

        if data.get("generated_sections"):
            base["generated_sections"] = GeneratedSections(**data["generated_sections"])
        if data.get("interview_questions"):
            base["interview_questions"] = InterviewQuestions(**data["interview_questions"])
        if data.get("submission_package"):
            base["submission_package"] = SubmissionPackage(**data["submission_package"])
        if data.get("email_drafts"):
            base["email_drafts"] = EmailDrafts(**data["email_drafts"])

        gap = build_gap_analysis(jd, base["resume_analysis"], base["ats_score"], base["optimized_resume"])
        base["gap_analysis"] = gap
        base["dashboard"] = build_dashboard(base["ats_score"], base["ats_score_before"], gap)
        base["documents"] = build_documents(
            base["optimized_resume"],
            base["generated_sections"],
            base["interview_questions"],
            base["submission_package"],
        )
        return base
    except Exception:
        return _run_core_pipeline(jd_text, resume_text)


def run_pipeline(jd_text: str, resume_text: str) -> tuple[dict[str, Any], str]:
    if _ai_client():
        return generate_package_ai(jd_text, resume_text), "ai"
    return _run_core_pipeline(jd_text, resume_text), "heuristic"
