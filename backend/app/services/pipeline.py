import json
import re
from typing import Any

from openai import OpenAI

from app.config import settings
from app.models.schemas import (
    ATSScore,
    ATSSectionScore,
    EmailDrafts,
    GeneratePackageResponse,
    InterviewQuestions,
    JDAnalysis,
    ResumeAnalysis,
    SkillMatch,
    SubmissionPackage,
)

# Common tech skills for heuristic matching
TECH_SKILLS = [
    "AWS", "Azure", "GCP", "Terraform", "Kubernetes", "Docker", "Python", "Java",
    "Jenkins", "Git", "GitHub", "GitLab", "Ansible", "Chef", "Puppet", "Linux",
    "CI/CD", "DevOps", "SRE", "ECS", "EKS", "Lambda", "CloudFormation", "Helm",
    "ArgoCD", "Prometheus", "Grafana", "Datadog", "Splunk", "SQL", "PostgreSQL",
    "MySQL", "Oracle", "MongoDB", "Redis", "Kafka", "Spark", "Snowflake",
    "React", "Node.js", "TypeScript", "JavaScript", "Go", "Rust", "C#", ".NET",
    "Spring", "Microservices", "REST", "API", "Agile", "Scrum", "SAFe",
    "Security", "OWASP", "Fortify", "WAF", "DDoS", "Networking", "BGP", "DNS",
]

VISA_PATTERNS = [
    r"\b(USC|US Citizen)\b",
    r"\b(GC|Green Card)\b",
    r"\bH1B\b",
    r"\bOPT\b",
    r"\bCPT\b",
    r"\bTN\b",
    r"\bEAD\b",
    r"no\s+visa\s+sponsorship",
    r"visa\s+sponsorship",
]

WORK_MODE_PATTERNS = {
    "Remote": r"\bremote\b",
    "Hybrid": r"\bhybrid\b",
    "Onsite": r"\b(on-?site|onsite)\b",
}


def _normalize_skill(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def _find_skills_in_text(text: str) -> list[str]:
    found = []
    lower = text.lower()
    for skill in TECH_SKILLS:
        if skill.lower() in lower or skill.replace(".", "").lower() in lower:
            found.append(skill)
    return sorted(set(found), key=str.lower)


def _extract_experience_years(text: str) -> str | None:
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience",
        r"experience[:\s]+(\d+)\+?\s*years?",
        r"minimum\s+of\s+(\d+)\+?\s*years?",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return f"{m.group(1)}+ years"
    return None


def _extract_visa(text: str) -> list[str]:
    visas = []
    for p in VISA_PATTERNS:
        for m in re.finditer(p, text, re.I):
            visas.append(m.group(0).strip())
    return list(dict.fromkeys(visas))[:5]


def _extract_work_mode(text: str) -> str | None:
    for mode, pattern in WORK_MODE_PATTERNS.items():
        if re.search(pattern, text, re.I):
            return mode
    return None


def _extract_location(text: str) -> str | None:
    # City, ST pattern
    m = re.search(
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z]{2})\b",
        text,
    )
    if m:
        return f"{m.group(1)}, {m.group(2)}"
    m = re.search(r"location[:\s]+([^\n.]+)", text, re.I)
    if m:
        return m.group(1).strip()[:80]
    return None


def _extract_name_from_resume(text: str) -> str | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    first = lines[0]
    if len(first) < 50 and not re.search(r"@|http|resume|curriculum", first, re.I):
        return first
    return None


def _extract_email(text: str) -> str | None:
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    return m.group(0) if m else None


def _extract_phone(text: str) -> str | None:
    m = re.search(r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    return m.group(0) if m else None


def analyze_jd_heuristic(jd: str) -> JDAnalysis:
    skills = _find_skills_in_text(jd)
    mandatory = skills[: max(5, len(skills) // 2)] if skills else []
    nice = skills[len(mandatory) :] if len(skills) > len(mandatory) else []

    title = None
    for line in jd.splitlines()[:8]:
        if re.search(r"engineer|developer|architect|analyst|manager|consultant", line, re.I):
            title = line.strip()[:120]
            break

    return JDAnalysis(
        title=title,
        mandatory_skills=mandatory[:12],
        nice_to_have_skills=nice[:8],
        experience_years=_extract_experience_years(jd),
        visa_requirements=_extract_visa(jd),
        location=_extract_location(jd),
        work_mode=_extract_work_mode(jd),
        summary=jd[:400].replace("\n", " ").strip() + ("..." if len(jd) > 400 else ""),
    )


def analyze_resume_heuristic(resume: str) -> ResumeAnalysis:
    skills = _find_skills_in_text(resume)
    certs = []
    for line in resume.splitlines():
        if re.search(r"certif|AWS|Azure|GCP|CKA|CKAD|PMP|CSM|CSPO|Security\+", line, re.I):
            certs.append(line.strip()[:100])

    education = []
    for line in resume.splitlines():
        if re.search(r"bachelor|master|b\.?s\.?|m\.?s\.?|ph\.?d|university|college|degree", line, re.I):
            education.append(line.strip()[:120])

    return ResumeAnalysis(
        candidate_name=_extract_name_from_resume(resume),
        email=_extract_email(resume),
        phone=_extract_phone(resume),
        skills=skills,
        experience_years=_extract_experience_years(resume),
        certifications=certs[:6],
        education=education[:4],
        visa_status=", ".join(_extract_visa(resume)) or None,
        location=_extract_location(resume),
        summary=resume[:350].replace("\n", " ").strip(),
    )


def compute_ats_score(jd: JDAnalysis, resume: ResumeAnalysis, jd_text: str, resume_text: str) -> ATSScore:
    jd_skills = set(s.lower() for s in jd.mandatory_skills + jd.nice_to_have_skills)
    resume_skills = set(s.lower() for s in resume.skills)
    if not jd_skills:
        jd_skills = set(s.lower() for s in _find_skills_in_text(jd_text))

    matched = [s for s in jd_skills if s in resume_skills or s in resume_text.lower()]
    missing = [s for s in jd_skills if s not in matched]

    skill_matches = []
    for skill in jd.mandatory_skills:
        sk = skill.lower()
        in_resume = sk in resume_text.lower()
        skill_matches.append(
            SkillMatch(
                skill=skill,
                matched=in_resume,
                resume_evidence=skill if in_resume else None,
                jd_requirement="mandatory",
            )
        )

    skills_score = int((len(matched) / max(len(jd_skills), 1)) * 100) if jd_skills else 70
    keywords_score = min(100, skills_score + 5)
    exp_score = 85 if jd.experience_years and resume.experience_years else 75
    loc_score = 100
    if jd.location and resume.location:
        loc_score = 100 if jd.location.split(",")[-1].strip() in resume.location else 60

    sections = [
        ATSSectionScore(section="Skills", score=min(100, skills_score), notes=f"{len(matched)} matched"),
        ATSSectionScore(section="Experience", score=exp_score),
        ATSSectionScore(section="Keywords", score=keywords_score),
        ATSSectionScore(section="Location", score=loc_score),
    ]
    overall = int(sum(s.score for s in sections) / len(sections))

    return ATSScore(
        sections=sections,
        overall=overall,
        missing_keywords=[m.title() for m in missing[:10]],
        matched_keywords=[m.title() for m in matched[:15]],
        skill_matches=skill_matches,
    )


def optimize_resume_heuristic(resume: str, jd: JDAnalysis, ats: ATSScore) -> str:
    lines = resume.splitlines()
    optimized = list(lines)

    if ats.missing_keywords:
        insert_at = min(15, len(optimized))
        block = [
            "",
            "CORE COMPETENCIES (JD-ALIGNED)",
            "— " + " | ".join(ats.matched_keywords[:8]),
        ]
        related = {
            "terraform": "infrastructure as code",
            "ansible": "configuration management",
            "python": "scripting",
            "kubernetes": "container orchestration",
        }
        for kw in ats.missing_keywords[:3]:
            hint = related.get(kw.lower())
            if hint and hint in resume.lower():
                block.append(
                    f"— {kw}: experience via {hint} (expand with explicit {kw} projects)"
                )
        optimized = optimized[:insert_at] + block + optimized[insert_at:]

    text = "\n".join(optimized)
    jd_skills = [s.lower() for s in jd.mandatory_skills + jd.nice_to_have_skills]
    replacements = [
        ("Infrastructure as Code", "Terraform-based Infrastructure as Code (IaC)", "terraform"),
        ("container orchestration", "Kubernetes container orchestration", "kubernetes"),
        ("CI/CD pipelines", "CI/CD pipelines (Jenkins, GitHub Actions)", "jenkins"),
    ]
    for old, new, skill_key in replacements:
        if skill_key in jd_skills and re.search(re.escape(old), text, re.I):
            text = re.sub(re.escape(old), new, text, count=1, flags=re.I)

    header = [
        "--- TALENTFORGE OPTIMIZED RESUME (review before submission) ---",
        f"Target role: {jd.title or 'N/A'} | ATS alignment focus",
        "---",
        "",
    ]
    return "\n".join(header) + text


def build_submission_package(
    jd: JDAnalysis, resume: ResumeAnalysis, ats: ATSScore
) -> SubmissionPackage:
    name = resume.candidate_name or "Candidate"
    yrs = resume.experience_years or "several years"
    top_skills = ", ".join(resume.skills[:6]) or "relevant technical skills"
    summary = (
        f"{name} — {jd.title or 'Technology professional'} with {yrs} of experience "
        f"in {top_skills}. ATS match score: {ats.overall}%."
    )
    strengths = [f"Strong {s} background" for s in resume.skills[:4]]
    if resume.certifications:
        strengths.append(f"Certifications: {resume.certifications[0][:60]}")
    risks = [f"Gap: {m} not explicitly listed on resume" for m in ats.missing_keywords[:3]]
    if jd.visa_requirements and not resume.visa_status:
        risks.append("Confirm visa status against JD requirements")

    return SubmissionPackage(
        candidate_summary=summary,
        strengths=strengths[:5],
        risks=risks[:4],
        fit_statement=f"Recommended for submission with recruiter verification on: {', '.join(ats.missing_keywords[:3]) or 'none'}.",
    )


def build_interview_questions(jd: JDAnalysis, resume: ResumeAnalysis) -> InterviewQuestions:
    skills = jd.mandatory_skills[:5] or resume.skills[:5]
    technical = []
    for s in skills:
        if s.lower() == "terraform":
            technical.append("Explain Terraform state locking and how you prevent drift in team environments.")
        elif s.lower() == "kubernetes":
            technical.append("Difference between EKS and self-managed Kubernetes — when would you choose each?")
        elif s.lower() == "aws":
            technical.append("How do you design a highly available multi-AZ architecture on AWS?")
        else:
            technical.append(f"Describe a production project where you used {s} — architecture and outcomes.")

    scenario = [
        "How would you reduce cloud infrastructure cost by 20% without sacrificing reliability?",
        "Walk through an incident you handled — detection, triage, resolution, and postmortem.",
    ]
    client = [
        f"For this {jd.title or 'role'}, how would you ramp in the first 30 days?",
        "What questions do you have about the client's tech stack and team structure?",
    ]
    recruiter = [
        f"Rate your proficiency in {skills[0] if skills else 'primary skill'} (1-10)?",
        "Current location and willingness to relocate / work hybrid?",
        "Visa status and work authorization?",
        f"Rate {skills[1] if len(skills) > 1 else 'cloud'} experience (1-10)?",
        "Expected hourly rate or salary range?",
        "Earliest start date and notice period?",
    ]
    return InterviewQuestions(
        technical=technical[:5],
        scenario=scenario,
        client_specific=client,
        recruiter_screening=recruiter,
    )


def build_emails(
    jd: JDAnalysis, resume: ResumeAnalysis, pkg: SubmissionPackage
) -> EmailDrafts:
    name = resume.candidate_name or "Candidate"
    role = jd.title or "the position"
    vendor = (
        f"Subject: Submission — {name} for {role}\n\n"
        f"Hi,\n\n"
        f"Please find attached our candidate submission for {role}.\n\n"
        f"Summary: {pkg.candidate_summary}\n\n"
        f"Strengths:\n" + "\n".join(f"• {s}" for s in pkg.strengths) + "\n\n"
        f"Please confirm receipt and next steps.\n\n"
        f"Best regards,\nGenvenX Talent Team"
    )
    candidate = (
        f"Subject: Submission confirmation — {role}\n\n"
        f"Hi {name},\n\n"
        f"We have submitted your profile for {role}"
        f"{f' ({jd.location})' if jd.location else ''}.\n\n"
        f"Please review the optimized resume we used and let us know if any detail needs correction.\n"
        f"Prepare for screening — sample topics: {', '.join(jd.mandatory_skills[:4])}.\n\n"
        f"GenvenX Talent Team"
    )
    manager = (
        f"Subject: New submission — {name} / {role}\n\n"
        f"Recruiter notes:\n"
        f"• ATS match: {pkg.candidate_summary.split('ATS match score: ')[-1] if 'ATS match score' in pkg.candidate_summary else 'see system'}\n"
        f"• Risks: {'; '.join(pkg.risks) or 'None flagged'}\n"
        f"• Action: Schedule recruiter screen\n"
    )
    return EmailDrafts(vendor_email=vendor, candidate_email=candidate, manager_email=manager)


def generate_package_heuristic(jd_text: str, resume_text: str) -> dict[str, Any]:
    jd = analyze_jd_heuristic(jd_text)
    resume = analyze_resume_heuristic(resume_text)
    ats = compute_ats_score(jd, resume, jd_text, resume_text)
    optimized = optimize_resume_heuristic(resume_text, jd, ats)
    pkg = build_submission_package(jd, resume, ats)
    questions = build_interview_questions(jd, resume)
    emails = build_emails(jd, resume, pkg)
    return {
        "jd_analysis": jd,
        "resume_analysis": resume,
        "ats_score": ats,
        "optimized_resume": optimized,
        "submission_package": pkg,
        "interview_questions": questions,
        "email_drafts": emails,
    }


AI_SYSTEM_PROMPT = """You are TalentForge, a recruiter productivity AI for IT staffing (GenvenX).
Analyze job descriptions and resumes honestly. Never invent experience, employers, or certifications.
For resume optimization: only rephrase existing experience to align with JD keywords — do not add false claims.
Return valid JSON matching the exact schema requested."""


def _ai_client() -> OpenAI | None:
    if not settings.openai_api_key or not settings.use_ai:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def generate_package_ai(jd_text: str, resume_text: str) -> dict[str, Any]:
    client = _ai_client()
    if not client:
        return generate_package_heuristic(jd_text, resume_text)

    prompt = f"""Analyze this JD and resume. Return JSON with keys:
jd_analysis (title, mandatory_skills[], nice_to_have_skills[], experience_years, visa_requirements[], location, work_mode, rate_notes, summary),
resume_analysis (candidate_name, email, phone, skills[], experience_years, certifications[], education[], visa_status, location, summary),
ats_score (sections[{{section, score, notes}}], overall, missing_keywords[], matched_keywords[]),
optimized_resume (string — full resume text, JD-aligned rewrites only, no lies),
submission_package (candidate_summary, strengths[], risks[], fit_statement),
interview_questions (technical[], scenario[], client_specific[], recruiter_screening[]),
email_drafts (vendor_email, candidate_email, manager_email).

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
        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)
        # Merge with heuristic ATS skill_matches if missing
        base = generate_package_heuristic(jd_text, resume_text)
        for key in ("jd_analysis", "resume_analysis", "ats_score", "submission_package",
                    "interview_questions", "email_drafts"):
            if key in data and data[key]:
                if key == "ats_score" and "skill_matches" not in data[key]:
                    data[key]["skill_matches"] = base["ats_score"].skill_matches
        if not data.get("optimized_resume"):
            data["optimized_resume"] = base["optimized_resume"]
        return {
            "jd_analysis": JDAnalysis(**data.get("jd_analysis", base["jd_analysis"].model_dump())),
            "resume_analysis": ResumeAnalysis(**data.get("resume_analysis", base["resume_analysis"].model_dump())),
            "ats_score": ATSScore(**{**base["ats_score"].model_dump(), **data.get("ats_score", {})}),
            "optimized_resume": data.get("optimized_resume", base["optimized_resume"]),
            "submission_package": SubmissionPackage(**data.get("submission_package", base["submission_package"].model_dump())),
            "interview_questions": InterviewQuestions(**data.get("interview_questions", base["interview_questions"].model_dump())),
            "email_drafts": EmailDrafts(**data.get("email_drafts", base["email_drafts"].model_dump())),
        }
    except Exception:
        return generate_package_heuristic(jd_text, resume_text)


def run_pipeline(jd_text: str, resume_text: str) -> tuple[dict[str, Any], str]:
    if _ai_client():
        result = generate_package_ai(jd_text, resume_text)
        return result, "ai"
    return generate_package_heuristic(jd_text, resume_text), "heuristic"
