"""Temporal due diligence test cases (TC-T01 through TC-T04)."""

from app.models.schemas import WorkEntry
from app.services.analyzers import analyze_jd, analyze_resume
from app.services.optimizer import optimize_resume
from app.services.temporal_validator import is_role_eligible, run_temporal_audit
from app.services.ats_engine import compute_ats_score


RESUME_ACME_2019_2021 = """
Jane Doe
Senior DBA

PROFESSIONAL EXPERIENCE
Acme Corp — DBA — 2019-2021
- Managed Oracle and MySQL databases
- Performed backups and disaster recovery
"""

RESUME_BETA_2023_PRESENT = """
John Smith
Cloud Engineer

PROFESSIONAL EXPERIENCE
Beta Inc — Cloud Engineer — 2023-Present
- Managed AWS RDS PostgreSQL instances
- Built CI/CD pipelines with Jenkins
"""

RESUME_K8S_2022 = """
Alex Dev
DevOps Engineer

PROFESSIONAL EXPERIENCE
Gamma LLC — DevOps Engineer — 2020-2022
- Deployed applications with Docker
- Managed Kubernetes clusters
"""

JD_POSTGRES_16 = """
Senior Database Engineer
Requirements:
- PostgreSQL 16 experience required
- 5+ years DBA experience
"""

JD_K8S_129 = """
Platform Engineer
Must have Kubernetes 1.29 experience
"""


def test_tc_t01_postgres_16_not_added_to_2019_role():
    """TC-T01: PostgreSQL 16 NOT added to Acme 2019-2021 role."""
    jd = analyze_jd(JD_POSTGRES_16)
    resume = analyze_resume(RESUME_ACME_2019_2021)
    audit = run_temporal_audit(JD_POSTGRES_16, jd, resume)

    pg_entries = [a for a in audit if "postgres" in a.requirement.lower()]
    assert len(pg_entries) >= 1
    assert pg_entries[0].allowed is False
    assert pg_entries[0].action_taken == "blocked"

    ats = compute_ats_score(jd, resume, JD_POSTGRES_16, RESUME_ACME_2019_2021)
    optimized = optimize_resume(RESUME_ACME_2019_2021, jd, ats, audit)
    assert "postgresql 16" not in optimized.lower() or "postgresql 16" in optimized.lower().split("experience")[0]


def test_tc_t02_postgres_16_eligible_for_2023_present():
    """TC-T02: PostgreSQL 16 MAY be added to 2023-Present role."""
    jd = analyze_jd(JD_POSTGRES_16)
    resume = analyze_resume(RESUME_BETA_2023_PRESENT)
    audit = run_temporal_audit(JD_POSTGRES_16, jd, resume)

    pg_entries = [a for a in audit if "postgres" in a.requirement.lower()]
    assert len(pg_entries) >= 1
    assert pg_entries[0].allowed is True
    assert pg_entries[0].action_taken == "eligible_for_placement"


def test_tc_t03_k8s_129_blocked_for_2022_role():
    """TC-T03: Kubernetes 1.29 blocked for role ended 2022."""
    jd = analyze_jd(JD_K8S_129)
    resume = analyze_resume(RESUME_K8S_2022)
    audit = run_temporal_audit(JD_K8S_129, jd, resume)

    k8s_entries = [a for a in audit if "kubernetes" in a.requirement.lower() or "k8s" in a.requirement.lower()]
    assert len(k8s_entries) >= 1
    assert k8s_entries[0].allowed is False


def test_tc_t04_audit_lists_all_decisions():
    """TC-T04: Temporal audit lists placement decisions with allowed flag."""
    jd = analyze_jd(JD_POSTGRES_16 + "\n" + JD_K8S_129)
    resume = analyze_resume(RESUME_BETA_2023_PRESENT)
    audit = run_temporal_audit(JD_POSTGRES_16 + "\n" + JD_K8S_129, jd, resume)

    assert len(audit) >= 2
    for entry in audit:
        assert entry.requirement
        assert entry.action_taken in ("blocked", "eligible_for_placement", "skipped")
        assert isinstance(entry.allowed, bool)
        assert entry.reason


def test_is_role_eligible_date_logic():
    from datetime import date

    assert is_role_eligible(date(2024, 6, 1), "2023-09") is True
    assert is_role_eligible(date(2021, 12, 1), "2023-09") is False


def test_work_entry_date_parsing():
    entry = WorkEntry(company="Acme", title="DBA", dates="2019-2021", bullets=[])
    resume = analyze_resume(RESUME_ACME_2019_2021)
    assert len(resume.work_history) >= 1
