"""Shared keyword lists and categorization for JD/resume analysis."""

import re

TECH_SKILLS = [
    "GitHub Actions", "GitLab CI", "GitLab", "GitHub", "CloudFormation",
    "Node.js", "TypeScript", "JavaScript", "PostgreSQL", "Kubernetes",
    "Terraform", "Ansible", "Prometheus", "Grafana", "Datadog", "Splunk",
    "Snowflake", "Databricks", "Microservices", "CloudWatch", "CloudTrail",
    "Azure DevOps", "Azure SQL", "HP Fortify", "Black Duck",
    "AWS", "Azure", "GCP", "Docker", "Jenkins", "Python", "Java", "Scala",
    "Spark", "SQL", "Linux", "CI/CD", "DevOps", "Agile", "Scrum", "SAFe",
    "Fortify", "Security", "OWASP", "WAF", "ECS", "EKS", "Lambda", "Helm",
    "ArgoCD", "Redis", "Kafka", "MongoDB", "MySQL", "Oracle", "REST", "API",
    "SRE", "Networking", "BGP", "DNS", "Chef", "Puppet", "Go", "Rust",
    "C#", ".NET", "Spring", "React", "Git", "RMF", "NIST", "STIG", "FISMA",
    "SOC 2", "ISO 27001", "DevSecOps", "IaC", "Software Factory",
]

SHORT_SKILL_STRICT = {"go", "git", "api", "sql", "c#", "r"}

PROGRAMMING_LANGS = {
    "python", "java", "javascript", "typescript", "scala", "go", "rust",
    "c#", ".net", "sql", "node.js",
}

CLOUD_PLATFORMS = {"aws", "azure", "gcp", "ecs", "eks", "lambda", "cloudformation"}

DEVOPS_TOOLS = {
    "terraform", "ansible", "jenkins", "gitlab", "github", "docker", "kubernetes",
    "helm", "argocd", "ci/cd", "devops", "chef", "puppet", "gitlab ci",
    "github actions",
}

SECURITY_TOOLS = {
    "fortify", "hp fortify", "black duck", "owasp", "waf", "rmf", "nist",
    "stig", "fisma", "security", "devsecops", "soc 2",
}

SOFT_SKILLS = {
    "communication", "leadership", "collaboration", "problem solving",
    "mentoring", "stakeholder", "presentation", "teamwork", "agile", "scrum",
}

CERT_KEYWORDS = re.compile(
    r"certif|AWS Certified|Azure|GCP|CKA|CKAD|PMP|CSM|CSPO|Security\+|CISSP|CISM",
    re.I,
)


def skill_regex(skill: str) -> re.Pattern[str]:
    escaped = re.escape(skill)
    if skill.upper() == "SAFe":
        return re.compile(r"\bSAFe\b")
    if skill.lower() in SHORT_SKILL_STRICT or len(skill) <= 3:
        return re.compile(rf"\b{escaped}\b", re.I)
    return re.compile(rf"\b{escaped}\b", re.I)


def keyword_in_text(keyword: str, text: str) -> bool:
    return skill_regex(keyword).search(text) is not None


def find_skills_in_text(text: str) -> list[str]:
    found: list[str] = []
    for skill in sorted(TECH_SKILLS, key=len, reverse=True):
        if keyword_in_text(skill, text):
            found.append(skill)
    return sorted(set(found), key=str.lower)


def categorize_skill(skill: str) -> str:
    low = skill.lower()
    if low in PROGRAMMING_LANGS or any(low == p for p in PROGRAMMING_LANGS):
        return "programming"
    if low in CLOUD_PLATFORMS or any(p in low for p in CLOUD_PLATFORMS):
        return "cloud"
    if low in DEVOPS_TOOLS or any(p in low for p in DEVOPS_TOOLS):
        return "devops"
    if low in SECURITY_TOOLS or any(p in low for p in SECURITY_TOOLS):
        return "security"
    return "general"


def categorize_skills(skills: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {
        "programming_languages": [],
        "cloud_platforms": [],
        "devops_tools": [],
        "security_tools": [],
        "general": [],
    }
    seen: set[str] = set()
    for s in skills:
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        cat = categorize_skill(s)
        bucket = {
            "programming": "programming_languages",
            "cloud": "cloud_platforms",
            "devops": "devops_tools",
            "security": "security_tools",
        }.get(cat, "general")
        if bucket == "general":
            out["general"].append(s)
        else:
            out[bucket].append(s)
    return out
