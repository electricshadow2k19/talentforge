import type { PackageResult } from './types'

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ?? ''

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('tf_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function parseError(res: Response): Promise<string> {
  const err = await res.json().catch(() => ({}))
  const detail = err.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d: { msg?: string }) => d.msg).join(', ')
  return `Request failed (${res.status})`
}

export interface User {
  id: string
  email: string
  name: string
  role: string
  is_active: boolean
}

export interface Candidate {
  id: string
  first_name: string
  last_name: string
  email: string | null
  phone: string | null
  current_location: string | null
  preferred_location: string | null
  availability: string | null
  status: string
  total_experience: string | null
  primary_skill: string | null
  secondary_skills: string[] | null
  notes: string | null
  created_at: string
  updated_at: string
  resume_count: number
}

export interface Resume {
  id: string
  candidate_id: string
  name: string
  resume_type: string
  parsed_text: string | null
  skills_extracted: string[] | null
  is_default: boolean
  created_at: string
}

export interface Submission {
  id: string
  candidate_id: string
  resume_id: string
  recruiter_id: string
  ats_score: number
  ats_score_before: number
  summary: string | null
  status: string
  created_at: string
  updated_at: string
  candidate_name?: string
  resume_name?: string
  recruiter_name?: string
  jd_title?: string
}

export interface DashboardStats {
  total_candidates: number
  active_bench: number
  total_recruiters: number
  submissions_this_month: number
  interview_count: number
  placement_count: number
}

export async function fetchHealth(): Promise<{ status: string; ai_enabled: boolean }> {
  const res = await fetch(`${API_BASE}/api/health`)
  if (!res.ok) throw new Error('API unavailable')
  return res.json()
}

export async function login(email: string, password: string): Promise<{ access_token: string; user: User }> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function fetchMe(): Promise<User> {
  const res = await fetch(`${API_BASE}/api/auth/me`, { headers: authHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function fetchDashboard(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE}/api/dashboard/stats`, { headers: authHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function fetchCandidates(params?: Record<string, string>): Promise<Candidate[]> {
  const qs = params ? `?${new URLSearchParams(params)}` : ''
  const res = await fetch(`${API_BASE}/api/candidates${qs}`, { headers: authHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function fetchCandidate(id: string): Promise<Candidate> {
  const res = await fetch(`${API_BASE}/api/candidates/${id}`, { headers: authHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function createCandidate(body: Partial<Candidate>): Promise<Candidate> {
  const res = await fetch(`${API_BASE}/api/candidates`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function updateCandidate(id: string, body: Partial<Candidate>): Promise<Candidate> {
  const res = await fetch(`${API_BASE}/api/candidates/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function deleteCandidate(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/candidates/${id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  })
  if (!res.ok) throw new Error(await parseError(res))
}

export async function uploadResume(
  candidateId: string,
  form: FormData,
): Promise<Resume> {
  const res = await fetch(`${API_BASE}/api/candidates/${candidateId}/resumes`, {
    method: 'POST',
    headers: authHeaders(),
    body: form,
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function deleteResume(candidateId: string, resumeId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/candidates/${candidateId}/resumes/${resumeId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  })
  if (!res.ok) throw new Error(await parseError(res))
}

export async function setDefaultResume(candidateId: string, resumeId: string): Promise<Resume> {
  const res = await fetch(
    `${API_BASE}/api/candidates/${candidateId}/resumes/${resumeId}?is_default=true`,
    { method: 'PATCH', headers: authHeaders() },
  )
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function fetchResumes(candidateId: string): Promise<Resume[]> {
  const res = await fetch(`${API_BASE}/api/candidates/${candidateId}/resumes`, { headers: authHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export function resumeFileUrl(candidateId: string, resumeId: string): string {
  return `${API_BASE}/api/candidates/${candidateId}/resumes/${resumeId}/file`
}

export async function fetchSubmissions(): Promise<Submission[]> {
  const res = await fetch(`${API_BASE}/api/submissions`, { headers: authHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function analyzeSubmission(form: FormData): Promise<PackageResult & { submission_id: string }> {
  const res = await fetch(`${API_BASE}/api/submissions/analyze`, {
    method: 'POST',
    headers: authHeaders(),
    body: form,
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function fetchRecruiters(): Promise<User[]> {
  const res = await fetch(`${API_BASE}/api/recruiters`, { headers: authHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function createRecruiter(body: { email: string; name: string; password: string }): Promise<User> {
  const res = await fetch(`${API_BASE}/api/recruiters`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function generatePackage(form: FormData): Promise<PackageResult> {
  const res = await fetch(`${API_BASE}/api/generate-package`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}
