import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AdminRoute, ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import { AppLayout } from './layouts/AppLayout'
import CandidateDetailPage from './pages/CandidateDetail'
import CandidatesPage from './pages/Candidates'
import DashboardPage from './pages/Dashboard'
import LoginPage from './pages/Login'
import RecruitersPage from './pages/Recruiters'
import SettingsPage from './pages/Settings'
import SubmissionsPage from './pages/Submissions'
import WorkspacePage from './pages/Workspace'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="candidates" element={<CandidatesPage />} />
            <Route path="candidates/:id" element={<CandidateDetailPage />} />
            <Route path="workspace" element={<WorkspacePage />} />
            <Route path="submissions" element={<SubmissionsPage />} />
            <Route
              path="recruiters"
              element={
                <AdminRoute>
                  <RecruitersPage />
                </AdminRoute>
              }
            />
            <Route
              path="settings"
              element={
                <AdminRoute>
                  <SettingsPage />
                </AdminRoute>
              }
            />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
