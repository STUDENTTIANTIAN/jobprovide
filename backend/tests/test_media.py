import pytest
from app.services.media_service import MediaService
from app.models.media import Media

@pytest.mark.asyncio
async def test_create_media(db_session):
    service = MediaService(db_session)
    media = await service.create_media(
        file_path="/uploads/test.jpg",
        file_type="image",
        name="测试图片",
        tags=["测试"]
    )
    assert media.type == "image"
    assert media.name == "测试图片"
    assert media.tags == ["测试"]

@pytest.mark.asyncio
async def test_get_media(db_session):
    service = MediaService(db_session)
    media = await service.create_media(
        file_path="/uploads/test.jpg",
        file_type="image"
    )
    fetched = await service.get_media(media.id)
    assert fetched is not None
    assert fetched.id == media.id

@pytest.mark.asyncio
async def test_list_media(db_session):
    service = MediaService(db_session)
    await service.create_media(file_path="/uploads/1.jpg", file_type="image", tags=["科技"])
    await service.create_media(file_path="/uploads/2.jpg", file_type="image", tags=["编程"])

    result = await service.list_media()
    assert result.total == 2

    result = await service.list_media(keyword="科技")
    assert result.total == 1