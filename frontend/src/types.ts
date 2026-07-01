export interface JDAnalysis {
  title: string | null
  required_skills: string[]
  preferred_skills: string[]
  mandatory_skills: string[]
  nice_to_have_skills: string[]
  programming_languages: string[]
  cloud_platforms: string[]
  devops_tools: string[]
  security_tools: string[]
  certifications: string[]
  experience_years: string | null
  responsibilities: string[]
  industry_keywords: string[]
  soft_skills: string[]
  visa_requirements: string[]
  location: string | null
  work_mode: string | null
  rate_notes: string | null
  summary: string | null
}

export interface WorkEntry {
  company: string | null
  title: string | null
  dates: string | null
  bullets: string[]
}

export interface ResumeAnalysis {
  candidate_name: string | null
  email: string | null
  phone: string | null
  summary: string | null
  skills: string[]
  tools: string[]
  technologies: string[]
  experience_years: string | null
  certifications: string[]
  education: string[]
  work_history: WorkEntry[]
  projects: string[]
  visa_status: string | null
  location: string | null
}

export interface ATSSectionScore {
  section: string
  score: number
  weight_pct?: number
  notes?: string | null
}

export interface ATSScore {
  sections: ATSSectionScore[]
  overall: number
  missing_keywords: string[]
  matched_keywords: string[]
  keyword_coverage_pct: number
  skill_matches: { skill: string; matched: boolean; resume_evidence?: string | null }[]
}

export interface GapAnalysis {
  missing_skills: string[]
  missing_keywords: string[]
  missing_technologies: string[]
  missing_certifications: string[]
  missing_responsibilities: string[]
  optimization_suggestions: string[]
}

export interface GeneratedSections {
  professional_summary: string
  key_strengths: string[]
  top_matching_skills: string[]
  technical_highlights: string[]
  client_submission_summary: string
}

export interface RatedQuestion {
  question: string
  difficulty: string
}

export interface SubmissionPackage {
  candidate_summary: string
  strengths: string[]
  risks: string[]
  fit_statement: string | null
}

export interface InterviewQuestions {
  technical: RatedQuestion[]
  scenario: RatedQuestion[]
  behavioral: RatedQuestion[]
  client_specific: RatedQuestion[]
  recruiter_screening: string[]
}

export interface EmailDrafts {
  vendor_email: string
  candidate_email: string
  manager_email: string
}

export interface Dashboard {
  ats_score: number
  ats_score_before: number
  keyword_coverage_pct: number
  top_skills: string[]
  missing_skills: string[]
  optimization_suggestions: string[]
  scoring_weights: Record<string, number>
}

export interface DocumentArtifacts {
  optimized_resume_docx_b64: string | null
  optimized_resume_pdf_b64: string | null
  candidate_summary_text: string | null
  interview_sheet_text: string | null
  submission_package_text: string | null
  submission_package_pdf_b64: string | null
  interview_sheet_pdf_b64: string | null
}

export interface TemporalAuditEntry {
  requirement: string
  release_date: string | null
  placed_in_role: string | null
  company: string | null
  role_dates: string | null
  allowed: boolean
  action_taken: string
  reason: string
}

export interface PackageResult {
  jd_analysis: JDAnalysis
  resume_analysis: ResumeAnalysis
  ats_score: ATSScore
  ats_score_before: number
  gap_analysis: GapAnalysis
  generated_sections: GeneratedSections
  dashboard: Dashboard
  original_resume: string
  optimized_resume: string
  submission_package: SubmissionPackage
  interview_questions: InterviewQuestions
  email_drafts: EmailDrafts
  documents: DocumentArtifacts
  temporal_audit: TemporalAuditEntry[]
  processing_mode: string
  elapsed_seconds: number
}
