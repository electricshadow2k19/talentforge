"""Steps 7–9 — generated sections, interview questions, emails, dashboard."""

from app.models.schemas import (
    ATSScore,
    Dashboard,
    EmailDrafts,
    GapAnalysis,
    GeneratedSections,
    InterviewQuestions,
    JDAnalysis,
    RatedQuestion,
    ResumeAnalysis,
    SubmissionPackage,
)
from app.services.ats_engine import WEIGHTS


def build_generated_sections(
    jd: JDAnalysis,
    resume: ResumeAnalysis,
    ats: ATSScore,
) -> GeneratedSections:
    name = resume.candidate_name or "Candidate"
    yrs = resume.experience_years or "several years"
    role = jd.title or "technology professional"
    top = ats.matched_keywords[:10] or resume.skills[:10]
    top_str = ", ".join(top[:8])

    prof_summary = (
        f"{role} with {yrs} of experience in {top_str}. "
        f"Proven background in cloud, DevOps, and security-aligned delivery."
    )
    if resume.summary and len(resume.summary) > 40:
        prof_summary = resume.summary[:400]
        if top:
            prof_summary = prof_summary.rstrip(".") + f". Core competencies: {', '.join(top[:6])}."

    highlights = [
        f"{s} — demonstrated in production environments" for s in top[:5]
    ]
    if resume.certifications:
        highlights.append(f"Certifications: {resume.certifications[0][:80]}")

    client_summary = (
        f"{name} is a strong candidate for the {role} role with {yrs} of hands-on experience. "
        f"Relevant strengths include {top_str}."
    )

    return GeneratedSections(
        professional_summary=prof_summary,
        key_strengths=[f"Strong {s} experience" for s in top[:5]],
        top_matching_skills=top[:10],
        technical_highlights=highlights[:6],
        client_submission_summary=client_summary,
    )


def build_submission_package(
    sections: GeneratedSections,
    gap: GapAnalysis,
    ats: ATSScore,
    ats_before: int,
) -> SubmissionPackage:
    risks = []
    if gap.missing_skills:
        risks.append(f"Verify with candidate: {', '.join(gap.missing_skills[:4])}")
    risks.append("Confirm optimized keywords reflect actual experience before client submission.")

    return SubmissionPackage(
        candidate_summary=sections.client_submission_summary,
        strengths=sections.key_strengths[:5],
        risks=risks[:4],
        fit_statement=f"ATS improved {ats_before}% → {ats.overall}% ({ats.keyword_coverage_pct}% keyword coverage).",
    )


def _rated(question: str, difficulty: str) -> RatedQuestion:
    return RatedQuestion(question=question, difficulty=difficulty)


def build_interview_questions(jd: JDAnalysis, resume: ResumeAnalysis) -> InterviewQuestions:
    skills = jd.required_skills[:6] or resume.skills[:6]
    technical: list[RatedQuestion] = []
    for i, s in enumerate(skills):
        diff = ["easy", "medium", "hard"][min(i, 2)]
        if s.lower() == "terraform":
            technical.append(_rated("Explain Terraform state locking and drift prevention.", diff))
        elif s.lower() == "kubernetes":
            technical.append(_rated("Compare EKS vs self-managed Kubernetes — when to choose each?", diff))
        elif s.lower() == "aws":
            technical.append(_rated("Design a highly available multi-AZ architecture on AWS.", diff))
        else:
            technical.append(_rated(f"Describe a production project using {s} — architecture and outcomes.", diff))

    scenario = [
        _rated("How would you reduce cloud cost by 20% without sacrificing reliability?", "medium"),
        _rated("Walk through an incident: detection, triage, resolution, postmortem.", "hard"),
        _rated("How would you implement a secure CI/CD pipeline for a regulated environment?", "hard"),
    ]
    behavioral = [
        _rated("Tell me about a time you influenced stakeholders on a technical decision.", "medium"),
        _rated("Describe handling conflicting priorities across multiple teams.", "medium"),
        _rated("Give an example of mentoring or upskilling team members.", "easy"),
    ]
    client = [
        _rated(f"For {jd.title or 'this role'}, how would you ramp in the first 30 days?", "medium"),
        _rated("What questions do you have about the client's tech stack and team?", "easy"),
    ]

    rate_skills = (jd.required_skills + jd.devops_tools + jd.cloud_platforms)[:3]
    while len(rate_skills) < 3:
        rate_skills.append("cloud platform")
    recruiter = [
        f"Rate {rate_skills[0]} proficiency (1-10)?",
        f"Rate {rate_skills[1]} proficiency (1-10)?",
        f"Rate {rate_skills[2]} proficiency (1-10)?",
        "Current location?",
        "Willingness to relocate / hybrid / remote?",
        "Availability and earliest start date?",
        "Expected compensation (hourly or salary range)?",
        "Notice period with current employer?",
    ]

    return InterviewQuestions(
        technical=technical[:6],
        scenario=scenario,
        behavioral=behavioral,
        client_specific=client,
        recruiter_screening=recruiter,
    )


def build_emails(
    jd: JDAnalysis,
    resume: ResumeAnalysis,
    sections: GeneratedSections,
    pkg: SubmissionPackage,
) -> EmailDrafts:
    name = resume.candidate_name or "Candidate"
    role = jd.title or "the position"
    yrs = resume.experience_years or "several years"
    skills = ", ".join(sections.top_matching_skills[:6]) or ", ".join(resume.skills[:6])
    loc = f" ({jd.location})" if jd.location else ""
    work_mode = f" — {jd.work_mode}" if jd.work_mode else ""

    vendor = (
        f"Subject: Candidate Submission — {name} for {role}{loc}\n\n"
        f"Dear Hiring Manager,\n\n"
        f"I hope you are doing well. I am pleased to submit {name} for the {role} "
        f"position{loc}{work_mode}.\n\n"
        f"{name} is a {role.split('—')[0].strip() if role and '—' in role else 'technology'} professional "
        f"with {yrs} of experience. {sections.professional_summary}\n\n"
        f"Based on your requirements, {name}'s background aligns well with this role. "
        f"Key qualifications include:\n"
        + "\n".join(f"• {s}" for s in sections.key_strengths[:5])
        + f"\n\n"
        f"Core technical skills: {skills}.\n\n"
        f"Please find {name}'s resume attached for your review. "
        f"They are available for an interview at your convenience and can discuss project "
        f"experience, technical depth, and availability upon request.\n\n"
        f"Thank you for your consideration. I look forward to your feedback.\n\n"
        f"Best regards,\n"
        f"[Recruiter Name]\n"
        f"GenvenX Technologies\n"
        f"recruiting@genvenx.com"
    )
    candidate = (
        f"Subject: Submission confirmation — {role}\n\n"
        f"Hi {name},\n\n"
        f"We have submitted your profile to the client for the {role} position"
        f"{loc}.\n\n"
        f"Summary shared with the client:\n{sections.professional_summary}\n\n"
        f"Please review the attached resume we submitted and let us know immediately "
        f"if any detail needs correction.\n\n"
        f"Next steps: prepare for a potential client screen. Topics may include: "
        f"{skills}.\n\n"
        f"GenvenX Talent Team"
    )
    manager = (
        f"Subject: Internal — submission logged — {name} / {role}\n\n"
        f"Recruiter notes (internal):\n"
        f"• Candidate: {name}\n"
        f"• Role: {role}{loc}\n"
        f"• {pkg.fit_statement}\n"
        f"• Risks: {'; '.join(pkg.risks)}\n"
        f"• Action: Track vendor response; schedule follow-up in 48h\n"
    )
    return EmailDrafts(vendor_email=vendor, candidate_email=candidate, manager_email=manager)


def build_dashboard(
    ats: ATSScore,
    ats_before: int,
    gap: GapAnalysis,
) -> Dashboard:
    return Dashboard(
        ats_score=ats.overall,
        ats_score_before=ats_before,
        keyword_coverage_pct=ats.keyword_coverage_pct,
        top_skills=ats.matched_keywords[:10],
        missing_skills=gap.missing_skills[:10],
        optimization_suggestions=gap.optimization_suggestions,
        scoring_weights={k: v / 100 for k, v in WEIGHTS.items()},
    )
