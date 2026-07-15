import asyncio
from app.database import async_session
from app.models.media import Media
from app.services.media_service import MediaService

DEMO_MEDIA = [
    {"name": "Python代码", "type": "image", "tags": ["Python", "编程", "代码"]},
    {"name": "编程教学", "type": "image", "tags": ["编程", "教学", "学习"]},
    {"name": "代码编辑器", "type": "image", "tags": ["代码", "编辑器", "开发"]},
    {"name": "终端界面", "type": "image", "tags": ["终端", "命令行", "开发"]},
    {"name": "数据分析", "type": "image", "tags": ["数据", "分析", "图表"]},
    {"name": "人工智能", "type": "image", "tags": ["AI", "人工智能", "机器学习"]},
    {"name": "网络技术", "type": "image", "tags": ["网络", "互联网", "技术"]},
    {"name": "数据库", "type": "image", "tags": ["数据库", "SQL", "存储"]},
    {"name": "云计算", "type": "image", "tags": ["云", "服务器", "部署"]},
    {"name": "移动开发", "type": "image", "tags": ["移动", "APP", "开发"]},
]

async def seed():
    async with async_session() as db:
        service = MediaService(db)
        for item in DEMO_MEDIA:
            await service.create_media(
                file_path=f"/uploads/demo_{item['name']}.jpg",
                file_type=item["type"],
                name=item["name"],
                tags=item["tags"]
            )
        await db.commit()
    print(f"Seeded {len(DEMO_MEDIA)} demo media items")

if __name__ == "__main__":
    asyncio.run(seed())