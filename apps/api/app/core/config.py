import os
from typing import Literal
from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "RepoLens API"
    VERSION: str = "1.0.0"
    ENV: Literal["development", "testing", "production"] = "development"

    # PostgreSQL Configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "repolens"
    DATABASE_URL: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, values) -> str:
        if isinstance(v, str) and v:
            return v
        
        # Access properties from the validation input object
        data = values.data
        user = data.get("POSTGRES_USER")
        password = data.get("POSTGRES_PASSWORD")
        host = data.get("POSTGRES_HOST")
        port = data.get("POSTGRES_PORT")
        db = data.get("POSTGRES_DB")
        
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Qdrant Configuration
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str | None = None

    # JWT Authentication settings
    JWT_SECRET_KEY: str = "supersecretkeyrepolensforlocaldevelopmentjwttokenvalidation"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # GitHub OAuth Settings (scaffolded)
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None

    # CORS configuration
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


settings = Settings()
