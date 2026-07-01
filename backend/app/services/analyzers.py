"""Step 2 & 3 — JD and resume analysis."""

import re

from app.models.schemas import JDAnalysis, ResumeAnalysis, WorkEntry
from app.services.keywords import (
    CERT_KEYWORDS,
    SOFT_SKILLS,
    categorize_skills,
    find_skills_in_text,
    keyword_in_text,
)
from app.services.temporal_validator import extract_versioned_requirements

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

JD_SKILL_LINE_PATTERNS = [
    r"(?:required|must have|requirements?|qualifications?|skills?)[:\s]+(.+)",
    r"^[\-\*•]\s*(.+)$",
]

RESPONSIBILITY_VERBS = re.compile(
    r"\b(design|develop|implement|manage|lead|build|maintain|automate|deploy|"
    r"monitor|secure|architect|integrate|optimize|support|configure|migrate)\b",
    re.I,
)


def _extract_experience_years(text: str) -> str | None:
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience",
        r"experience[:\s]+(\d+)\+?\s*years?",
        r"minimum\s+of\s+(\d+)\+?\s*years?",
        r"(\d+)\+?\s*years?",
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
    m = re.search(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z]{2})\b", text)
    if m:
        return f"{m.group(1)}, {m.group(2)}"
    m = re.search(r"location[:\s]+([^\n.]+)", text, re.I)
    if m:
        return m.group(1).strip()[:80]
    return None


def _extract_jd_title(jd: str) -> str | None:
    for line in jd.splitlines()[:20]:
        line = line.strip()
        if not line or len(line) < 8:
            continue
        opening = re.search(
            r"(?:opening for|position for|role of|hiring an?|seeking an?)\s+(.+?)(?:\s+to\s+join|\.\s|\n|$)",
            line,
            re.I,
        )
        if opening:
            title = opening.group(1).strip(" .,-")
            title = re.sub(r"^(?:an?\s+)", "", title, flags=re.I)
            title = re.sub(r"\s+to join.*", "", title, flags=re.I).strip()
            if 8 <= len(title) <= 80:
                return title
        if re.search(r"engineer|developer|architect|analyst|manager|consultant|administrator", line, re.I):
            if re.search(r"has an opening|join our team|we are hiring|qualified candidates", line, re.I):
                role = re.search(
                    r"((?:Principal|Senior|Lead|Staff|Junior)?\s*"
                    r"[\w\s/&.-]*(?:Engineer|Developer|Architect|Analyst|Manager|Consultant|Administrator)"
                    r"[\w\s/&.-]*)",
                    line,
                    re.I,
                )
                if role:
                    return role.group(1).strip()[:80]
                continue
            if len(line) <= 90:
                return line[:80]
    return None


def _extract_jd_skill_phrases(jd: str) -> list[str]:
    phrases: list[str] = []
    for line in jd.splitlines():
        line = line.strip()
        if not line:
            continue
        for pat in JD_SKILL_LINE_PATTERNS:
            m = re.search(pat, line, re.I)
            if m:
                chunk = m.group(1) if m.lastindex else line
                parts = re.split(r",|\||/|\band\b", chunk, flags=re.I)
                for p in parts:
                    p = p.strip(" .-•*")
                    if 2 <= len(p) <= 60:
                        phrases.append(p)
                break
    return phrases


def _merge_jd_skills(jd_text: str) -> tuple[list[str], list[str]]:
    detected = find_skills_in_text(jd_text)
    phrases = _extract_jd_skill_phrases(jd_text)
    for phrase in phrases:
        for skill in find_skills_in_text(phrase):
            if skill not in detected:
                detected.append(skill)
        if find_skills_in_text(phrase) or re.search(
            r"azure|aws|sql|spark|python|java|agile|scrum|safe|fortify|gitlab|jenkins|docker|kubernetes|rmf",
            phrase,
            re.I,
        ):
            clean = phrase.strip()
            if clean and clean not in detected and len(clean) < 40:
                detected.append(clean)

    seen: set[str] = set()
    unique: list[str] = []
    for s in detected:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)

    nice_section = re.search(
        r"(nice\s*to\s*have|preferred|bonus)[:\s]*(.*?)(?:\n\n|\Z)",
        jd_text,
        re.I | re.S,
    )
    nice: list[str] = []
    if nice_section:
        nice = find_skills_in_text(nice_section.group(2))
        for p in _extract_jd_skill_phrases(nice_section.group(2)):
            for s in find_skills_in_text(p):
                if s not in nice:
                    nice.append(s)

    nice_lower = {n.lower() for n in nice}
    mandatory = [s for s in unique if s.lower() not in nice_lower]
    if not mandatory:
        mandatory = unique[: max(6, len(unique) // 2 + 1)]
        nice = [s for s in unique if s not in mandatory]
    return mandatory[:20], nice[:12]


def _extract_responsibilities(jd: str) -> list[str]:
    items: list[str] = []
    in_resp = False
    for line in jd.splitlines():
        stripped = line.strip()
        if re.search(r"responsibilit|duties|what you.ll do|you will", stripped, re.I):
            in_resp = True
            continue
        if in_resp and re.match(r"^(requirements|qualifications|skills|nice|preferred)\b", stripped, re.I):
            break
        if stripped.startswith(("-", "•", "*")) or (in_resp and RESPONSIBILITY_VERBS.search(stripped)):
            text = re.sub(r"^[\-\*•]\s*", "", stripped)
            if len(text) > 15:
                items.append(text[:200])
        elif in_resp and not stripped:
            in_resp = False
    if not items:
        for line in jd.splitlines():
            if RESPONSIBILITY_VERBS.search(line) and len(line.strip()) > 20:
                items.append(line.strip()[:200])
    return items[:12]


def _extract_industry_keywords(jd: str) -> list[str]:
    industry_terms = [
        "defense", "aerospace", "healthcare", "finance", "fintech", "government",
        "fedramp", "hipaa", "pci", "software factory", "continuous cyber",
        "zero trust", "cleared", "secret", "top secret", "dod", "intelligence",
    ]
    found = [t.title() if t.islower() else t for t in industry_terms if keyword_in_text(t, jd)]
    return found[:10]


def _extract_soft_skills(jd: str) -> list[str]:
    found = []
    low = jd.lower()
    for s in SOFT_SKILLS:
        if s in low:
            found.append(s.title())
    return found[:8]


def _extract_certifications_from_text(text: str) -> list[str]:
    certs: list[str] = []
    for line in text.splitlines():
        if CERT_KEYWORDS.search(line):
            certs.append(line.strip()[:100])
    return certs[:8]


def analyze_jd(jd: str) -> JDAnalysis:
    required, preferred = _merge_jd_skills(jd)
    all_skills = required + [p for p in preferred if p not in required]
    cats = categorize_skills(all_skills)

    title = _extract_jd_title(jd)
    if not title:
        for line in jd.splitlines()[:12]:
            if re.search(r"engineer|developer|architect|analyst|manager|consultant|administrator", line, re.I):
                if len(line.strip()) <= 90 and not re.search(r"has an opening|join our team", line, re.I):
                    title = line.strip()[:80]
                break

    return JDAnalysis(
        title=title,
        required_skills=required,
        preferred_skills=preferred,
        mandatory_skills=required,
        nice_to_have_skills=preferred,
        programming_languages=cats["programming_languages"],
        cloud_platforms=cats["cloud_platforms"],
        devops_tools=cats["devops_tools"],
        security_tools=cats["security_tools"],
        certifications=_extract_certifications_from_text(jd),
        experience_years=_extract_experience_years(jd),
        responsibilities=_extract_responsibilities(jd),
        industry_keywords=_extract_industry_keywords(jd),
        soft_skills=_extract_soft_skills(jd),
        visa_requirements=_extract_visa(jd),
        location=_extract_location(jd),
        work_mode=_extract_work_mode(jd),
        summary=jd[:400].replace("\n", " ").strip() + ("..." if len(jd) > 400 else ""),
        versioned_tools=extract_versioned_requirements(jd),
        tools=all_skills[:25],
    )


def _extract_name(text: str) -> str | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    first = lines[0]
    if len(first) < 50 and not re.search(r"@|http|resume|curriculum|talentforge", first, re.I):
        return first
    return None


def _extract_email(text: str) -> str | None:
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    return m.group(0) if m else None


def _extract_phone(text: str) -> str | None:
    m = re.search(r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    return m.group(0) if m else None


def _extract_summary_block(text: str) -> str | None:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^(PROFESSIONAL\s+SUMMARY|SUMMARY|PROFILE)\s*:?\s*$", line.strip(), re.I):
            block: list[str] = []
            for j in range(i + 1, min(i + 6, len(lines))):
                if not lines[j].strip():
                    break
                if re.match(r"^[A-Z][A-Z\s]+:?\s*$", lines[j].strip()) and j > i + 1:
                    break
                block.append(lines[j].strip())
            if block:
                return " ".join(block)[:500]
    return None


def _parse_work_history(text: str) -> list[WorkEntry]:
    entries: list[WorkEntry] = []
    current: WorkEntry | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.search(r"^(EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT)\s*:?\s*$", stripped, re.I):
            continue
        is_job_header = (
            re.search(r"\d{4}\s*[-–—]\s*(?:\d{4}|present)", stripped, re.I)
            or (re.search(r"—|–|-", stripped) and re.search(r"engineer|developer|architect|manager|analyst", stripped, re.I))
        )
        if is_job_header and not stripped.startswith(("-", "•", "*")):
            if current:
                entries.append(current)
            parts = re.split(r"\s*[—–-]\s*", stripped, maxsplit=2)
            current = WorkEntry(
                company=parts[0].strip() if parts else None,
                title=parts[1].strip() if len(parts) > 1 else None,
                dates=parts[2].strip() if len(parts) > 2 else None,
                bullets=[],
            )
        elif current and re.match(r"^[\-\*•]\s+", stripped):
            current.bullets.append(re.sub(r"^[\-\*•]\s+", "", stripped))
    if current:
        entries.append(current)
    return entries[:8]


def _extract_projects(text: str) -> list[str]:
    projects: list[str] = []
    in_projects = False
    for line in text.splitlines():
        stripped = line.strip()
        if re.search(r"^PROJECTS?\s*:?\s*$", stripped, re.I):
            in_projects = True
            continue
        if in_projects:
            if re.match(r"^[A-Z][A-Z\s]+:?\s*$", stripped) and not stripped.startswith(("-", "•")):
                break
            if stripped:
                projects.append(stripped[:150])
    return projects[:6]


def strip_optimizer_banner(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    skip_block = False
    for line in lines:
        if re.search(r"talentforge|optimized resume|jd-aligned|review before submission", line, re.I):
            skip_block = True
            continue
        if skip_block and line.strip().startswith("---"):
            skip_block = False
            continue
        if skip_block and not line.strip():
            skip_block = False
            continue
        out.append(line)
    return "\n".join(out).strip()


def analyze_resume(resume: str) -> ResumeAnalysis:
    clean = strip_optimizer_banner(resume)
    skills = find_skills_in_text(clean)
    cats = categorize_skills(skills)
    tools = cats["devops_tools"] + cats["security_tools"]
    technologies = cats["cloud_platforms"] + cats["programming_languages"] + skills

    return ResumeAnalysis(
        candidate_name=_extract_name(clean),
        email=_extract_email(clean),
        phone=_extract_phone(clean),
        summary=_extract_summary_block(clean) or clean[:350].replace("\n", " ").strip(),
        skills=skills,
        tools=list(dict.fromkeys(tools))[:15],
        technologies=list(dict.fromkeys(technologies))[:20],
        certifications=_extract_certifications_from_text(clean),
        education=[
            ln.strip()[:120]
            for ln in clean.splitlines()
            if re.search(r"bachelor|master|b\.?s\.?|m\.?s\.?|ph\.?d|university|college|degree", ln, re.I)
        ][:4],
        work_history=_parse_work_history(clean),
        projects=_extract_projects(clean),
        experience_years=_extract_experience_years(clean),
        visa_status=", ".join(_extract_visa(clean)) or None,
        location=_extract_location(clean),
    )
