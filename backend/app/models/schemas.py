from pydantic import BaseModel, Field


class SkillMatch(BaseModel):
    skill: str
    matched: bool
    resume_evidence: str | None = None
    jd_requirement: str | None = None


class JDAnalysis(BaseModel):
    title: str | None = None
    mandatory_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    experience_years: str | None = None
    visa_requirements: list[str] = Field(default_factory=list)
    location: str | None = None
    work_mode: str | None = None  # Remote, Hybrid, Onsite
    rate_notes: str | None = None
    summary: str | None = None


class ResumeAnalysis(BaseModel):
    candidate_name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: str | None = None
    certifications: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    visa_status: str | None = None
    location: str | None = None
    summary: str | None = None


class ATSSectionScore(BaseModel):
    section: str
    score: int
    notes: str | None = None


class ATSScore(BaseModel):
    sections: list[ATSSectionScore] = Field(default_factory=list)
    overall: int = 0
    missing_keywords: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    skill_matches: list[SkillMatch] = Field(default_factory=list)


class SubmissionPackage(BaseModel):
    candidate_summary: str
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    fit_statement: str | None = None


class InterviewQuestions(BaseModel):
    technical: list[str] = Field(default_factory=list)
    scenario: list[str] = Field(default_factory=list)
    client_specific: list[str] = Field(default_factory=list)
    recruiter_screening: list[str] = Field(default_factory=list)


class EmailDrafts(BaseModel):
    vendor_email: str
    candidate_email: str
    manager_email: str


class GeneratePackageResponse(BaseModel):
    jd_analysis: JDAnalysis
    resume_analysis: ResumeAnalysis
    ats_score: ATSScore
    optimized_resume: str
    submission_package: SubmissionPackage
    interview_questions: InterviewQuestions
    email_drafts: EmailDrafts
    processing_mode: str  # "ai" | "heuristic"
    elapsed_seconds: float


class TextInputRequest(BaseModel):
    job_description: str
    resume: str


class HealthResponse(BaseModel):
    status: str
    ai_enabled: bool
    model: str
