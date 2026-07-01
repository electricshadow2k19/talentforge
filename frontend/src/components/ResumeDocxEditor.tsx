import { useEffect, useRef, useState } from 'react'
import { renderAsync } from 'docx-preview'
import { resumeTextToDocxBlob } from '../utils/resumeToDocx'
import './ResumeDocxEditor.css'

type Props = {
  text: string
  fileName: string
  label: string
  hint?: string
}

export function ResumeDocxEditor({ text, fileName, label, hint }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [documentFile, setDocumentFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewerHeight, setViewerHeight] = useState(640)

  useEffect(() => {
    const updateHeight = () => setViewerHeight(Math.max(520, window.innerHeight - 280))
    updateHeight()
    window.addEventListener('resize', updateHeight)
    return () => window.removeEventListener('resize', updateHeight)
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    resumeTextToDocxBlob(text, fileName)
      .then((file) => {
        if (!cancelled) {
          setDocumentFile(file)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to build document')
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [text, fileName])

  useEffect(() => {
    const el = containerRef.current
    if (!el || !documentFile) return

    el.innerHTML = ''
    let cancelled = false

    renderAsync(documentFile, el, undefined, {
      className: 'docx-preview-root',
      inWrapper: true,
      ignoreWidth: false,
      ignoreHeight: false,
      breakPages: true,
      renderHeaders: false,
      renderFooters: false,
      useBase64URL: true,
    })
      .then(() => {
        if (cancelled || !containerRef.current) return
        const wrapper = containerRef.current.querySelector('.docx-wrapper') as HTMLElement | null
        if (!wrapper) return
        const pad = 16
        const avail = containerRef.current.clientWidth - pad * 2
        const docW = wrapper.offsetWidth || wrapper.scrollWidth
        if (docW > avail && docW > 0) {
          const scale = Math.min(1, avail / docW)
          wrapper.style.transform = `scale(${scale})`
          wrapper.style.transformOrigin = 'top center'
          wrapper.style.marginBottom = `${-(docW * (1 - scale)) / 2}px`
        }
      })
      .catch(() => {
        if (!cancelled) setError('Could not render document preview.')
      })

    return () => {
      cancelled = true
    }
  }, [documentFile, viewerHeight])

  const handleDownload = () => {
    if (!documentFile) return
    const url = URL.createObjectURL(documentFile)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div
        className="flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-600"
        style={{ height: viewerHeight }}
      >
        Building formatted resume…
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-800">{label}</h3>
          {hint && <p className="mt-0.5 text-xs text-slate-500">{hint}</p>}
        </div>
        <button
          type="button"
          onClick={handleDownload}
          className="rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700"
        >
          Download DOCX
        </button>
      </div>

      <div className="resume-docx-shell rounded-xl border border-slate-300 bg-slate-200" style={{ height: viewerHeight }}>
        <div ref={containerRef} className="resume-docx-preview" />
      </div>
      <p className="text-xs text-slate-500">
        Preview matches the downloaded Word file. Open in Microsoft Word to edit formatting further.
      </p>
    </div>
  )
}
