from pydantic_settings import BaseSettings, SettingsConfigDict
import os


def _default_database_url() -> str:
    # Vercel serverless filesystem is read-only except /tmp
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
        return "sqlite:////tmp/talentforge.db"
    return "sqlite:///./talentforge.db"


def _default_storage_path() -> str:
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
        return "/tmp/talentforge-storage"
    return "./storage"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # AI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    use_ai: bool = True

    # App
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    app_name: str = "TalentForge"
    environment: str = "development"

    # Database — SQLite default for local dev without Docker/Postgres
    database_url: str = _default_database_url()

    # Auth — dev JWT (use Clerk in production when keys are set)
    jwt_secret: str = "change-me-in-production-talentforge-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    clerk_jwks_url: str = ""
    clerk_issuer: str = ""

    # Storage — local path or S3
    storage_backend: str = "local"  # local | s3
    storage_local_path: str = _default_storage_path()
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""


settings = Settings()


def get_database_url() -> str:
    """Normalize DATABASE_URL for SQLAlchemy (Render/Heroku use postgres://)."""
    url = settings.database_url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url
