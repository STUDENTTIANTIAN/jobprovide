from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.api import api_router
from app.services.qdrant_service import qdrant_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化Qdrant集合
    try:
        await qdrant_service.ensure_collections()
        print("Qdrant collections initialized")
    except Exception as e:
        print(f"Qdrant initialization warning: {e}")
    yield
    # 关闭时清理连接
    await qdrant_service.close()


app = FastAPI(
    title="AI字幕分析平台",
    version="1.0.0",
    description="基于 TEI + Qdrant 的字幕分析与素材匹配平台",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/info")
async def system_info():
    """系统信息"""
    return {
        "tei_url": settings.TEI_URL,
        "qdrant_url": settings.QDRANT_URL,
        "qdrant_connected": qdrant_service.client is not None,
    }
