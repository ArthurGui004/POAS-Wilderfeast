import os
import secrets
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    ALGORITHM: str = "HS256"
    CLOUDINARY_URL: SecretStr | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://wilderfeast:admin@127.0.0.1:5432/wilderfeast")
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("DATABASE_URL")
    @classmethod
    def usar_driver_asyncpg(cls, url: str) -> str:
        protocolo, separador, restante = url.partition("://")
        if protocolo in {"postgres", "postgresql"}:
            return f"postgresql+asyncpg{separador}{restante}"
        return url


settings = Settings()
