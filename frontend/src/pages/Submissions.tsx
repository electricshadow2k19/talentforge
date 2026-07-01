import { useEffect, useState } from 'react'
import { fetchSubmissions, type Submission } from '../api'

export default function SubmissionsPage() {
  const [rows, setRows] = useState<Submission[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSubmissions()
      .then(setRows)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
  }, [])

  return (
    <div>
      <h2 className="text-xl font-semibold">Submissions</h2>
      <p className="text-sm text-slate-500">Track candidate submissions and status</p>
      {error && <p className="mt-4 text-red-600">{error}</p>}
      <div className="mt-4 overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="border-b bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3">Candidate</th>
              <th className="px-4 py-3">Resume</th>
              <th className="px-4 py-3">JD</th>
              <th className="px-4 py-3">Recruiter</th>
              <th className="px-4 py-3">ATS</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Date</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.id} className="border-b last:border-0">
                <td className="px-4 py-3">{s.candidate_name}</td>
                <td className="px-4 py-3">{s.resume_name}</td>
                <td className="px-4 py-3">{s.jd_title ?? '—'}</td>
                <td className="px-4 py-3">{s.recruiter_name}</td>
                <td className="px-4 py-3 font-medium">{s.ats_score}%</td>
                <td className="px-4 py-3">{s.status}</td>
                <td className="px-4 py-3">{new Date(s.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                  No submissions yet — run analysis from Recruiter Workspace
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
