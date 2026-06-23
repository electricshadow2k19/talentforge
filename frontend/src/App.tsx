import { useEffect, useState } from 'react'
import { fetchHealth, generatePackage } from './api'
import type { PackageResult } from './types'
import { ResultsPanel } from './components/ResultsPanel'

const SAMPLE_JD = `Senior DevOps Engineer — Dallas, TX (Hybrid)

Requirements:
- 8+ years experience
- AWS, Terraform, Kubernetes, Python, CI/CD
- Jenkins, Docker, ECS
- USC or Green Card only
- No visa sponsorship

Nice to have: Ansible, Prometheus, security background`

const SAMPLE_RESUME = `ARUN KUMAR VALLALA
DevOps Engineer | kumar.arunvallala@gmail.com | +1-516-928-9153

PROFESSIONAL SUMMARY
DevOps Engineer with 14 years in cloud infrastructure, CI/CD, and security-focused solutions.

SKILLS: AWS, Terraform, Kubernetes, Docker, Jenkins, Git, Python, ECS, MySQL, HP Fortify

EXPERIENCE
DigiCert Inc (Vercara) — DevOps Engineer | 2023–2026
- Built CI/CD pipelines with Jenkins and Terraform on AWS ECS
- Infrastructure as Code deployments and containerized workloads
- DDoS mitigation support and security scanning (Fortify, Black Duck)

CERTIFICATIONS: CSM, CSPO, ISC2 CC training`

type Tab = 'paste' | 'upload'

export default function App() {
  const [jd, setJd] = useState('')
  const [resume, setResume] = useState('')
  const [jdFile, setJdFile] = useState<File | null>(null)
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [inputMode, setInputMode] = useState<Tab>('paste')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PackageResult | null>(null)
  const [aiEnabled, setAiEnabled] = useState(false)

  useEffect(() => {
    fetchHealth().then((h) => setAiEnabled(h.ai_enabled)).catch(() => setAiEnabled(false))
  }, [])

  const loadSamples = () => {
    setJd(SAMPLE_JD)
    setResume(SAMPLE_RESUME)
    setJdFile(null)
    setResumeFile(null)
  }

  const handleGenerate = async () => {
    setError(null)
    setLoading(true)
    setResult(null)
    try {
      const form = new FormData()
      if (inputMode === 'paste') {
        form.append('job_description', jd)
        form.append('resume', resume)
      } else {
        if (jdFile) form.append('jd_file', jdFile)
        else form.append('job_description', jd)
        if (resumeFile) form.append('resume_file', resumeFile)
        else form.append('resume', resume)
      }
      const data = await generatePackage(form)
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  const canSubmit =
    inputMode === 'paste'
      ? jd.trim().length > 20 && resume.trim().length > 20
      : (jdFile || jd.trim().length > 20) && (resumeFile || resume.trim().length > 20)

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div>
            <h1 className="text-xl font-bold text-brand-900">
              Talent<span className="text-brand-600">Forge</span>
            </h1>
            <p className="text-sm text-slate-500">GenvenX Recruiter Productivity AI</p>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span
              className={`rounded-full px-3 py-1 ${
                aiEnabled ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
              }`}
            >
              {aiEnabled ? 'AI enabled' : 'Heuristic mode'}
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        <section className="mb-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-1 text-lg font-semibold">One-click submission package</h2>
          <p className="mb-6 text-sm text-slate-600">
            JD + Resume → ATS score, optimized resume, summary, questions, emails — target under 2 minutes.
          </p>

          <div className="mb-4 flex gap-2">
            <button
              type="button"
              onClick={() => setInputMode('paste')}
              className={`rounded-lg px-4 py-2 text-sm font-medium ${
                inputMode === 'paste' ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-700'
              }`}
            >
              Paste text
            </button>
            <button
              type="button"
              onClick={() => setInputMode('upload')}
              className={`rounded-lg px-4 py-2 text-sm font-medium ${
                inputMode === 'upload' ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-700'
              }`}
            >
              Upload files
            </button>
            <button
              type="button"
              onClick={loadSamples}
              className="ml-auto rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
            >
              Load sample (DevOps JD)
            </button>
          </div>

          {inputMode === 'paste' ? (
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Job Description</label>
                <textarea
                  value={jd}
                  onChange={(e) => setJd(e.target.value)}
                  rows={14}
                  className="w-full rounded-lg border border-slate-300 p-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  placeholder="Paste JD text or email..."
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Resume</label>
                <textarea
                  value={resume}
                  onChange={(e) => setResume(e.target.value)}
                  rows={14}
                  className="w-full rounded-lg border border-slate-300 p-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  placeholder="Paste resume text..."
                />
              </div>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">JD file (PDF, DOCX, TXT)</label>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => setJdFile(e.target.files?.[0] ?? null)}
                  className="w-full text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Resume file</label>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)}
                  className="w-full text-sm"
                />
              </div>
            </div>
          )}

          {error && (
            <div className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
          )}

          <button
            type="button"
            disabled={!canSubmit || loading}
            onClick={handleGenerate}
            className="mt-6 w-full rounded-xl bg-brand-600 py-3 text-base font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50 md:w-auto md:px-10"
          >
            {loading ? 'Generating package…' : 'Generate submission package'}
          </button>
        </section>

        {result && <ResultsPanel result={result} />}
      </main>

      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        TalentForge MVP · GenvenX Technologies · Review all outputs before client submission
      </footer>
    </div>
  )
}
