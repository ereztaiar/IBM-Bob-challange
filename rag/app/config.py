"""Application settings loaded from environment variables or a .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised configuration for the RAG micro-service.

    All values are read from environment variables.  A ``.env`` file in the
    working directory is also supported via pydantic-settings.
    """

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/vulnchecker"
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    RAG_SERVICE_URL: str = "http://rag:8001"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
