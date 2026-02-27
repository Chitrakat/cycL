from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str
    REDIS_URL: str
    CORS_ORIGINS: str = ""
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Cycling Workout API"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        from_attributes=True,
    )

    def get_cors_origins(self) -> list[str]:
        """Get CORS origins as a list."""
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
