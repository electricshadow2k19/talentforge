"""Simple PDF export from text content."""

import io

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def text_to_pdf_bytes(text: str, title: str = "TalentForge Document") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    y = height - inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, y, title[:80])
    y -= 0.4 * inch
    c.setFont("Helvetica", 10)
    for line in text.splitlines():
        if y < inch:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - inch
        # wrap long lines
        while len(line) > 90:
            c.drawString(inch, y, line[:90])
            line = line[90:]
            y -= 14
        c.drawString(inch, y, line[:120])
        y -= 14
    c.save()
    return buf.getvalue()
