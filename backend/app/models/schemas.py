from pydantic import BaseModel, Field, model_validator


class SkillMatch(BaseModel):
    skill: str
    matched: bool
    resume_evidence: str | None = None
    jd_requirement: str | None = None


class VersionedTool(BaseModel):
    tool: str
    version: str
    display_name: str
    release_date: str | None = None
    confidence: str = "high"  # high | medium | low


class TemporalAuditEntry(BaseModel):
    requirement: str
    release_date: str | None = None
    placed_in_role: str | None = None
    company: str | None = None
    role_dates: str | None = None
    allowed: bool = False
    action_taken: str = "blocked"  # blocked | eligible_for_placement | skipped | placed
    reason: str = ""


class JDAnalysis(BaseModel):
    """Structured JD JSON (Step 2)."""
    title: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    programming_languages: list[str] = Field(default_factory=list)
    cloud_platforms: list[str] = Field(default_factory=list)
    devops_tools: list[str] = Field(default_factory=list)
    security_tools: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    experience_years: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    industry_keywords: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    location: str | None = None
    work_mode: str | None = None
    visa_requirements: list[str] = Field(default_factory=list)  # extracted, not scored
    rate_notes: str | None = None
    summary: str | None = None
    versioned_tools: list[VersionedTool] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    # Backward-compatible aliases
    mandatory_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def sync_skill_aliases(self) -> "JDAnalysis":
        if self.required_skills and not self.mandatory_skills:
            self.mandatory_skills = list(self.required_skills)
        elif self.mandatory_skills and not self.required_skills:
            self.required_skills = list(self.mandatory_skills)
        if self.preferred_skills and not self.nice_to_have_skills:
            self.nice_to_have_skills = list(self.preferred_skills)
        elif self.nice_to_have_skills and not self.preferred_skills:
            self.preferred_skills = list(self.nice_to_have_skills)
        return self

    def structured_json(self) -> dict:
        return {
            "title": self.title,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "programming_languages": self.programming_languages,
            "cloud_platforms": self.cloud_platforms,
            "devops_tools": self.devops_tools,
            "security_tools": self.security_tools,
            "certifications": self.certifications,
            "experience_years": self.experience_years,
            "responsibilities": self.responsibilities,
            "industry_keywords": self.industry_keywords,
            "soft_skills": self.soft_skills,
        }


class WorkEntry(BaseModel):
    company: str | None = None
    title: str | None = None
    dates: str | None = None
    bullets: list[str] = Field(default_factory=list)


class ResumeAnalysis(BaseModel):
    """Candidate profile object (Step 3)."""
    candidate_name: str | None = None
    email: str | None = None
    phone: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    work_history: list[WorkEntry] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    experience_years: str | None = None
    visa_status: str | None = None  # not used in ATS scoring
    location: str | None = None


class ATSSectionScore(BaseModel):
    section: str
    score: int
    weight_pct: int = 0
    notes: str | None = None


class ATSScore(BaseModel):
    sections: list[ATSSectionScore] = Field(default_factory=list)
    overall: int = 0
    missing_keywords: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    skill_matches: list[SkillMatch] = Field(default_factory=list)
    keyword_coverage_pct: int = 0


class GapAnalysis(BaseModel):
    """Step 5 — gap analysis."""
    missing_skills: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    missing_technologies: list[str] = Field(default_factory=list)
    missing_certifications: list[str] = Field(default_factory=list)
    missing_responsibilities: list[str] = Field(default_factory=list)
    optimization_suggestions: list[str] = Field(default_factory=list)


class GeneratedSections(BaseModel):
    """Step 7 — AI generated sections."""
    professional_summary: str
    key_strengths: list[str] = Field(default_factory=list)
    top_matching_skills: list[str] = Field(default_factory=list)
    technical_highlights: list[str] = Field(default_factory=list)
    client_submission_summary: str


class RatedQuestion(BaseModel):
    question: str
    difficulty: str = "medium"  # easy | medium | hard


class InterviewQuestions(BaseModel):
    technical: list[RatedQuestion] = Field(default_factory=list)
    scenario: list[RatedQuestion] = Field(default_factory=list)
    behavioral: list[RatedQuestion] = Field(default_factory=list)
    client_specific: list[RatedQuestion] = Field(default_factory=list)
    recruiter_screening: list[str] = Field(default_factory=list)


class SubmissionPackage(BaseModel):
    candidate_summary: str
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    fit_statement: str | None = None


class EmailDrafts(BaseModel):
    vendor_email: str
    candidate_email: str
    manager_email: str


class Dashboard(BaseModel):
    ats_score: int
    ats_score_before: int
    keyword_coverage_pct: int
    top_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    optimization_suggestions: list[str] = Field(default_factory=list)
    scoring_weights: dict[str, float] = Field(default_factory=dict)


class DocumentArtifacts(BaseModel):
    optimized_resume_docx_b64: str | None = None
    optimized_resume_pdf_b64: str | None = None
    candidate_summary_text: str | None = None
    interview_sheet_text: str | None = None
    submission_package_text: str | None = None
    submission_package_pdf_b64: str | None = None
    interview_sheet_pdf_b64: str | None = None


class GeneratePackageResponse(BaseModel):
    jd_analysis: JDAnalysis
    resume_analysis: ResumeAnalysis
    ats_score: ATSScore
    ats_score_before: int = 0
    gap_analysis: GapAnalysis
    generated_sections: GeneratedSections
    dashboard: Dashboard
    original_resume: str = ""
    optimized_resume: str
    submission_package: SubmissionPackage
    interview_questions: InterviewQuestions
    email_drafts: EmailDrafts
    documents: DocumentArtifacts = Field(default_factory=DocumentArtifacts)
    temporal_audit: list[TemporalAuditEntry] = Field(default_factory=list)
    processing_mode: str
    elapsed_seconds: float


class TextInputRequest(BaseModel):
    job_description: str
    resume: str


class HealthResponse(BaseModel):
    status: str
    ai_enabled: bool
    model: str
