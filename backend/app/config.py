from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/subtitle"
    REDIS_URL: str = "redis://localhost:6379/0"
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_API_URL: str = ""
    SPEECH_API_KEY: str = ""
    SPEECH_API_URL: str = ""
    KEYWORD_WEIGHT: float = 0.4
    SEMANTIC_WEIGHT: float = 0.6

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
