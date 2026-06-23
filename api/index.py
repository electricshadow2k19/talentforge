import sys
from pathlib import Path

# Make backend package importable on Vercel
BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.main import app  # noqa: F401 — Vercel FastAPI entrypoint
