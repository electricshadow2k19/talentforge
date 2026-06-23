from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    use_ai: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:3000"


settings = Settings()
