/** Parse plain-text resume into structured sections (no misclassified lines). */

export interface ResumeSection {
  title: string
  lines: string[]
}

export interface ParsedResume {
  name: string
  title: string
  contact: string[]
  sections: ResumeSection[]
}

const SECTION_HEADERS = [
  'PROFESSIONAL SUMMARY',
  'SUMMARY',
  'PROFILE',
  'OBJECTIVE',
  'TECHNICAL SKILLS',
  'SKILLS',
  'CORE COMPETENCIES',
  'PROFESSIONAL EXPERIENCE',
  'WORK EXPERIENCE',
  'EXPERIENCE',
  'EDUCATION',
  'CERTIFICATIONS',
  'PROJECTS',
]

function normalizeHeader(line: string): string | null {
  const t = line.trim()
  if (!t) return null
  const bare = t.replace(/:$/, '').trim()
  for (const h of SECTION_HEADERS) {
    if (new RegExp(`^${h}\\s*:?\\s*$`, 'i').test(bare)) return h
  }
  if (/^TECHNICAL\s+SKILLS?\s*:/i.test(t)) return 'TECHNICAL SKILLS'
  if (/^SKILLS?\s*:/i.test(t) && t.length < 40) return 'TECHNICAL SKILLS'
  return null
}

const CONTACT_RE = /@|linkedin|github|phone:|email:|tel:|http|www\.|^\+\d/i
const TITLE_RE =
  /engineer|developer|architect|analyst|manager|consultant|administrator|specialist|lead\b/i

/** Job/employer line: short, has date range or clear Company | Role pattern */
function isJobHeader(line: string): boolean {
  const t = line.trim()
  if (t.length > 130 || t.startsWith('-') || t.startsWith('•')) return false
  if (/\d{4}\s*[-–—]\s*(?:\d{4}|present)/i.test(t)) return true
  if (t.includes('|') && t.length < 100 && !t.endsWith('.')) {
    const parts = t.split('|').map((p) => p.trim())
    return parts.length >= 2 && parts[0].length < 50
  }
  return false
}

function isBullet(line: string): boolean {
  return /^[\-\*•]\s+/.test(line.trim())
}

function bulletText(line: string): string {
  return line.trim().replace(/^[\-\*•]\s+/, '')
}

export function parseResumeText(text: string): ParsedResume {
  const lines = text.replace(/\r\n/g, '\n').split('\n')
  const sections: ResumeSection[] = []
  let current: ResumeSection | null = null
  const headerLines: string[] = []

  for (const raw of lines) {
    const line = raw.trimEnd()
    const header = normalizeHeader(line)
    if (header) {
      current = { title: header, lines: [] }
      sections.push(current)
      continue
    }
    if (/^(TECHNICAL\s+)?SKILLS?\s*[:|]/i.test(line.trim())) {
      const skillsBody = line.trim().replace(/^(TECHNICAL\s+)?SKILLS?\s*[:|]\s*/i, '')
      if (!current || current.title !== 'TECHNICAL SKILLS') {
        current = { title: 'TECHNICAL SKILLS', lines: [] }
        sections.push(current)
      }
      if (skillsBody) current.lines.push(skillsBody)
      continue
    }
    if (current) {
      if (line.trim()) current.lines.push(line.trim())
    } else if (line.trim()) {
      headerLines.push(line.trim())
    }
  }

  let name = 'Candidate'
  let title = ''
  const contact: string[] = []
  const preSection: string[] = []

  for (let i = 0; i < headerLines.length; i++) {
    const line = headerLines[i]
    if (i === 0 && line.length < 70 && !CONTACT_RE.test(line)) {
      name = line
      continue
    }
    if (!title && line.length < 90 && TITLE_RE.test(line) && !CONTACT_RE.test(line)) {
      title = line
      continue
    }
    if (CONTACT_RE.test(line) || (contact.length > 0 && line.length < 120)) {
      contact.push(line)
      continue
    }
    preSection.push(line)
  }

  if (preSection.length && sections.length && sections[0].title.match(/SUMMARY|PROFILE|OBJECTIVE/i)) {
    sections[0].lines = [...preSection, ...sections[0].lines]
  } else if (preSection.length) {
    sections.unshift({ title: 'PROFESSIONAL SUMMARY', lines: preSection })
  }

  return { name, title, contact, sections }
}

export { isJobHeader, isBullet, bulletText, CONTACT_RE }
