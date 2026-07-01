import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { createCandidate, fetchCandidates, type Candidate } from '../api'
import { useAuth } from '../context/AuthContext'

export default function CandidatesPage() {
  const { isAdmin } = useAuth()
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [q, setQ] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ first_name: '', last_name: '', primary_skill: '', total_experience: '' })

  const load = () => {
    fetchCandidates(q ? { q } : undefined)
      .then(setCandidates)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
  }

  useEffect(() => {
    load()
  }, [])

  const handleCreate = async () => {
    await createCandidate(form)
    setShowForm(false)
    setForm({ first_name: '', last_name: '', primary_skill: '', total_experience: '' })
    load()
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Candidates</h2>
          <p className="text-sm text-slate-500">Bench consultants and talent database</p>
        </div>
        {isAdmin && (
          <button
            type="button"
            onClick={() => setShowForm(!showForm)}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white"
          >
            Add candidate
          </button>
        )}
      </div>

      {showForm && (
        <div className="mt-4 grid gap-3 rounded-xl border border-slate-200 bg-white p-4 md:grid-cols-4">
          <input placeholder="First name" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} className="rounded border px-3 py-2 text-sm" />
          <input placeholder="Last name" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} className="rounded border px-3 py-2 text-sm" />
          <input placeholder="Primary skill" value={form.primary_skill} onChange={(e) => setForm({ ...form, primary_skill: e.target.value })} className="rounded border px-3 py-2 text-sm" />
          <input placeholder="Experience" value={form.total_experience} onChange={(e) => setForm({ ...form, total_experience: e.target.value })} className="rounded border px-3 py-2 text-sm" />
          <button type="button" onClick={handleCreate} className="rounded bg-brand-600 px-4 py-2 text-sm text-white md:col-span-4 md:w-fit">
            Save
          </button>
        </div>
      )}

      <div className="mt-4 flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search name, skill…"
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <button type="button" onClick={load} className="rounded-lg border border-slate-300 px-4 py-2 text-sm">
          Search
        </button>
      </div>

      {error && <p className="mt-4 text-red-600">{error}</p>}

      <div className="mt-4 overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="border-b bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Primary Skill</th>
              <th className="px-4 py-3">Experience</th>
              <th className="px-4 py-3">Location</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Resumes</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((c) => (
              <tr key={c.id} className="border-b last:border-0">
                <td className="px-4 py-3 font-medium">
                  {c.first_name} {c.last_name}
                </td>
                <td className="px-4 py-3">{c.primary_skill}</td>
                <td className="px-4 py-3">{c.total_experience}</td>
                <td className="px-4 py-3">{c.current_location}</td>
                <td className="px-4 py-3">{c.status}</td>
                <td className="px-4 py-3">{c.resume_count}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-3">
                    <Link to={`/candidates/${c.id}`} className="text-brand-600 hover:underline">
                      {isAdmin ? 'Manage' : 'View'}
                    </Link>
                    <Link to={`/workspace?candidate=${c.id}`} className="text-slate-500 hover:underline">
                      Analyze
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
