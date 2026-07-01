import { FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  deleteCandidate,
  deleteResume,
  fetchCandidate,
  fetchResumes,
  resumeFileUrl,
  setDefaultResume,
  updateCandidate,
  uploadResume,
  type Candidate,
  type Resume,
} from '../api'
import { useAuth } from '../context/AuthContext'

const STATUSES = [
  'Active Bench',
  'Submitted',
  'Interview Scheduled',
  'Client Interview',
  'Offer',
  'Placed',
  'Inactive',
]

const emptyForm = (c?: Candidate) => ({
  first_name: c?.first_name ?? '',
  last_name: c?.last_name ?? '',
  email: c?.email ?? '',
  phone: c?.phone ?? '',
  current_location: c?.current_location ?? '',
  preferred_location: c?.preferred_location ?? '',
  availability: c?.availability ?? '',
  status: c?.status ?? 'Active Bench',
  total_experience: c?.total_experience ?? '',
  primary_skill: c?.primary_skill ?? '',
  secondary_skills: (c?.secondary_skills ?? []).join(', '),
  notes: c?.notes ?? '',
})

export default function CandidateDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { isAdmin } = useAuth()
  const [candidate, setCandidate] = useState<Candidate | null>(null)
  const [resumes, setResumes] = useState<Resume[]>([])
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState(emptyForm())
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [resumeForm, setResumeForm] = useState({ name: '', resume_type: '', is_default: false })
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [resumeText, setResumeText] = useState('')
  const [uploading, setUploading] = useState(false)

  const load = async () => {
    if (!id) return
    const [c, r] = await Promise.all([fetchCandidate(id), fetchResumes(id)])
    setCandidate(c)
    setForm(emptyForm(c))
    setResumes(r)
  }

  useEffect(() => {
    load().catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
  }, [id])

  const handleSave = async (e: FormEvent) => {
    e.preventDefault()
    if (!id) return
    setSaving(true)
    setError(null)
    try {
      const updated = await updateCandidate(id, {
        ...form,
        email: form.email || null,
        phone: form.phone || null,
        secondary_skills: form.secondary_skills
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      })
      setCandidate(updated)
      setEditing(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!id || !candidate) return
    if (!confirm(`Delete ${candidate.first_name} ${candidate.last_name}? This cannot be undone.`)) return
    try {
      await deleteCandidate(id)
      navigate('/candidates')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  const handleUploadResume = async (e: FormEvent) => {
    e.preventDefault()
    if (!id) return
    setUploading(true)
    setError(null)
    try {
      const fd = new FormData()
      fd.append('name', resumeForm.name)
      fd.append('resume_type', resumeForm.resume_type)
      fd.append('is_default', String(resumeForm.is_default))
      if (resumeFile) fd.append('file', resumeFile)
      else if (resumeText.trim()) fd.append('parsed_text', resumeText)
      else throw new Error('Upload a file or paste resume text')
      await uploadResume(id, fd)
      setResumeForm({ name: '', resume_type: '', is_default: false })
      setResumeFile(null)
      setResumeText('')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteResume = async (resumeId: string, name: string) => {
    if (!id) return
    if (!confirm(`Delete resume "${name}"?`)) return
    try {
      await deleteResume(id, resumeId)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  const handleSetDefault = async (resumeId: string) => {
    if (!id) return
    try {
      await setDefaultResume(id, resumeId)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed')
    }
  }

  if (!candidate) {
    return <div className="text-slate-500">{error ?? 'Loading…'}</div>
  }

  const token = localStorage.getItem('tf_token')

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/candidates" className="text-sm text-brand-600 hover:underline">
            ← Back to candidates
          </Link>
          <h2 className="mt-1 text-xl font-semibold">
            {candidate.first_name} {candidate.last_name}
          </h2>
          <p className="text-sm text-slate-500">{candidate.primary_skill} · {candidate.status}</p>
        </div>
        <div className="flex gap-2">
          <Link
            to={`/workspace?candidate=${id}`}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
          >
            Analyze
          </Link>
          {isAdmin && (
            <>
              <button
                type="button"
                onClick={() => setEditing(!editing)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
              >
                {editing ? 'Cancel' : 'Edit'}
              </button>
              <button
                type="button"
                onClick={handleDelete}
                className="rounded-lg border border-red-300 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                Delete
              </button>
            </>
          )}
        </div>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      {editing ? (
        <form onSubmit={handleSave} className="mb-8 grid gap-4 rounded-xl border border-slate-200 bg-white p-6 md:grid-cols-2">
          <Field label="First name" value={form.first_name} onChange={(v) => setForm({ ...form, first_name: v })} />
          <Field label="Last name" value={form.last_name} onChange={(v) => setForm({ ...form, last_name: v })} />
          <Field label="Email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} />
          <Field label="Phone" value={form.phone} onChange={(v) => setForm({ ...form, phone: v })} />
          <Field label="Current location" value={form.current_location} onChange={(v) => setForm({ ...form, current_location: v })} />
          <Field label="Preferred location" value={form.preferred_location} onChange={(v) => setForm({ ...form, preferred_location: v })} />
          <Field label="Availability" value={form.availability} onChange={(v) => setForm({ ...form, availability: v })} />
          <Field label="Experience" value={form.total_experience} onChange={(v) => setForm({ ...form, total_experience: v })} />
          <Field label="Primary skill" value={form.primary_skill} onChange={(v) => setForm({ ...form, primary_skill: v })} />
          <div>
            <label className="text-sm font-medium text-slate-700">Status</label>
            <select
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Secondary skills (comma-separated)</label>
            <input
              value={form.secondary_skills}
              onChange={(e) => setForm({ ...form, secondary_skills: e.target.value })}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div className="md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              rows={3}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-brand-600 px-6 py-2 text-sm font-medium text-white disabled:opacity-50 md:col-span-2 md:w-fit"
          >
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      ) : (
        <div className="mb-8 grid gap-4 rounded-xl border border-slate-200 bg-white p-6 md:grid-cols-2">
          <Info label="Email" value={candidate.email} />
          <Info label="Phone" value={candidate.phone} />
          <Info label="Location" value={candidate.current_location} />
          <Info label="Preferred" value={candidate.preferred_location} />
          <Info label="Availability" value={candidate.availability} />
          <Info label="Experience" value={candidate.total_experience} />
          <Info label="Primary skill" value={candidate.primary_skill} />
          <Info label="Status" value={candidate.status} />
          <div className="md:col-span-2">
            <Info label="Secondary skills" value={candidate.secondary_skills?.join(', ')} />
          </div>
          {candidate.notes && (
            <div className="md:col-span-2">
              <Info label="Notes" value={candidate.notes} />
            </div>
          )}
        </div>
      )}

      <h3 className="mb-3 text-lg font-semibold">Resumes ({resumes.length})</h3>

      {isAdmin && (
        <form onSubmit={handleUploadResume} className="mb-6 rounded-xl border border-slate-200 bg-white p-4">
          <p className="mb-3 text-sm font-medium text-slate-700">Upload new resume</p>
          <div className="grid gap-3 md:grid-cols-3">
            <input
              placeholder="Resume name (e.g. DevOps Resume)"
              value={resumeForm.name}
              onChange={(e) => setResumeForm({ ...resumeForm, name: e.target.value })}
              className="rounded border px-3 py-2 text-sm"
              required
            />
            <input
              placeholder="Type (e.g. DevOps)"
              value={resumeForm.resume_type}
              onChange={(e) => setResumeForm({ ...resumeForm, resume_type: e.target.value })}
              className="rounded border px-3 py-2 text-sm"
              required
            />
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={resumeForm.is_default}
                onChange={(e) => setResumeForm({ ...resumeForm, is_default: e.target.checked })}
              />
              Set as default
            </label>
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)}
              className="text-sm"
            />
            <textarea
              placeholder="Or paste resume text…"
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              rows={4}
              className="rounded border px-3 py-2 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={uploading}
            className="mt-3 rounded-lg bg-brand-600 px-4 py-2 text-sm text-white disabled:opacity-50"
          >
            {uploading ? 'Uploading…' : 'Upload resume'}
          </button>
        </form>
      )}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="border-b bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Skills</th>
              <th className="px-4 py-3">Default</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {resumes.map((r) => (
              <tr key={r.id} className="border-b last:border-0">
                <td className="px-4 py-3 font-medium">{r.name}</td>
                <td className="px-4 py-3">{r.resume_type}</td>
                <td className="px-4 py-3 text-slate-600">
                  {(r.skills_extracted ?? []).slice(0, 5).join(', ')}
                  {(r.skills_extracted?.length ?? 0) > 5 ? '…' : ''}
                </td>
                <td className="px-4 py-3">
                  {r.is_default ? (
                    <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs text-emerald-800">Default</span>
                  ) : isAdmin ? (
                    <button
                      type="button"
                      onClick={() => handleSetDefault(r.id)}
                      className="text-xs text-brand-600 hover:underline"
                    >
                      Set default
                    </button>
                  ) : (
                    '—'
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-2">
                    <a
                      href={`${resumeFileUrl(id!, r.id)}${token ? `?token=${token}` : ''}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand-600 hover:underline"
                      onClick={(e) => {
                        e.preventDefault()
                        fetch(resumeFileUrl(id!, r.id), { headers: { Authorization: `Bearer ${token}` } })
                          .then((res) => res.blob())
                          .then((blob) => {
                            const url = URL.createObjectURL(blob)
                            window.open(url, '_blank')
                          })
                          .catch(() => setError('Could not open file'))
                      }}
                    >
                      View
                    </a>
                    {isAdmin && (
                      <button
                        type="button"
                        onClick={() => handleDeleteResume(r.id, r.name)}
                        className="text-red-600 hover:underline"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {resumes.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  No resumes yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div>
      <label className="text-sm font-medium text-slate-700">{label}</label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
      />
    </div>
  )
}

function Info({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-0.5 text-sm text-slate-800">{value || '—'}</p>
    </div>
  )
}
