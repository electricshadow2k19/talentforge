from io import BytesIO

from docx import Document
from pypdf import PdfReader


def extract_text_from_bytes(data: bytes, filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        return _pdf_text(data)
    if name.endswith(".docx"):
        return _docx_text(data)
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="replace")
    # Best effort
    try:
        return data.decode("utf-8", errors="replace")
    except Exception:
        return _pdf_text(data)


def _pdf_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def _docx_text(data: bytes) -> str:
    doc = Document(BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()
