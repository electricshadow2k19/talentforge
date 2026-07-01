import { FormEvent, useEffect, useState } from 'react'
import { createRecruiter, fetchRecruiters, type User } from '../api'

export default function RecruitersPage() {
  const [recruiters, setRecruiters] = useState<User[]>([])
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  const load = () => fetchRecruiters().then(setRecruiters).catch((e) => setError(e.message))

  useEffect(() => {
    load()
  }, [])

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await createRecruiter({ name, email, password })
      setName('')
      setEmail('')
      setPassword('')
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed')
    }
  }

  return (
    <div>
      <h2 className="text-xl font-semibold">Recruiters</h2>
      <p className="text-sm text-slate-500">Admin — create and manage recruiter accounts</p>

      <form onSubmit={onSubmit} className="mt-6 grid max-w-xl gap-3 rounded-xl border border-slate-200 bg-white p-4">
        <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} className="rounded border px-3 py-2 text-sm" required />
        <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="rounded border px-3 py-2 text-sm" required />
        <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} className="rounded border px-3 py-2 text-sm" required />
        <button type="submit" className="rounded bg-brand-600 px-4 py-2 text-sm text-white w-fit">
          Create recruiter
        </button>
      </form>

      {error && <p className="mt-4 text-red-600">{error}</p>}

      <ul className="mt-6 space-y-2">
        {recruiters.map((r) => (
          <li key={r.id} className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm">
            <span className="font-medium">{r.name}</span> — {r.email}
            {!r.is_active && <span className="ml-2 text-red-500">(disabled)</span>}
          </li>
        ))}
      </ul>
    </div>
  )
}
