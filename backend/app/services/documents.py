"""Step 10 — document generation (DOCX + text artifacts)."""

import base64

from app.models.schemas import (
    DocumentArtifacts,
    GeneratedSections,
    InterviewQuestions,
    SubmissionPackage,
)
from app.services.pdf_export import text_to_pdf_bytes
from app.services.resume_formatter import resume_text_to_docx_bytes


def build_interview_sheet(questions: InterviewQuestions) -> str:
    lines = ["INTERVIEW QUESTION SHEET", "=" * 40, ""]
    for label, items in [
        ("TECHNICAL", questions.technical),
        ("SCENARIO", questions.scenario),
        ("BEHAVIORAL", questions.behavioral),
        ("CLIENT-SPECIFIC", questions.client_specific),
    ]:
        lines.append(label)
        lines.append("-" * len(label))
        for i, q in enumerate(items, 1):
            lines.append(f"{i}. [{q.difficulty.upper()}] {q.question}")
        lines.append("")
    lines.append("RECRUITER SCREENING")
    lines.append("-" * 20)
    for i, q in enumerate(questions.recruiter_screening, 1):
        lines.append(f"{i}. {q}")
    return "\n".join(lines)


def build_submission_text(sections: GeneratedSections, pkg: SubmissionPackage) -> str:
    return "\n".join([
        "SUBMISSION PACKAGE",
        "=" * 40,
        "",
        "PROFESSIONAL SUMMARY",
        sections.professional_summary,
        "",
        "CLIENT SUBMISSION SUMMARY",
        sections.client_submission_summary,
        "",
        "KEY STRENGTHS",
        *[f"• {s}" for s in sections.key_strengths],
        "",
        "TECHNICAL HIGHLIGHTS",
        *[f"• {h}" for h in sections.technical_highlights],
        "",
        "FIT STATEMENT",
        pkg.fit_statement or "",
        "",
        "RISKS",
        *[f"• {r}" for r in pkg.risks],
    ])


def build_documents(
    optimized_resume: str,
    sections: GeneratedSections,
    questions: InterviewQuestions,
    pkg: SubmissionPackage,
) -> DocumentArtifacts:
    docx_bytes = resume_text_to_docx_bytes(optimized_resume)
    summary_text = "\n".join([
        "CANDIDATE SUMMARY",
        "=" * 40,
        "",
        sections.professional_summary,
        "",
        "TOP MATCHING SKILLS: " + ", ".join(sections.top_matching_skills[:8]),
        "",
        sections.client_submission_summary,
    ])
    interview_text = build_interview_sheet(questions)
    submission_text = build_submission_text(sections, pkg)
    pdf_bytes = text_to_pdf_bytes(optimized_resume, "Optimized Resume")
    return DocumentArtifacts(
        optimized_resume_docx_b64=base64.b64encode(docx_bytes).decode("ascii"),
        optimized_resume_pdf_b64=base64.b64encode(pdf_bytes).decode("ascii"),
        candidate_summary_text=summary_text,
        interview_sheet_text=interview_text,
        submission_package_text=submission_text,
        submission_package_pdf_b64=base64.b64encode(
            text_to_pdf_bytes(submission_text, "Submission Package")
        ).decode("ascii"),
        interview_sheet_pdf_b64=base64.b64encode(
            text_to_pdf_bytes(interview_text, "Interview Questions")
        ).decode("ascii"),
    )
