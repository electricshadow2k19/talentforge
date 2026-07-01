"""Seed TalentForge with admin, recruiters, candidates, and resumes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth.security import hash_password
from app.db.models import Candidate, CandidateStatus, Resume, User, UserRole
from app.db.session import SessionLocal
from app.services.analyzers import analyze_resume

SAMPLE_RESUME = """RAJ KUMAR
Senior DevOps Engineer | raj.kumar@email.com | Dallas, TX

PROFESSIONAL SUMMARY
DevOps Engineer with 10 years in AWS, Kubernetes, Terraform, CI/CD, and cloud security.

SKILLS: AWS, Terraform, Kubernetes, Docker, Jenkins, Python, Ansible, Prometheus, Git

EXPERIENCE
Northrop Grumman — DevOps Engineer | 2020–2026
- Built CI/CD pipelines with Jenkins and Terraform on AWS EKS
- Infrastructure as Code and containerized workloads
- Security scanning and compliance automation

CERTIFICATIONS: AWS Solutions Architect Associate"""


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == "admin@genvenx.com").first():
            print("Seed data already exists — skipping")
            return

        admin = User(
            email="admin@genvenx.com",
            name="Admin User",
            role=UserRole.admin,
            password_hash=hash_password("admin123"),
            is_active=True,
        )
        hira = User(
            email="hira@genvenx.com",
            name="Hira Patel",
            role=UserRole.recruiter,
            password_hash=hash_password("recruiter123"),
            is_active=True,
        )
        db.add_all([admin, hira])
        db.flush()

        people = [
            ("Raj", "Kumar", "DevOps", "10 years", "Dallas, TX"),
            ("Pavan", "Reddy", "Cloud", "8 years", "Austin, TX"),
            ("Alex", "Thomas", "SRE", "12 years", "Remote"),
        ]
        resume_types = [
            ("DevOps Resume", "DevOps"),
            ("QA Resume", "QA"),
            ("Cloud Resume", "Cloud"),
            ("SRE Resume", "SRE"),
        ]

        for first, last, skill, exp, loc in people:
            c = Candidate(
                first_name=first,
                last_name=last,
                email=f"{first.lower()}.{last.lower()}@email.com",
                current_location=loc,
                preferred_location=loc,
                availability="Immediate",
                status=CandidateStatus.active_bench,
                total_experience=exp,
                primary_skill=skill,
                secondary_skills=["AWS", "Kubernetes", "Terraform"],
                created_by_id=admin.id,
            )
            db.add(c)
            db.flush()
            profile = analyze_resume(SAMPLE_RESUME.replace("RAJ KUMAR", f"{first.upper()} {last.upper()}"))
            for i, (rname, rtype) in enumerate(resume_types):
                text = SAMPLE_RESUME.replace("RAJ KUMAR", f"{first.upper()} {last.upper()}").replace(
                    "DevOps Engineer", f"{rtype} Engineer"
                )
                db.add(
                    Resume(
                        candidate_id=c.id,
                        name=rname,
                        resume_type=rtype,
                        parsed_text=text,
                        skills_extracted=profile.skills,
                        is_default=i == 0,
                    )
                )

        db.commit()
        print("Seed complete:")
        print("  Admin: admin@genvenx.com / admin123")
        print("  Recruiter: hira@genvenx.com / recruiter123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
