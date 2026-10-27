"""Application settings loaded from environment variables or a .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised configuration for the backend service.

    All values are read from environment variables.  A ``.env`` file in the
    working directory is also supported via pydantic-settings.
    """

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/vulnchecker"
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "changeme"
    JWT_SECRET: str = "change-me-in-production"
    RAG_SERVICE_URL: str = "http://rag:8001"
    FRONTEND_USER_URL: str = "http://localhost:5173"
    FRONTEND_ADMIN_URL: str = "http://localhost:5174"
    JWT_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
