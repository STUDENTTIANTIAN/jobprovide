from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.schemas.media import MediaResponse, MediaListResponse
from app.services.media_service import MediaService
import os
import uuid
import json

router = APIRouter(prefix="/api/media", tags=["media"])

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("", response_model=MediaListResponse)
async def list_media(
    keyword: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """获取素材列表"""
    service = MediaService(db)
    return await service.list_media(keyword=keyword, page=page, size=size)

@router.post("", response_model=MediaResponse)
async def upload_media(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    tags: Optional[str] = Form("[]"),
    db: AsyncSession = Depends(get_db)
):
    """上传素材"""
    # 保存文件
    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 判断类型
    file_type = "video" if file_ext in [".mp4", ".avi", ".mov"] else "image"

    # 解析tags
    try:
        tags_list = json.loads(tags)
    except:
        tags_list = []

    service = MediaService(db)
    media = await service.create_media(
        file_path=f"/uploads/{file_name}",
        file_type=file_type,
        name=name,
        tags=tags_list
    )

    return media

@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取单个素材"""
    service = MediaService(db)
    media = await service.get_media(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return media

@router.delete("/{media_id}")
async def delete_media(
    media_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """删除素材"""
    service = MediaService(db)
    success = await service.delete_media(media_id)
    if not success:
        raise HTTPException(status_code=404, detail="Media not found")
    return {"message": "Deleted"}
