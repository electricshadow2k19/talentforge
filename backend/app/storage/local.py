import uuid
from pathlib import Path

from app.config import settings


class StorageService:
  """Local filesystem storage with S3-compatible key paths."""

  def __init__(self) -> None:
    self.root = Path(settings.storage_local_path)
    try:
      self.root.mkdir(parents=True, exist_ok=True)
    except OSError:
      # Serverless (e.g. Vercel): fall back to /tmp
      self.root = Path("/tmp/talentforge-storage")
      self.root.mkdir(parents=True, exist_ok=True)

  def save(self, key: str, data: bytes) -> str:
    path = self.root / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return key

  def read(self, key: str) -> bytes:
    return (self.root / key).read_bytes()

  def delete(self, key: str) -> None:
    p = self.root / key
    if p.exists():
      p.unlink()

  def key_for_resume(self, candidate_id: uuid.UUID, resume_id: uuid.UUID, ext: str) -> str:
    return f"candidates/{candidate_id}/resumes/{resume_id}.{ext}"


storage = StorageService()
