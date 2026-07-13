import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "wilderfeast-hunters-guild-secret")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias
    DATABASE_URL: str = "sqlite+aiosqlite:///./wilderfeast.db"
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


settings = Settings()
