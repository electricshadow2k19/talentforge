import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { analyzeSubmission, fetchCandidates, fetchResumes, type Candidate, type Resume } from '../api'
import type { PackageResult } from '../types'
import { ResultsPanel } from '../components/ResultsPanel'

type ResumeMode = 'database' | 'adhoc'

export default function WorkspacePage() {
  const [params] = useSearchParams()
  const preselect = params.get('candidate')

  const [resumeMode, setResumeMode] = useState<ResumeMode>(preselect ? 'database' : 'database')
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [candidateId, setCandidateId] = useState(preselect ?? '')
  const [resumes, setResumes] = useState<Resume[]>([])
  const [resumeId, setResumeId] = useState('')
  const [resumeText, setResumeText] = useState('')
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [jd, setJd] = useState('')
  const [jdFile, setJdFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PackageResult | null>(null)

  useEffect(() => {
    fetchCandidates().then(setCandidates).catch(() => {})
  }, [])

  useEffect(() => {
    if (resumeMode !== 'database' || !candidateId) {
      if (resumeMode !== 'database') {
        setResumes([])
        setResumeId('')
      }
      return
    }
    fetchResumes(candidateId)
      .then((rows) => {
        setResumes(rows)
        const def = rows.find((r) => r.is_default) ?? rows[0]
        setResumeId(def?.id ?? '')
      })
      .catch(() => setResumes([]))
  }, [candidateId, resumeMode])

  const runAnalysis = async () => {
    const hasJd = jdFile || jd.trim()
    if (!hasJd) {
      setError('Job description is required (paste or upload)')
      return
    }
    if (resumeMode === 'database' && (!candidateId || !resumeId)) {
      setError('Select candidate and resume version')
      return
    }
    if (resumeMode === 'adhoc' && !resumeFile && !resumeText.trim()) {
      setError('Paste resume text or upload a file')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const form = new FormData()
      if (resumeMode === 'database') {
        form.append('candidate_id', candidateId)
        form.append('resume_id', resumeId)
      } else {
        if (resumeFile) form.append('resume_file', resumeFile)
        else form.append('resume_text', resumeText)
      }
      if (jdFile) form.append('jd_file', jdFile)
      else form.append('job_description', jd)
      const data = await analyzeSubmission(form)
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2 className="text-xl font-semibold">Recruiter Workspace</h2>
      <p className="text-sm text-slate-500">
        Provide a job description and resume, then run JD-driven evaluation and optimization
      </p>

      <div className="mt-6 space-y-6">
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <h3 className="text-sm font-semibold text-slate-800">Job description (required)</h3>
          <textarea
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            rows={8}
            className="mt-2 w-full rounded-lg border border-slate-300 p-3 text-sm"
            placeholder="Paste full JD or upload file below…"
          />
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={(e) => setJdFile(e.target.files?.[0] ?? null)}
            className="mt-2 text-sm"
          />
          {jdFile && <p className="mt-1 text-xs text-slate-500">File: {jdFile.name}</p>}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <h3 className="text-sm font-semibold text-slate-800">Resume (required)</h3>
          <div className="mt-3 flex gap-4">
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="radio"
                name="resumeMode"
                checked={resumeMode === 'database'}
                onChange={() => setResumeMode('database')}
              />
              From candidate database
            </label>
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="radio"
                name="resumeMode"
                checked={resumeMode === 'adhoc'}
                onChange={() => setResumeMode('adhoc')}
              />
              Ad hoc (paste or upload)
            </label>
          </div>

          {resumeMode === 'database' ? (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium text-slate-700">Candidate</label>
                <select
                  value={candidateId}
                  onChange={(e) => setCandidateId(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="">Select…</option>
                  {candidates.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.first_name} {c.last_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Resume version</label>
                <select
                  value={resumeId}
                  onChange={(e) => setResumeId(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="">Select…</option>
                  {resumes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name} ({r.resume_type})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          ) : (
            <div className="mt-4">
              <textarea
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                rows={10}
                className="w-full rounded-lg border border-slate-300 p-3 text-sm"
                placeholder="Paste resume text or upload DOCX/PDF below…"
              />
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)}
                className="mt-2 text-sm"
              />
              {resumeFile && <p className="mt-1 text-xs text-slate-500">File: {resumeFile.name}</p>}
            </div>
          )}
        </div>
      </div>

      {error && <div className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <button
        type="button"
        disabled={loading}
        onClick={runAnalysis}
        className="mt-6 rounded-xl bg-brand-600 px-8 py-3 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
      >
        {loading ? 'Running evaluation…' : 'Run JD Evaluation & Optimize Resume'}
      </button>

      {result && (
        <div className="mt-8">
          <ResultsPanel result={result} />
        </div>
      )}
    </div>
  )
}
