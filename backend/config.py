"""Application configuration using pydantic-settings."""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

# Get the directory where this config file is located
BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    The BETTER_AUTH_SECRET must be the same value used in the
    Better Auth frontend configuration to verify JWT tokens.
    """

    # Better Auth Configuration
    better_auth_url: str = Field(
        default="https://frontend-delta-two-31.vercel.app",
        alias="BETTER_AUTH_URL",
        description="URL of the Better Auth frontend for session verification"
    )

    # Legacy - kept for compatibility
    jwt_secret: str = Field(
        default="not-used",
        alias="BETTER_AUTH_SECRET",
        description="Legacy secret (not used with session verification)"
    )

    # Database Configuration
    database_url: Optional[str] = Field(
        default=None,
        alias="DATABASE_URL",
        description="PostgreSQL connection string (asyncpg format)"
    )

    # Server Configuration
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(
        default=None,
        alias="OPENAI_API_KEY",
        description="API key for OpenAI Agents SDK"
    )

    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["https://frontend-delta-two-31.vercel.app", "http://localhost:3000"],
        description="Allowed origins for CORS"
    )

    model_config = {
        "env_file": BASE_DIR / ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

    def validate_secret(self) -> None:
        """Validate Better Auth URL is configured."""
        if not self.better_auth_url:
            raise ValueError(
                "BETTER_AUTH_URL is not configured. "
                "Set it in environment variables or .env file."
            )


# Create settings instance - will fail fast if BETTER_AUTH_SECRET not set
settings = Settings()
