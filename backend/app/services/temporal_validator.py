"""Temporal due diligence — prevent anachronistic skill/version claims."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from app.models.schemas import JDAnalysis, ResumeAnalysis, TemporalAuditEntry, VersionedTool, WorkEntry

_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "tech_releases.json"

# Aliases: normalized tool key -> registry key
_TOOL_ALIASES: dict[str, str] = {
    "postgres": "postgresql",
    "pg": "postgresql",
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "golang": "go",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "tf": "terraform",
    "eks": "kubernetes",
    "aks": "kubernetes",
    "gke": "kubernetes",
    "node": "nodejs",
    "node.js": "nodejs",
    "react.js": "react",
    "vue.js": "vue",
    "angular.js": "angular",
    "ms sql": "sql server",
    "mssql": "sql server",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "azure devops": "azure",
}

_VERSIONED_RE = re.compile(
    r"\b("
    r"postgresql|postgres|pg|kubernetes|k8s|kube|docker|python|java|node\.?js|nodejs|"
    r"react|angular|vue|terraform|ansible|jenkins|gitlab|github|aws|azure|gcp|"
    r"spring|django|flask|fastapi|\.net|dotnet|go|golang|rust|typescript|javascript|"
    r"redis|mongodb|mysql|sql\s*server|elasticsearch|kafka|rabbitmq|nginx|"
    r"helm|istio|prometheus|grafana|linux|ubuntu|windows\s*server|"
    r"spark|hadoop|airflow|snowflake|databricks|tableau|power\s*bi|"
    r"splunk|fortify|sonarqube|openshift|vmware|vsphere|"
    r"angularjs|react\s*native|next\.?js|nuxt|svelte|laravel|rails|ruby|php|"
    r"c\+\+|c#|swift|kotlin|scala|hadoop|hive|presto|"
    r"tensorflow|pytorch|scikit-learn|pandas|numpy"
    r")"
    r"\s*(?:v(?:ersion)?\.?\s*)?(\d+(?:\.\d+){0,2})\b",
    re.I,
)

_PRESENT_RE = re.compile(r"present|current|now|today", re.I)


def _load_registry() -> dict[str, Any]:
    if not _REGISTRY_PATH.exists():
        return {}
    with open(_REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)


def _normalize_tool(name: str) -> str:
    key = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    key = re.sub(r"\s+", " ", key)
    for alias, canonical in _TOOL_ALIASES.items():
        if key == alias or key.startswith(alias + " "):
            key = canonical
            break
    return key.split()[0] if key else name.lower()


def lookup_release_date(tool: str, version: str) -> tuple[str | None, str]:
    """Return (release_date YYYY-MM, confidence)."""
    registry = _load_registry()
    tool_key = _normalize_tool(tool)
    # Direct lookup
    tool_data = registry.get(tool_key) or registry.get(tool.lower())
    if not tool_data:
        # Fuzzy: find key that matches prefix
        for k, v in registry.items():
            if tool_key.startswith(k) or k.startswith(tool_key.split()[0]):
                tool_data = v
                tool_key = k
                break
    if not tool_data:
        return None, "low"

    versions = tool_data if isinstance(tool_data, dict) and "release_date" not in tool_data else None
    if versions is None and isinstance(tool_data, dict) and "release_date" in tool_data:
        return tool_data["release_date"][:7], "high"

    if not versions:
        return None, "low"

    # Exact version match
    if version in versions:
        return versions[version]["release_date"][:7], "high"

    # Major.minor match
    parts = version.split(".")
    for try_ver in [version, f"{parts[0]}.{parts[1]}" if len(parts) > 1 else parts[0], parts[0]]:
        if try_ver in versions:
            return versions[try_ver]["release_date"][:7], "medium"

    # Closest lower version
    try:
        ver_float = float(version)
        best = None
        best_date = None
        for v, meta in versions.items():
            try:
                if float(v) <= ver_float:
                    if best is None or float(v) > float(best):
                        best = v
                        best_date = meta["release_date"][:7]
            except ValueError:
                continue
        if best_date:
            return best_date, "medium"
    except ValueError:
        pass

    return None, "low"


def extract_versioned_requirements(jd_text: str, jd: JDAnalysis | None = None) -> list[VersionedTool]:
    """Extract versioned tool requirements from JD text."""
    found: dict[str, VersionedTool] = {}
    sources = [jd_text]
    if jd:
        for skill in jd.required_skills + jd.preferred_skills + jd.devops_tools:
            sources.append(skill)

    for source in sources:
        for m in _VERSIONED_RE.finditer(source):
            tool_raw = m.group(1)
            version = m.group(2)
            tool_norm = _normalize_tool(tool_raw)
            display = f"{tool_raw.strip()} {version}".strip()
            key = f"{tool_norm}:{version}"
            if key in found:
                continue
            release, confidence = lookup_release_date(tool_raw, version)
            found[key] = VersionedTool(
                tool=tool_norm.title() if tool_norm != "postgresql" else "PostgreSQL",
                version=version,
                display_name=display,
                release_date=release,
                confidence=confidence,
            )
    return list(found.values())


def _parse_month_year(text: str) -> date | None:
    """Parse date from various resume date formats."""
    text = text.strip()
    if not text:
        return None
    if _PRESENT_RE.search(text):
        return date.today()

    # YYYY-MM or YYYY/MM
    m = re.search(r"(\d{4})[-/](\d{1,2})", text)
    if m:
        return date(int(m.group(1)), min(int(m.group(2)), 12), 1)

    # Month YYYY
    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    m = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*['']?(\d{2,4})", text, re.I)
    if m:
        year = int(m.group(2))
        if year < 100:
            year += 2000 if year < 50 else 1900
        return date(year, months[m.group(1).lower()[:3]], 1)

    # Just YYYY
    m = re.search(r"\b(19|20)\d{2}\b", text)
    if m:
        return date(int(m.group(0)), 12, 1)

    return None


def _parse_role_dates(dates_str: str | None) -> tuple[date | None, date | None]:
    """Parse start and end dates from a date range string."""
    if not dates_str:
        return None, None
    parts = re.split(r"\s*[-–—to]+\s*", dates_str, maxsplit=1, flags=re.I)
    start = _parse_month_year(parts[0]) if parts else None
    end = _parse_month_year(parts[1]) if len(parts) > 1 else None
    if end is None and _PRESENT_RE.search(dates_str):
        end = date.today()
    return start, end


def _role_end_month(entry: WorkEntry) -> date | None:
    """Get role end date from work entry."""
    if entry.dates:
        _, end = _parse_role_dates(entry.dates)
        if end:
            return end
    # Try parsing from company/title line
    for field in (entry.company, entry.title):
        if field and re.search(r"\d{4}", field):
            _, end = _parse_role_dates(field)
            if end:
                return end
    return None


def _role_label(entry: WorkEntry) -> str:
    parts = [p for p in (entry.title, entry.company) if p]
    return " at ".join(parts) if parts else "Unknown role"


def _release_to_date(release: str) -> date:
    """Convert YYYY-MM release string to date."""
    parts = release.split("-")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 1
    return date(year, month, 1)


def is_role_eligible(role_end: date | None, release_date: str) -> bool:
    """Role may include technology if it ended on/after release (or is current)."""
    if role_end is None:
        return False
    release = _release_to_date(release_date)
    return role_end >= release


def run_temporal_audit(
    jd_text: str,
    jd: JDAnalysis,
    resume: ResumeAnalysis,
) -> list[TemporalAuditEntry]:
    """Run full temporal due diligence and return audit trail."""
    requirements = extract_versioned_requirements(jd_text, jd)
    audit: list[TemporalAuditEntry] = []

    for req in requirements:
        if not req.release_date:
            audit.append(
                TemporalAuditEntry(
                    requirement=req.display_name,
                    release_date=None,
                    placed_in_role=None,
                    company=None,
                    role_dates=None,
                    allowed=False,
                    action_taken="skipped",
                    reason="Release date unknown — cannot verify placement safely",
                )
            )
            continue

        eligible_roles: list[WorkEntry] = []
        for entry in resume.work_history:
            role_end = _role_end_month(entry)
            if role_end and is_role_eligible(role_end, req.release_date):
                eligible_roles.append(entry)

        if eligible_roles:
            best = eligible_roles[0]
            audit.append(
                TemporalAuditEntry(
                    requirement=req.display_name,
                    release_date=req.release_date,
                    placed_in_role=_role_label(best),
                    company=best.company,
                    role_dates=best.dates,
                    allowed=True,
                    action_taken="eligible_for_placement",
                    reason=f"Role ended {best.dates or 'Present'} — after {req.release_date} release",
                )
            )
        else:
            # Check if any role ended before release
            blocked_roles = []
            for entry in resume.work_history:
                role_end = _role_end_month(entry)
                if role_end and not is_role_eligible(role_end, req.release_date):
                    blocked_roles.append(_role_label(entry))

            reason = (
                f"No employment period overlaps post-{req.release_date} release. "
                f"Blocked for: {', '.join(blocked_roles[:3]) or 'all roles'}"
            )
            audit.append(
                TemporalAuditEntry(
                    requirement=req.display_name,
                    release_date=req.release_date,
                    placed_in_role=blocked_roles[0] if blocked_roles else None,
                    company=resume.work_history[0].company if resume.work_history else None,
                    role_dates=resume.work_history[0].dates if resume.work_history else None,
                    allowed=False,
                    action_taken="blocked",
                    reason=reason,
                )
            )

    return audit


def blocked_requirements(audit: list[TemporalAuditEntry]) -> set[str]:
    """Return requirement display names that must NOT be placed in experience bullets."""
    return {a.requirement.lower() for a in audit if not a.allowed}


def filter_keywords_for_role(
    keywords: list[str],
    audit: list[TemporalAuditEntry],
) -> list[str]:
    """Remove blocked versioned requirements from optimizer keyword list for experience."""
    blocked = blocked_requirements(audit)
    result = []
    for kw in keywords:
        kl = kw.lower()
        if any(b in kl or kl in b for b in blocked):
            continue
        result.append(kw)
    return result
