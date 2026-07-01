"""Step 5 — gap analysis."""

from app.models.schemas import ATSScore, GapAnalysis, JDAnalysis, ResumeAnalysis
from app.services.keywords import keyword_in_text


def build_gap_analysis(
    jd: JDAnalysis,
    resume: ResumeAnalysis,
    ats: ATSScore,
    resume_text: str,
) -> GapAnalysis:
    text = resume_text.lower()
    suggestions: list[str] = []

    missing_skills = [
        s for s in jd.required_skills
        if not keyword_in_text(s, resume_text)
    ]
    missing_tech = [
        t for t in (jd.devops_tools + jd.cloud_platforms + jd.programming_languages)
        if not keyword_in_text(t, resume_text)
    ]
    missing_certs = [
        c for c in jd.certifications
        if c.lower() not in text and not any(word in text for word in c.lower().split()[:2])
    ]
    missing_resp: list[str] = []
    for resp in jd.responsibilities:
        tokens = [w for w in resp.lower().split() if len(w) > 4][:4]
        if tokens and not any(t in text for t in tokens):
            missing_resp.append(resp[:80])

    if missing_skills:
        suggestions.append(
            f"Add verified {', '.join(missing_skills[:4])} to TECHNICAL SKILLS if candidate has experience."
        )
    if missing_tech:
        suggestions.append(
            f"Highlight existing experience with {', '.join(missing_tech[:4])} in relevant bullets."
        )
    if missing_resp:
        suggestions.append("Rephrase experience bullets to reflect JD responsibilities where truthful.")
    if ats.overall < 85:
        suggestions.append("Strengthen professional summary with top matching JD keywords.")
    suggestions.append("Recruiter: confirm all optimized keywords reflect actual candidate experience.")

    return GapAnalysis(
        missing_skills=missing_skills,
        missing_keywords=ats.missing_keywords,
        missing_technologies=missing_tech,
        missing_certifications=missing_certs,
        missing_responsibilities=missing_resp[:6],
        optimization_suggestions=suggestions[:6],
    )
