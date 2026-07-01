"""Step 4 — weighted ATS match engine (visa/citizenship excluded)."""

import re

from app.models.schemas import ATSScore, ATSSectionScore, JDAnalysis, ResumeAnalysis, SkillMatch
from app.services.analyzers import strip_optimizer_banner
from app.services.keywords import find_skills_in_text, keyword_in_text

# Scoring model weights (must sum to 100)
WEIGHTS = {
    "Skill Match": 35,
    "Tools Match": 20,
    "Responsibilities Match": 20,
    "Experience Match": 15,
    "Keyword Match": 10,
}


def _jd_targets(jd: JDAnalysis) -> list[str]:
    combined: list[str] = []
    seen: set[str] = set()
    for s in (
        jd.required_skills
        + jd.preferred_skills
        + jd.industry_keywords
        + jd.programming_languages
        + jd.cloud_platforms
        + jd.devops_tools
        + jd.security_tools
    ):
        key = s.lower()
        if key not in seen:
            seen.add(key)
            combined.append(s)
    return combined


def _pct_matched(targets: list[str], text: str) -> tuple[int, list[str], list[str]]:
    if not targets:
        return 100, [], []
    matched = [t for t in targets if keyword_in_text(t, text)]
    missing = [t for t in targets if t not in matched]
    score = int((len(matched) / len(targets)) * 100)
    return score, matched, missing


def _experience_score(jd: JDAnalysis, resume: ResumeAnalysis) -> int:
    if not jd.experience_years:
        return 100
    jd_years = re.search(r"(\d+)", jd.experience_years)
    res_years = re.search(r"(\d+)", resume.experience_years or "")
    if jd_years and res_years:
        return 100 if int(res_years.group(1)) >= int(jd_years.group(1)) else 75
    if res_years:
        return 85
    return 70


def _responsibility_score(jd: JDAnalysis, resume_text: str) -> int:
    if not jd.responsibilities:
        return 90
    text = resume_text.lower()
    hits = 0
    for resp in jd.responsibilities:
        tokens = [w for w in re.findall(r"[a-z]{4,}", resp.lower()) if w not in {"with", "that", "this", "will", "your"}]
        if tokens and sum(1 for t in tokens[:5] if t in text) >= min(2, len(tokens)):
            hits += 1
    return int((hits / len(jd.responsibilities)) * 100) if jd.responsibilities else 90


def compute_ats_score(
    jd: JDAnalysis,
    resume: ResumeAnalysis,
    jd_text: str,
    resume_text: str,
) -> ATSScore:
    clean = strip_optimizer_banner(resume_text)
    targets = _jd_targets(jd)
    if not targets:
        targets = find_skills_in_text(jd_text)

    skill_targets = jd.required_skills + jd.preferred_skills or targets
    tool_targets = list(dict.fromkeys(jd.devops_tools + jd.security_tools + jd.cloud_platforms))
    keyword_targets = jd.industry_keywords + [
        k for k in targets if k not in skill_targets
    ]

    skill_score, skill_matched, skill_missing = _pct_matched(skill_targets, clean)
    tool_score, tool_matched, _ = _pct_matched(tool_targets or skill_targets[:8], clean)
    kw_score, kw_matched, kw_missing = _pct_matched(keyword_targets or targets, clean)
    exp_score = _experience_score(jd, resume)
    resp_score = _responsibility_score(jd, clean)

    sections = [
        ATSSectionScore(section="Skill Match", score=skill_score, weight_pct=WEIGHTS["Skill Match"],
                        notes=f"{len(skill_matched)}/{max(len(skill_targets), 1)}"),
        ATSSectionScore(section="Tools Match", score=tool_score, weight_pct=WEIGHTS["Tools Match"],
                        notes=f"{len(tool_matched)}/{max(len(tool_targets or skill_targets[:8]), 1)}"),
        ATSSectionScore(section="Responsibilities Match", score=resp_score, weight_pct=WEIGHTS["Responsibilities Match"]),
        ATSSectionScore(section="Experience Match", score=exp_score, weight_pct=WEIGHTS["Experience Match"]),
        ATSSectionScore(section="Keyword Match", score=kw_score, weight_pct=WEIGHTS["Keyword Match"]),
    ]

    overall = int(sum(s.score * s.weight_pct for s in sections) / 100)
    all_matched = list(dict.fromkeys(skill_matched + tool_matched + kw_matched))
    all_missing = list(dict.fromkeys(skill_missing + kw_missing))

    skill_matches = [
        SkillMatch(skill=s, matched=keyword_in_text(s, clean), resume_evidence=s if keyword_in_text(s, clean) else None,
                   jd_requirement="required" if s in jd.required_skills else "preferred")
        for s in skill_targets[:15]
    ]

    coverage = int((len(all_matched) / max(len(targets), 1)) * 100)

    return ATSScore(
        sections=sections,
        overall=overall,
        missing_keywords=all_missing,
        matched_keywords=all_matched,
        skill_matches=skill_matches,
        keyword_coverage_pct=coverage,
    )
