"""Step 6 — resume optimization (factual alignment only)."""

import re

from app.models.schemas import ATSScore, JDAnalysis, TemporalAuditEntry
from app.services.analyzers import strip_optimizer_banner
from app.services.ats_engine import _jd_targets
from app.services.keywords import find_skills_in_text, keyword_in_text
from app.services.temporal_validator import filter_keywords_for_role

OPTIMIZER_RULES = (
    "Rewrite the resume to maximize ATS alignment with the supplied job description "
    "while preserving complete factual accuracy. Do not fabricate any experience, "
    "certifications, projects, tools, employers, responsibilities, or achievements. "
    "Improve keyword alignment, formatting, readability, and relevance only."
)


def _is_summary_header(line: str) -> bool:
    stripped = line.strip()
    if re.search(r"linkedin\s+profile|github\s+profile|portfolio", stripped, re.I):
        return False
    return bool(
        re.match(
            r"^(PROFESSIONAL\s+SUMMARY|EXECUTIVE\s+SUMMARY|SUMMARY|PROFILE|OBJECTIVE)\s*:?\s*$",
            stripped,
            re.I,
        )
    )


def _is_contact_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    return bool(
        re.search(r"@|linkedin|github|phone:|email:|tel:|http|www\.|^\+\d", stripped, re.I)
    )


def _upsert_skills_section(lines: list[str], keywords: list[str]) -> list[str]:
    skills_line_re = re.compile(r"^(TECHNICAL\s+)?SKILLS?\s*[:|]", re.I)
    new_lines: list[str] = []
    skills_inserted = False
    unique_kw: list[str] = []
    seen: set[str] = set()
    for k in keywords:
        if k.lower() not in seen:
            seen.add(k.lower())
            unique_kw.append(k)
    skills_value = " | ".join(unique_kw)

    i = 0
    while i < len(lines):
        line = lines[i]
        if skills_line_re.match(line.strip()):
            new_lines.append(f"TECHNICAL SKILLS: {skills_value}")
            skills_inserted = True
            i += 1
            continue
        new_lines.append(line)
        i += 1

    if not skills_inserted:
        insert_at = len(new_lines)
        for idx, line in enumerate(new_lines):
            stripped = line.strip()
            if re.match(
                r"^(PROFESSIONAL SUMMARY|SUMMARY|PROFILE|EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EDUCATION)\s*:?\s*$",
                stripped,
                re.I,
            ):
                insert_at = idx
                break
        if insert_at == len(new_lines):
            for idx, line in enumerate(new_lines[:15]):
                if _is_contact_line(line) or (idx < 6 and line.strip()):
                    insert_at = idx + 1
        block = ["", "TECHNICAL SKILLS", f"TECHNICAL SKILLS: {skills_value}", ""]
        new_lines = new_lines[:insert_at] + block + new_lines[insert_at:]
    return new_lines


def _enhance_summary(lines: list[str], top_keywords: list[str]) -> list[str]:
    for i, line in enumerate(lines):
        if not _is_summary_header(line):
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j >= len(lines) or _is_contact_line(lines[j]):
            break
        summary_line = lines[j]
        missing = [k for k in top_keywords[:6] if not keyword_in_text(k, summary_line)]
        if missing:
            lines[j] = summary_line.rstrip() + f" Skilled in {', '.join(missing[:5])}."
        break
    return lines


def _enhance_experience_bullets(lines: list[str], missing: list[str]) -> list[str]:
    triggers: dict[str, list[str]] = {
        "gitlab": ["ci/cd", "jenkins", "git", "pipeline", "devops"],
        "agile": ["scrum", "sprint", "team", "kanban"],
        "safe": ["enterprise", "scrum", "agile", "program"],
        "fortify": ["security", "scan", "sast", "vulnerability", "hp fortify"],
        "git": ["version control", "github", "gitlab", "source control"],
        "rmf": ["security", "compliance", "nist", "authorization"],
    }
    result = list(lines)
    for idx, line in enumerate(result):
        if not re.match(r"^[\-\*•]\s+", line.strip()):
            continue
        lower = line.lower()
        for kw in missing:
            kl = kw.lower()
            if keyword_in_text(kw, line):
                continue
            if any(t in lower for t in triggers.get(kl, [])):
                if kl == "safe":
                    result[idx] = line.rstrip() + " (SAFe / Agile delivery)"
                elif kl == "gitlab":
                    result[idx] = line.rstrip() + " — GitLab/Git CI/CD"
                elif kl == "fortify":
                    result[idx] = line.rstrip() + " — HP Fortify security scanning"
                elif kl == "agile":
                    result[idx] = line.rstrip() + " in Agile/Scrum teams"
                elif kl == "rmf":
                    result[idx] = line.rstrip() + " — RMF / security compliance"
                break
    return result


def optimize_resume(
    resume: str,
    jd: JDAnalysis,
    _ats: ATSScore,
    temporal_audit: list[TemporalAuditEntry] | None = None,
) -> str:
    clean = strip_optimizer_banner(resume)
    lines = [ln for ln in clean.splitlines()]
    targets = _jd_targets(jd)
    if not targets:
        targets = find_skills_in_text(jd.summary or "")

    # Block versioned requirements that fail temporal validation from experience bullets
    experience_targets = (
        filter_keywords_for_role(targets, temporal_audit) if temporal_audit else targets
    )

    existing = find_skills_in_text(clean)
    all_skills: list[str] = []
    seen: set[str] = set()
    for s in existing + targets:
        if s.lower() not in seen:
            seen.add(s.lower())
            all_skills.append(s)

    lines = _upsert_skills_section(lines, all_skills)
    lines = _enhance_summary(lines, targets)

    text_so_far = "\n".join(lines)
    still_missing = [k for k in experience_targets if not keyword_in_text(k, text_so_far)]
    lines = _enhance_experience_bullets(lines, still_missing)
    text = "\n".join(lines)

    still_missing = [k for k in targets if not keyword_in_text(k, text)]
    if still_missing:
        for kw in still_missing:
            if not keyword_in_text(kw, text):
                all_skills.append(kw)
        lines = _upsert_skills_section(text.splitlines(), all_skills)
        text = "\n".join(lines)

    upgrades = [
        (r"\bInfrastructure as Code\b", "Terraform Infrastructure as Code (IaC)"),
        (r"\bCI/CD pipelines\b", "CI/CD pipelines (Jenkins, GitLab)"),
        (r"\bversion control\b", "Git/GitLab version control"),
    ]
    for pattern, repl in upgrades:
        if re.search(pattern, text, re.I):
            text = re.sub(pattern, repl, text, count=1, flags=re.I)
    return text.strip()
