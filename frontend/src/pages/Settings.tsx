export default function SettingsPage() {
  return (
    <div>
      <h2 className="text-xl font-semibold">Settings</h2>
      <p className="text-sm text-slate-500">System configuration (admin)</p>
      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
        <p>MVP settings are managed via environment variables:</p>
        <ul className="mt-3 list-disc space-y-1 pl-5">
          <li><code>OPENAI_API_KEY</code> — enable AI mode</li>
          <li><code>DATABASE_URL</code> — PostgreSQL connection</li>
          <li><code>JWT_SECRET</code> — auth signing key</li>
          <li><code>STORAGE_BACKEND</code> — local or S3</li>
        </ul>
        <p className="mt-4 text-amber-700">Email sending is disabled in MVP — templates are generated only.</p>
      </div>
    </div>
  )
}
