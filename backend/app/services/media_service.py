from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.media import Media
from app.schemas.media import MediaCreate, MediaResponse, MediaListResponse
import os
import uuid as uuid_lib

class MediaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_media(self, file_path: str, file_type: str, name: str = None, tags: List[str] = None) -> Media:
        """创建素材记录"""
        media = Media(
            type=file_type,
            url=file_path,
            name=name or os.path.basename(file_path),
            tags=tags or [],
            keywords=[]
        )
        self.db.add(media)
        await self.db.flush()
        return media

    async def get_media(self, media_id: UUID) -> Optional[Media]:
        """获取单个素材"""
        result = await self.db.execute(select(Media).where(Media.id == media_id))
        return result.scalar_one_or_none()

    async def list_media(self, keyword: str = None, page: int = 1, size: int = 20) -> MediaListResponse:
        """获取素材列表"""
        query = select(Media)
        count_query = select(func.count(Media.id))

        if keyword:
            query = query.where(Media.tags.contains([keyword]))
            count_query = count_query.where(Media.tags.contains([keyword]))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = query.offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return MediaListResponse(items=items, total=total)

    async def update_tags(self, media_id: UUID, tags: List[str]) -> Optional[Media]:
        """更新素材标签"""
        media = await self.get_media(media_id)
        if media:
            media.tags = tags
            await self.db.flush()
        return media

    async def delete_media(self, media_id: UUID) -> bool:
        """删除素材"""
        media = await self.get_media(media_id)
        if media:
            await self.db.delete(media)
            await self.db.flush()
            return True
        return False