from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/subtitle"
    REDIS_URL: str = "redis://localhost:6379/0"
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024

    # HuggingFace TEI (Text Embeddings Inference)
    # 参考: E:\shangagent\data_agent 项目
    TEI_URL: str = "http://localhost:8081"  # bge-large-zh-v1.5

    # Qdrant Vector DB
    QDRANT_URL: str = "http://localhost:6333"

    # 语音识别（可选）
    SPEECH_API_KEY: str = ""
    SPEECH_API_URL: str = ""

    # 匹配权重
    KEYWORD_WEIGHT: float = 0.4
    SEMANTIC_WEIGHT: float = 0.6

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
