import {
  AlignmentType,
  BorderStyle,
  Document,
  Packer,
  Paragraph,
  TextRun,
} from 'docx'
import {
  bulletText,
  isBullet,
  isJobHeader,
  parseResumeText,
  type ResumeSection,
} from './resumeParser'

const BRAND = '1F4E79'
const ACCENT = '2E75B6'
const BODY_SIZE = 22 // 11pt half-points
const NAME_SIZE = 32 // 16pt

function sectionHeading(title: string): Paragraph {
  const label = title.replace(/:$/, '').toUpperCase()
  return new Paragraph({
    spacing: { before: 280, after: 120 },
    border: {
      bottom: { color: ACCENT, size: 6, style: BorderStyle.SINGLE, space: 2 },
    },
    children: [
      new TextRun({ text: label, bold: true, size: 24, color: BRAND, font: 'Calibri' }),
    ],
  })
}

function bodyParagraph(text: string, opts?: { bold?: boolean; italic?: boolean; spacingBefore?: number }): Paragraph {
  return new Paragraph({
    spacing: { before: opts?.spacingBefore ?? 0, after: 80 },
    alignment: AlignmentType.LEFT,
    children: [
      new TextRun({
        text,
        size: BODY_SIZE,
        font: 'Calibri',
        bold: opts?.bold,
        italics: opts?.italic,
      }),
    ],
  })
}

function bulletParagraph(text: string): Paragraph {
  return new Paragraph({
    bullet: { level: 0 },
    spacing: { after: 60 },
    alignment: AlignmentType.LEFT,
    children: [new TextRun({ text, size: BODY_SIZE, font: 'Calibri' })],
  })
}

function jobHeaderParagraph(line: string): Paragraph {
  return new Paragraph({
    spacing: { before: 200, after: 60 },
    alignment: AlignmentType.LEFT,
    children: [
      new TextRun({ text: line, bold: true, size: BODY_SIZE, color: BRAND, font: 'Calibri' }),
    ],
  })
}

function skillsParagraph(text: string): Paragraph {
  const skills = text.split(/\||,/).map((s) => s.trim()).filter(Boolean)
  const formatted = skills.map((s) => `• ${s}`).join('    ')
  return bodyParagraph(formatted || text)
}

function sectionContent(section: ResumeSection): (Paragraph)[] {
  const out: Paragraph[] = []
  const isSkills = /SKILLS|COMPETENCIES/i.test(section.title)

  if (isSkills && section.lines.length === 1 && section.lines[0].includes('|')) {
    out.push(skillsParagraph(section.lines[0]))
    return out
  }

  for (const line of section.lines) {
    if (isBullet(line)) {
      out.push(bulletParagraph(bulletText(line)))
    } else if (isJobHeader(line)) {
      out.push(jobHeaderParagraph(line))
    } else if (isSkills && line.includes('|')) {
      out.push(skillsParagraph(line))
    } else {
      out.push(bodyParagraph(line))
    }
  }
  return out
}

export async function resumeTextToDocxBlob(text: string, fileName = 'resume.docx'): Promise<File> {
  const parsed = parseResumeText(text)
  const children: Paragraph[] = []

  // Header block — centered, clean
  children.push(
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 60 },
      children: [
        new TextRun({ text: parsed.name, bold: true, size: NAME_SIZE, color: BRAND, font: 'Calibri' }),
      ],
    })
  )

  if (parsed.title) {
    children.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
        children: [
          new TextRun({ text: parsed.title, italics: true, size: 24, color: '505050', font: 'Calibri' }),
        ],
      })
    )
  }

  if (parsed.contact.length) {
    children.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [
          new TextRun({
            text: parsed.contact.join('  |  '),
            size: 20,
            color: '505050',
            font: 'Calibri',
          }),
        ],
      })
    )
  } else {
    children.push(new Paragraph({ spacing: { after: 120 }, children: [new TextRun('')] }))
  }

  for (const section of parsed.sections) {
    children.push(sectionHeading(section.title))
    children.push(...sectionContent(section))
  }

  const doc = new Document({
    sections: [
      {
        properties: {
          page: {
            margin: { top: 720, right: 720, bottom: 720, left: 720 },
          },
        },
        children,
      },
    ],
  })

  const blob = await Packer.toBlob(doc)
  return new File([blob], fileName, {
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  })
}
