export interface JDAnalysis {
  title: string | null
  mandatory_skills: string[]
  nice_to_have_skills: string[]
  experience_years: string | null
  visa_requirements: string[]
  location: string | null
  work_mode: string | null
  rate_notes: string | null
  summary: string | null
}

export interface ResumeAnalysis {
  candidate_name: string | null
  email: string | null
  phone: string | null
  skills: string[]
  experience_years: string | null
  certifications: string[]
  education: string[]
  visa_status: string | null
  location: string | null
  summary: string | null
}

export interface ATSSectionScore {
  section: string
  score: number
  notes?: string | null
}

export interface ATSScore {
  sections: ATSSectionScore[]
  overall: number
  missing_keywords: string[]
  matched_keywords: string[]
  skill_matches: { skill: string; matched: boolean; resume_evidence?: string | null }[]
}

export interface SubmissionPackage {
  candidate_summary: string
  strengths: string[]
  risks: string[]
  fit_statement: string | null
}

export interface InterviewQuestions {
  technical: string[]
  scenario: string[]
  client_specific: string[]
  recruiter_screening: string[]
}

export interface EmailDrafts {
  vendor_email: string
  candidate_email: string
  manager_email: string
}

export interface PackageResult {
  jd_analysis: JDAnalysis
  resume_analysis: ResumeAnalysis
  ats_score: ATSScore
  optimized_resume: string
  submission_package: SubmissionPackage
  interview_questions: InterviewQuestions
  email_drafts: EmailDrafts
  processing_mode: string
  elapsed_seconds: number
}
