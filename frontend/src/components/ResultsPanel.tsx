import { useState } from 'react'
import type { PackageResult } from '../types'

const TABS = [
  { id: 'jd', label: 'JD Analysis' },
  { id: 'resume', label: 'Resume' },
  { id: 'ats', label: 'ATS Score' },
  { id: 'optimized', label: 'Optimized Resume' },
  { id: 'package', label: 'Submission' },
  { id: 'questions', label: 'Questions' },
  { id: 'emails', label: 'Emails' },
] as const

type TabId = (typeof TABS)[number]['id']

function copyText(text: string) {
  navigator.clipboard.writeText(text)
}

function ScoreRing({ score }: { score: number }) {
  const color = score >= 85 ? 'text-emerald-600' : score >= 70 ? 'text-amber-600' : 'text-red-600'
  return (
    <div className={`text-4xl font-bold ${color}`}>{score}%</div>
  )
}

export function ResultsPanel({ result }: { result: PackageResult }) {
  const [tab, setTab] = useState<TabId>('ats')
  const { jd_analysis: jd, resume_analysis: res, ats_score: ats } = result

  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-6 py-4">
        <div>
          <h2 className="text-lg font-semibold">Submission package ready</h2>
          <p className="text-sm text-slate-500">
            {result.processing_mode} mode · {result.elapsed_seconds}s
            {res.candidate_name && ` · ${res.candidate_name}`}
          </p>
        </div>
        <ScoreRing score={ats.overall} />
      </div>

      <div className="flex flex-wrap gap-1 border-b border-slate-100 px-4 pt-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-t-lg px-4 py-2 text-sm font-medium ${
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
        {tab === 'jd' && (
          <div className="space-y-4 text-sm">
            <Row label="Title" value={jd.title} />
            <Row label="Location" value={jd.location} />
            <Row label="Work mode" value={jd.work_mode} />
            <Row label="Experience" value={jd.experience_years} />
            <TagList label="Mandatory skills" items={jd.mandatory_skills} color="blue" />
            <TagList label="Nice to have" items={jd.nice_to_have_skills} color="slate" />
            <TagList label="Visa" items={jd.visa_requirements} color="amber" />
          </div>
        )}

        {tab === 'resume' && (
          <div className="space-y-4 text-sm">
            <Row label="Name" value={res.candidate_name} />
            <Row label="Email" value={res.email} />
            <Row label="Experience" value={res.experience_years} />
            <Row label="Visa" value={res.visa_status} />
            <TagList label="Skills" items={res.skills} color="blue" />
            <TagList label="Certifications" items={res.certifications} color="emerald" />
          </div>
        )}

        {tab === 'ats' && (
          <div>
            <table className="mb-6 w-full text-sm">
              <thead>
                <tr className="border-b text-left text-slate-500">
                  <th className="pb-2">Section</th>
                  <th className="pb-2">Score</th>
                  <th className="pb-2">Notes</th>
                </tr>
              </thead>
              <tbody>
                {ats.sections.map((s) => (
                  <tr key={s.section} className="border-b border-slate-100">
                    <td className="py-2 font-medium">{s.section}</td>
                    <td className="py-2">{s.score}%</td>
                    <td className="py-2 text-slate-600">{s.notes || '—'}</td>
                  </tr>
                ))}
                <tr className="font-semibold">
                  <td className="pt-3">Overall</td>
                  <td className="pt-3">{ats.overall}%</td>
                  <td />
                </tr>
              </tbody>
            </table>
            <div className="grid gap-4 md:grid-cols-2">
              <TagList label="Matched" items={ats.matched_keywords} color="emerald" />
              <TagList label="Missing" items={ats.missing_keywords} color="red" />
            </div>
          </div>
        )}

        {tab === 'optimized' && (
          <CopyBlock text={result.optimized_resume} label="Optimized resume" />
        )}

        {tab === 'package' && (
          <div className="space-y-4 text-sm">
            <div>
              <h3 className="mb-1 font-semibold">Summary</h3>
              <p className="text-slate-700">{result.submission_package.candidate_summary}</p>
            </div>
            <TagList label="Strengths" items={result.submission_package.strengths} color="emerald" />
            <TagList label="Risks" items={result.submission_package.risks} color="amber" />
            <p className="text-slate-600">{result.submission_package.fit_statement}</p>
          </div>
        )}

        {tab === 'questions' && (
          <div className="space-y-6 text-sm">
            <QuestionList title="Technical" items={result.interview_questions.technical} />
            <QuestionList title="Scenario" items={result.interview_questions.scenario} />
            <QuestionList title="Client-specific" items={result.interview_questions.client_specific} />
            <QuestionList title="Recruiter screening" items={result.interview_questions.recruiter_screening} />
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
  if (!items.length) return null
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

function QuestionList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null
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
