import type { PackageResult } from './types'

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ?? ''

export async function fetchHealth(): Promise<{ status: string; ai_enabled: boolean }> {
  const res = await fetch(`${API_BASE}/api/health`)
  if (!res.ok) throw new Error('API unavailable')
  return res.json()
}

export async function generatePackage(form: FormData): Promise<PackageResult> {
  const res = await fetch(`${API_BASE}/api/generate-package`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Request failed (${res.status})`)
  }
  return res.json()
}
