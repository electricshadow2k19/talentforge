import { lazy, Suspense, useState } from 'react'
import type { PackageResult, RatedQuestion } from '../types'

const ResumeDocxEditor = lazy(() =>
  import('./ResumeDocxEditor').then((m) => ({ default: m.ResumeDocxEditor }))
)

const TABS = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'jd', label: 'JD Analysis' },
  { id: 'resume', label: 'Original Resume' },
  { id: 'ats', label: 'ATS Score' },
  { id: 'gaps', label: 'Gap Analysis' },
  { id: 'temporal', label: 'Temporal Review' },
  { id: 'optimized', label: 'Optimized Resume' },
  { id: 'package', label: 'Submission' },
  { id: 'questions', label: 'Questions' },
  { id: 'documents', label: 'Documents' },
  { id: 'emails', label: 'Emails' },
] as const

type TabId = (typeof TABS)[number]['id']

function copyText(text: string) {
  navigator.clipboard.writeText(text)
}

function downloadText(text: string, filename: string) {
  const blob = new Blob([text], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function downloadDocxB64(b64: string, filename: string) {
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0))
  const blob = new Blob([bytes], {
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function downloadPdfB64(b64: string, filename: string) {
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0))
  const blob = new Blob([bytes], { type: 'application/pdf' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function docxFileName(name: string | null | undefined, suffix: string) {
  const base = (name || 'candidate').replace(/[^\w\s-]/g, '').trim().replace(/\s+/g, '_')
  return `${base}_${suffix}.docx`
}

function EditorFallback() {
  return (
    <div className="flex h-[min(70vh,720px)] items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-600">
      Loading Word editor…
    </div>
  )
}

function ScoreRing({ score }: { score: number }) {
  const color = score >= 85 ? 'text-emerald-600' : score >= 70 ? 'text-amber-600' : 'text-red-600'
  return <div className={`text-4xl font-bold ${color}`}>{score}%</div>
}

export function ResultsPanel({ result }: { result: PackageResult }) {
  const [tab, setTab] = useState<TabId>('dashboard')
  const { jd_analysis: jd, resume_analysis: res, ats_score: ats, ats_score_before } = result
  const dash = result.dashboard
  const gap = result.gap_analysis
  const sections = result.generated_sections
  const improved = ats.overall > ats_score_before
  const baseName = docxFileName(res.candidate_name, '').replace(/\.docx$/, '')

  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-6 py-4">
        <div>
          <h2 className="text-lg font-semibold">Submission package ready</h2>
          <p className="text-sm text-slate-500">
            {result.processing_mode} mode · {result.elapsed_seconds}s
            {res.candidate_name && ` · ${res.candidate_name}`}
          </p>
          {ats_score_before > 0 && (
            <p className="mt-1 text-sm font-medium text-slate-600">
              ATS: {ats_score_before}% → {ats.overall}%
              {improved && (
                <span className="ml-2 text-emerald-600">(+{ats.overall - ats_score_before}%)</span>
              )}
              {dash && (
                <span className="ml-2 text-slate-500">· {dash.keyword_coverage_pct}% keyword coverage</span>
              )}
            </p>
          )}
        </div>
        <div className="text-right">
          <ScoreRing score={ats.overall} />
          {ats_score_before > 0 && ats_score_before !== ats.overall && (
            <p className="mt-1 text-xs text-slate-500">was {ats_score_before}%</p>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-1 border-b border-slate-100 px-4 pt-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-t-lg px-3 py-2 text-sm font-medium ${
              tab === t.id
                ? 'border border-b-0 border-slate-200 bg-white text-brand-700'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="p-6">
        {tab === 'dashboard' && dash && (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="ATS Score" value={`${dash.ats_score}%`} sub={`was ${dash.ats_score_before}%`} />
              <StatCard label="Keyword Coverage" value={`${dash.keyword_coverage_pct}%`} />
              <StatCard label="Top Skills" value={String(dash.top_skills.length)} />
              <StatCard label="Gaps" value={String(dash.missing_skills.length)} />
            </div>
            <TagList label="Top matching skills" items={dash.top_skills} color="emerald" />
            <TagList label="Missing skills" items={dash.missing_skills} color="red" />
            <div>
              <h3 className="mb-2 text-sm font-semibold text-slate-700">Optimization suggestions</h3>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
                {dash.optimization_suggestions.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="mb-2 text-sm font-semibold text-slate-700">Scoring model</h3>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {Object.entries(dash.scoring_weights).map(([k, v]) => (
                  <div key={k} className="rounded-lg bg-slate-50 px-3 py-2 text-sm">
                    <span className="font-medium">{k}</span>
                    <span className="text-slate-500"> — {Math.round(v * 100)}%</span>
                  </div>
                ))}
              </div>
              <p className="mt-2 text-xs text-slate-500">
                Visa, citizenship, nationality, gender, race, and age are excluded from ATS scoring.
              </p>
            </div>
          </div>
        )}

        {tab === 'jd' && (
          <div className="space-y-4 text-sm">
            <Row label="Title" value={jd.title} />
            <Row label="Location" value={jd.location} />
            <Row label="Work mode" value={jd.work_mode} />
            <Row label="Experience" value={jd.experience_years} />
            <TagList label="Required skills" items={jd.required_skills || jd.mandatory_skills} color="blue" />
            <TagList label="Preferred skills" items={jd.preferred_skills || jd.nice_to_have_skills} color="slate" />
            <TagList label="Programming languages" items={jd.programming_languages} color="blue" />
            <TagList label="Cloud platforms" items={jd.cloud_platforms} color="emerald" />
            <TagList label="DevOps tools" items={jd.devops_tools} color="emerald" />
            <TagList label="Security tools" items={jd.security_tools} color="amber" />
            <TagList label="Industry keywords" items={jd.industry_keywords} color="slate" />
            <TagList label="Soft skills" items={jd.soft_skills} color="slate" />
            {jd.responsibilities?.length > 0 && (
              <div>
                <h3 className="mb-2 font-semibold text-slate-700">Responsibilities</h3>
                <ul className="list-disc space-y-1 pl-5 text-slate-600">
                  {jd.responsibilities.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
            <CopyBlock
              text={JSON.stringify(
                {
                  title: jd.title,
                  required_skills: jd.required_skills || jd.mandatory_skills,
                  preferred_skills: jd.preferred_skills || jd.nice_to_have_skills,
                },
                null,
                2
              )}
              label="Structured JD JSON"
            />
          </div>
        )}

        {tab === 'resume' && (
          <div className="space-y-4">
            <div className="grid gap-4 text-sm md:grid-cols-2 lg:grid-cols-4">
              <Row label="Name" value={res.candidate_name} />
              <Row label="Email" value={res.email} />
              <Row label="Experience" value={res.experience_years} />
              <Row label="Location" value={res.location} />
            </div>
            <TagList label="Skills" items={res.skills} color="blue" />
            <TagList label="Tools" items={res.tools} color="emerald" />
            <TagList label="Technologies" items={res.technologies} color="slate" />
            <Suspense fallback={<EditorFallback />}>
              <ResumeDocxEditor
                text={result.original_resume || res.summary || ''}
                fileName={docxFileName(res.candidate_name, 'resume')}
                label="Current resume"
                hint="Formatted Word preview — download DOCX to edit in Microsoft Word."
              />
            </Suspense>
          </div>
        )}

        {tab === 'ats' && (
          <div>
            <p className="mb-4 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">
              Weighted ATS score on the <strong>optimized resume</strong>. Original:{' '}
              <strong>{ats_score_before}%</strong> → Optimized: <strong>{ats.overall}%</strong>.
            </p>
            <table className="mb-6 w-full text-sm">
              <thead>
                <tr className="border-b text-left text-slate-500">
                  <th className="pb-2">Section</th>
                  <th className="pb-2">Weight</th>
                  <th className="pb-2">Score</th>
                  <th className="pb-2">Notes</th>
                </tr>
              </thead>
              <tbody>
                {ats.sections.map((s) => (
                  <tr key={s.section} className="border-b border-slate-100">
                    <td className="py-2 font-medium">{s.section}</td>
                    <td className="py-2 text-slate-500">{s.weight_pct ? `${s.weight_pct}%` : '—'}</td>
                    <td className="py-2">{s.score}%</td>
                    <td className="py-2 text-slate-600">{s.notes || '—'}</td>
                  </tr>
                ))}
                <tr className="font-semibold">
                  <td className="pt-3">Overall</td>
                  <td className="pt-3">100%</td>
                  <td className="pt-3">{ats.overall}%</td>
                  <td className="pt-3">{ats.keyword_coverage_pct}% keyword coverage</td>
                </tr>
              </tbody>
            </table>
            <div className="grid gap-4 md:grid-cols-2">
              <TagList label="Matched" items={ats.matched_keywords} color="emerald" />
              <TagList label="Missing" items={ats.missing_keywords} color="red" />
            </div>
          </div>
        )}

        {tab === 'gaps' && gap && (
          <div className="space-y-4">
            <TagList label="Missing skills" items={gap.missing_skills} color="red" />
            <TagList label="Missing keywords" items={gap.missing_keywords} color="red" />
            <TagList label="Missing technologies" items={gap.missing_technologies} color="amber" />
            <TagList label="Missing certifications" items={gap.missing_certifications} color="amber" />
            {gap.missing_responsibilities.length > 0 && (
              <div>
                <h3 className="mb-2 text-sm font-semibold text-slate-700">Missing responsibilities alignment</h3>
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
                  {gap.missing_responsibilities.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
            <div>
              <h3 className="mb-2 text-sm font-semibold text-slate-700">Optimization suggestions</h3>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
                {gap.optimization_suggestions.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {tab === 'temporal' && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600">
              Temporal due diligence audit — verifies skill/version placement against technology release dates.
            </p>
            {(result.temporal_audit ?? []).length === 0 ? (
              <p className="text-sm text-slate-500">No versioned requirements detected in this JD.</p>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-slate-200">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-600">
                    <tr>
                      <th className="px-4 py-3">Requirement</th>
                      <th className="px-4 py-3">Release</th>
                      <th className="px-4 py-3">Target Role</th>
                      <th className="px-4 py-3">Role Dates</th>
                      <th className="px-4 py-3">Allowed</th>
                      <th className="px-4 py-3">Action / Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(result.temporal_audit ?? []).map((row) => (
                      <tr
                        key={row.requirement + (row.placed_in_role ?? '')}
                        className={row.allowed ? 'bg-white' : 'bg-amber-50'}
                      >
                        <td className="px-4 py-3 font-medium text-slate-800">{row.requirement}</td>
                        <td className="px-4 py-3 text-slate-600">{row.release_date ?? '—'}</td>
                        <td className="px-4 py-3 text-slate-600">{row.placed_in_role ?? '—'}</td>
                        <td className="px-4 py-3 text-slate-600">{row.role_dates ?? '—'}</td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
                              row.allowed
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-amber-200 text-amber-900'
                            }`}
                          >
                            {row.allowed ? 'Yes' : 'No'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          <span className="font-medium">{row.action_taken}</span>
                          {row.reason && <span className="block text-xs text-slate-500">{row.reason}</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {tab === 'optimized' && (
          <Suspense fallback={<EditorFallback />}>
            <ResumeDocxEditor
              text={result.optimized_resume}
              fileName={docxFileName(res.candidate_name, 'optimized_resume')}
              label="Optimized resume"
              hint="JD-aligned resume preview. Download DOCX for submission or further edits in Word."
            />
          </Suspense>
        )}

        {tab === 'package' && sections && (
          <div className="space-y-4 text-sm">
            <div>
              <h3 className="mb-1 font-semibold">Professional summary</h3>
              <p className="text-slate-700">{sections.professional_summary}</p>
            </div>
            <div>
              <h3 className="mb-1 font-semibold">Client submission summary</h3>
              <p className="text-slate-700">{sections.client_submission_summary}</p>
            </div>
            <TagList label="Key strengths" items={sections.key_strengths} color="emerald" />
            <TagList label="Top matching skills" items={sections.top_matching_skills} color="blue" />
            <div>
              <h3 className="mb-2 font-semibold">Technical highlights</h3>
              <ul className="list-disc space-y-1 pl-5 text-slate-600">
                {sections.technical_highlights.map((h) => (
                  <li key={h}>{h}</li>
                ))}
              </ul>
            </div>
            <TagList label="Risks" items={result.submission_package.risks} color="amber" />
            <p className="text-slate-600">{result.submission_package.fit_statement}</p>
          </div>
        )}

        {tab === 'questions' && (
          <div className="space-y-6 text-sm">
            <RatedQuestionList title="Technical" items={result.interview_questions.technical} />
            <RatedQuestionList title="Scenario" items={result.interview_questions.scenario} />
            <RatedQuestionList title="Behavioral" items={result.interview_questions.behavioral} />
            <RatedQuestionList title="Client-specific" items={result.interview_questions.client_specific} />
            <QuestionList title="Recruiter screening" items={result.interview_questions.recruiter_screening} />
          </div>
        )}

        {tab === 'documents' && (
          <div className="grid gap-3 sm:grid-cols-2">
            {result.documents?.optimized_resume_docx_b64 && (
              <DownloadCard
                title="Optimized Resume DOCX"
                description="Word document ready for submission"
                onClick={() =>
                  downloadDocxB64(
                    result.documents.optimized_resume_docx_b64!,
                    `${baseName}_optimized.docx`
                  )
                }
              />
            )}
            {result.documents?.optimized_resume_pdf_b64 && (
              <DownloadCard
                title="Optimized Resume PDF"
                description="PDF version of optimized resume"
                onClick={() =>
                  downloadPdfB64(result.documents.optimized_resume_pdf_b64!, `${baseName}_optimized.pdf`)
                }
              />
            )}
            {result.documents?.candidate_summary_text && (
              <DownloadCard
                title="Candidate Summary"
                description="Text summary for internal use"
                onClick={() => downloadText(result.documents.candidate_summary_text!, `${baseName}_summary.txt`)}
              />
            )}
            {result.documents?.interview_sheet_text && (
              <DownloadCard
                title="Interview Question Sheet"
                description="Technical, scenario, behavioral questions"
                onClick={() => downloadText(result.documents.interview_sheet_text!, `${baseName}_interview_sheet.txt`)}
              />
            )}
            {result.documents?.submission_package_pdf_b64 && (
              <DownloadCard
                title="Submission Package PDF"
                description="Full submission package as PDF"
                onClick={() =>
                  downloadPdfB64(result.documents.submission_package_pdf_b64!, `${baseName}_submission.pdf`)
                }
              />
            )}
            {result.documents?.interview_sheet_pdf_b64 && (
              <DownloadCard
                title="Interview Questions PDF"
                description="Interview sheet as PDF"
                onClick={() =>
                  downloadPdfB64(result.documents.interview_sheet_pdf_b64!, `${baseName}_interview.pdf`)
                }
              />
            )}
            {result.documents?.submission_package_text && (
              <DownloadCard
                title="Submission Package (TXT)"
                description="Full submission text bundle"
                onClick={() => downloadText(result.documents.submission_package_text!, `${baseName}_submission.txt`)}
              />
            )}
          </div>
        )}

        {tab === 'emails' && (
          <div className="space-y-6">
            <CopyBlock text={result.email_drafts.vendor_email} label="Vendor email" />
            <CopyBlock text={result.email_drafts.candidate_email} label="Candidate email" />
            <CopyBlock text={result.email_drafts.manager_email} label="Manager / internal" />
          </div>
        )}
      </div>
    </section>
  )
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-800">{value}</p>
      {sub && <p className="text-xs text-slate-500">{sub}</p>}
    </div>
  )
}

function DownloadCard({
  title,
  description,
  onClick,
}: {
  title: string
  description: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-xl border border-slate-200 bg-white p-4 text-left hover:border-brand-300 hover:bg-brand-50"
    >
      <p className="font-semibold text-slate-800">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{description}</p>
      <p className="mt-2 text-xs font-medium text-brand-600">Download →</p>
    </button>
  )
}

function Row({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null
  return (
    <p>
      <span className="font-medium text-slate-700">{label}: </span>
      <span className="text-slate-600">{value}</span>
    </p>
  )
}

function TagList({
  label,
  items,
  color,
}: {
  label: string
  items: string[]
  color: 'blue' | 'slate' | 'emerald' | 'amber' | 'red'
}) {
  if (!items?.length) return null
  const colors = {
    blue: 'bg-blue-100 text-blue-800',
    slate: 'bg-slate-100 text-slate-700',
    emerald: 'bg-emerald-100 text-emerald-800',
    amber: 'bg-amber-100 text-amber-900',
    red: 'bg-red-100 text-red-800',
  }
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-slate-700">{label}</h3>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span key={item} className={`rounded-full px-3 py-1 text-xs font-medium ${colors[color]}`}>
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}

function RatedQuestionList({ title, items }: { title: string; items: RatedQuestion[] }) {
  if (!items?.length) return null
  const diffColor: Record<string, string> = {
    easy: 'bg-emerald-100 text-emerald-800',
    medium: 'bg-amber-100 text-amber-900',
    hard: 'bg-red-100 text-red-800',
  }
  return (
    <div>
      <h3 className="mb-2 font-semibold text-slate-800">{title}</h3>
      <ol className="list-decimal space-y-2 pl-5 text-slate-700">
        {items.map((q) => (
          <li key={q.question}>
            <span className={`mr-2 rounded px-1.5 py-0.5 text-xs font-medium ${diffColor[q.difficulty] || diffColor.medium}`}>
              {q.difficulty}
            </span>
            {q.question}
          </li>
        ))}
      </ol>
    </div>
  )
}

function QuestionList({ title, items }: { title: string; items: string[] }) {
  if (!items?.length) return null
  return (
    <div>
      <h3 className="mb-2 font-semibold text-slate-800">{title}</h3>
      <ol className="list-decimal space-y-1 pl-5 text-slate-700">
        {items.map((q) => (
          <li key={q}>{q}</li>
        ))}
      </ol>
    </div>
  )
}

function CopyBlock({ text, label }: { text: string; label: string }) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold">{label}</h3>
        <button
          type="button"
          onClick={() => copyText(text)}
          className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-medium hover:bg-slate-200"
        >
          Copy
        </button>
      </div>
      <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-900 p-4 text-xs text-slate-100">
        {text}
      </pre>
    </div>
  )
}
