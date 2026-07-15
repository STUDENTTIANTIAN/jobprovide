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
    # 提供商: iflytek / baidu / tencent / generic
    SPEECH_PROVIDER: str = "generic"
    SPEECH_API_KEY: str = ""
    SPEECH_API_URL: str = ""

    # 讯飞语音识别
    IFLYTEK_APP_ID: str = ""
    IFLYTEK_API_KEY: str = ""
    IFLYTEK_API_SECRET: str = ""

    # 百度语音识别
    BAIDU_API_KEY: str = ""
    BAIDU_API_SECRET: str = ""

    # 腾讯云语音识别
    TENCENT_SECRET_ID: str = ""
    TENCENT_SECRET_KEY: str = ""

    # 匹配权重
    KEYWORD_WEIGHT: float = 0.4
    SEMANTIC_WEIGHT: float = 0.6

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
