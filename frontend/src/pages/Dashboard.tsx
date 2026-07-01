import { useEffect, useState } from 'react'
import { fetchDashboard, type DashboardStats } from '../api'

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-bold text-slate-900">{value}</p>
    </div>
  )
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDashboard()
      .then(setStats)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load dashboard'))
  }, [])

  if (error) return <div className="text-red-600">{error}</div>
  if (!stats) return <div className="text-slate-500">Loading dashboard…</div>

  return (
    <div>
      <h2 className="text-xl font-semibold text-slate-900">Dashboard</h2>
      <p className="mt-1 text-sm text-slate-500">Recruiter operating system overview</p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard label="Total Candidates" value={stats.total_candidates} />
        <StatCard label="Active Bench" value={stats.active_bench} />
        <StatCard label="Total Recruiters" value={stats.total_recruiters} />
        <StatCard label="Submissions This Month" value={stats.submissions_this_month} />
        <StatCard label="Interviews" value={stats.interview_count} />
        <StatCard label="Placements" value={stats.placement_count} />
      </div>
    </div>
  )
}
