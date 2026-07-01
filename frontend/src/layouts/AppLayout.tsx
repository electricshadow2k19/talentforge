import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const nav = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/candidates', label: 'Candidates' },
  { to: '/workspace', label: 'Recruiter Workspace' },
  { to: '/submissions', label: 'Submissions' },
  { to: '/recruiters', label: 'Recruiters', admin: true },
  { to: '/settings', label: 'Settings', admin: true },
]

export function AppLayout() {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="flex w-56 flex-col border-r border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-5">
          <h1 className="text-lg font-bold text-brand-900">
            Talent<span className="text-brand-600">Forge</span>
          </h1>
          <p className="text-xs text-slate-500">Recruiter OS</p>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {nav
            .filter((item) => !item.admin || isAdmin)
            .map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `block rounded-lg px-3 py-2 text-sm font-medium ${
                    isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
        </nav>
        <div className="border-t border-slate-200 p-4 text-sm">
          <p className="font-medium text-slate-800">{user?.name}</p>
          <p className="text-xs capitalize text-slate-500">{user?.role}</p>
          <button
            type="button"
            onClick={handleLogout}
            className="mt-2 text-xs text-brand-600 hover:underline"
          >
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
