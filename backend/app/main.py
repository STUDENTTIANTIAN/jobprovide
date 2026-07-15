from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.config import get_settings
from app.api import api_router
from app.services.qdrant_service import qdrant_service
import os

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await qdrant_service.ensure_collections()
    except Exception as e:
        print(f"Qdrant init warning: {e}")
    yield
    await qdrant_service.close()


app = FastAPI(
    title="AI字幕分析平台",
    version="1.0.0",
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

uploads_dir = "/app/uploads"
os.makedirs(uploads_dir, exist_ok=True)


@app.get("/uploads/{filename}")
async def get_upload(filename: str):
    file_path = os.path.join(uploads_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/info")
async def system_info():
    return {
        "tei_url": settings.TEI_URL,
        "qdrant_url": settings.QDRANT_URL,
        "qdrant_connected": qdrant_service.client is not None,
    }
