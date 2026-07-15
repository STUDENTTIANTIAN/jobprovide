# AI 字幕分析与素材匹配平台 - 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 开发一个轻量化的视频制作辅助平台，完成"字幕输入→语义分段→素材匹配→人工调整→结果保存"的业务闭环

**Architecture:** 单体后端(FastAPI) + SPA前端(Vue3)，使用PostgreSQL存储数据，Redis+Celery处理异步任务，混合匹配策略(关键词+Embedding)

**Tech Stack:** Vue3, TypeScript, Element Plus, FastAPI, Python, PostgreSQL, Redis, Celery

---

## 文件结构

```
project/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI应用入口
│   │   ├── config.py               # 配置管理
│   │   ├── database.py             # 数据库连接
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── task.py             # 任务模型
│   │   │   ├── subtitle_segment.py # 字幕片段模型
│   │   │   ├── media.py            # 素材模型
│   │   │   └── match_result.py     # 匹配结果模型
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── task.py
│   │   │   ├── subtitle_segment.py
│   │   │   ├── media.py
│   │   │   └── match_result.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── tasks.py            # 任务接口
│   │   │   ├── media.py            # 素材接口
│   │   │   └── transcribe.py       # 语音识别接口
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── subtitle_service.py # 字幕处理服务
│   │   │   ├── media_service.py    # 素材管理服务
│   │   │   ├── matching_service.py # 匹配服务
│   │   │   └── embedding_service.py # Embedding服务
│   │   └── workers/
│   │       ├── __init__.py
│   │       └── celery_app.py       # Celery配置
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_tasks.py
│   │   ├── test_media.py
│   │   └── test_matching.py
│   ├── alembic/
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── views/
│   │   │   ├── TaskList.vue
│   │   │   ├── TaskDetail.vue
│   │   │   └── MediaLibrary.vue
│   │   ├── components/
│   │   │   ├── SubtitleSegment.vue
│   │   │   ├── MediaCard.vue
│   │   │   └── MatchResult.vue
│   │   ├── api/
│   │   │   └── index.ts
│   │   └── types/
│   │       └── index.ts
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Task 1: 后端项目初始化

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: 创建requirements.txt**

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.13.0
celery==5.3.6
redis==5.0.1
python-multipart==0.0.6
pydantic==2.5.3
pydantic-settings==2.1.0
numpy==1.26.2
httpx==0.25.2
pytest==7.4.3
pytest-asyncio==0.23.2
```

- [ ] **Step 2: 创建config.py**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/subtitle"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 文件存储
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # AI服务
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_API_URL: str = ""
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
```

- [ ] **Step 3: 创建database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 4: 创建main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="AI字幕分析平台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && python -c "from app.main import app; print('Import OK')"`
Expected: Import OK

- [ ] **Step 6: 提交**

```bash
git add backend/
git commit -m "feat: initialize backend project with FastAPI"
```

---

## Task 2: 数据库模型

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/task.py`
- Create: `backend/app/models/subtitle_segment.py`
- Create: `backend/app/models/media.py`
- Create: `backend/app/models/match_result.py`

- [ ] **Step 1: 创建task.py模型**

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(20), nullable=False)  # video, audio, text
    status = Column(String(20), nullable=False, default="pending")  # pending, processing, completed, failed
    input_text = Column(Text, nullable=True)
    input_file_url = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: 创建subtitle_segment.py模型**

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.database import Base

class SubtitleSegment(Base):
    __tablename__ = "subtitle_segments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    start_time = Column(Integer, nullable=True)  # 毫秒
    end_time = Column(Integer, nullable=True)  # 毫秒
    keywords = Column(JSONB, nullable=True)
    embedding = Column(ARRAY(Float), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    selected_media_id = Column(UUID(as_uuid=True), ForeignKey("media.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 3: 创建media.py模型**

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.database import Base

class Media(Base):
    __tablename__ = "media"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(10), nullable=False)  # image, video
    url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)
    name = Column(String(255), nullable=True)
    tags = Column(JSONB, nullable=True)
    keywords = Column(JSONB, nullable=True)
    embedding = Column(ARRAY(Float), nullable=True)
    duration = Column(Integer, nullable=True)  # 秒
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 4: 创建match_result.py模型**

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class MatchResult(Base):
    __tablename__ = "match_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("subtitle_segments.id", ondelete="CASCADE"), nullable=False)
    media_id = Column(UUID(as_uuid=True), ForeignKey("media.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, nullable=True)
    keyword_score = Column(Float, nullable=True)
    semantic_score = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    rank = Column(Integer, nullable=True)
    model = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 5: 创建models/__init__.py**

```python
from app.models.task import Task
from app.models.subtitle_segment import SubtitleSegment
from app.models.media import Media
from app.models.match_result import MatchResult

__all__ = ["Task", "SubtitleSegment", "Media", "MatchResult"]
```

- [ ] **Step 6: 测试模型导入**

Run: `cd backend && python -c "from app.models import Task, SubtitleSegment, Media, MatchResult; print('Models OK')"`
Expected: Models OK

- [ ] **Step 7: 提交**

```bash
git add backend/app/models/
git commit -m "feat: add database models for tasks, segments, media, matches"
```

---

## Task 3: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/task.py`
- Create: `backend/app/schemas/subtitle_segment.py`
- Create: `backend/app/schemas/media.py`
- Create: `backend/app/schemas/match_result.py`

- [ ] **Step 1: 创建task.py schema**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class TaskCreate(BaseModel):
    type: str  # video, audio, text
    content: Optional[str] = None  # 文本内容

class TaskResponse(BaseModel):
    id: UUID
    type: str
    status: str
    input_text: Optional[str]
    input_file_url: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TaskStatus(BaseModel):
    task_id: UUID
    status: str
    progress: Optional[int] = None
    segments_count: Optional[int] = None
```

- [ ] **Step 2: 创建subtitle_segment.py schema**

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class SubtitleSegmentResponse(BaseModel):
    id: UUID
    task_id: UUID
    content: str
    start_time: Optional[int]
    end_time: Optional[int]
    keywords: Optional[List[str]]
    sort_order: int
    selected_media_id: Optional[UUID]
    created_at: datetime
    
    class Config:
        from_attributes = True

class SubtitleSegmentUpdate(BaseModel):
    content: Optional[str]
    sort_order: Optional[int]
    selected_media_id: Optional[UUID]
```

- [ ] **Step 3: 创建media.py schema**

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class MediaCreate(BaseModel):
    name: Optional[str]
    tags: Optional[List[str]] = []

class MediaResponse(BaseModel):
    id: UUID
    type: str
    url: str
    thumbnail_url: Optional[str]
    name: Optional[str]
    tags: Optional[List[str]]
    keywords: Optional[List[str]]
    duration: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MediaListResponse(BaseModel):
    items: List[MediaResponse]
    total: int
```

- [ ] **Step 4: 创建match_result.py schema**

```python
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class MatchResultResponse(BaseModel):
    id: UUID
    segment_id: UUID
    media_id: UUID
    score: Optional[float]
    keyword_score: Optional[float]
    semantic_score: Optional[float]
    reason: Optional[str]
    rank: Optional[int]
    model: Optional[str]
    
    class Config:
        from_attributes = True
```

- [ ] **Step 5: 创建schemas/__init__.py**

```python
from app.schemas.task import TaskCreate, TaskResponse, TaskStatus
from app.schemas.subtitle_segment import SubtitleSegmentResponse, SubtitleSegmentUpdate
from app.schemas.media import MediaCreate, MediaResponse, MediaListResponse
from app.schemas.match_result import MatchResultResponse

__all__ = [
    "TaskCreate", "TaskResponse", "TaskStatus",
    "SubtitleSegmentResponse", "SubtitleSegmentUpdate",
    "MediaCreate", "MediaResponse", "MediaListResponse",
    "MatchResultResponse"
]
```

- [ ] **Step 6: 测试schema导入**

Run: `cd backend && python -c "from app.schemas import TaskCreate, MediaResponse; print('Schemas OK')"`
Expected: Schemas OK

- [ ] **Step 7: 提交**

```bash
git add backend/app/schemas/
git commit -m "feat: add Pydantic schemas for API request/response"
```

---

## Task 4: 素材管理服务

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/media_service.py`
- Create: `backend/tests/test_media.py`

- [ ] **Step 1: 创建media_service.py**

```python
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
```

- [ ] **Step 2: 创建services/__init__.py**

```python
from app.services.media_service import MediaService

__all__ = ["MediaService"]
```

- [ ] **Step 3: 创建test_media.py**

```python
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
```

- [ ] **Step 4: 创建conftest.py**

```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && pytest tests/test_media.py -v`
Expected: 3 tests passed

- [ ] **Step 6: 提交**

```bash
git add backend/app/services/ backend/tests/
git commit -m "feat: add media service with CRUD operations"
```

---

## Task 5: 字幕处理服务

**Files:**
- Create: `backend/app/services/subtitle_service.py`
- Create: `backend/tests/test_subtitles.py`

- [ ] **Step 1: 创建subtitle_service.py**

```python
import re
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from app.models.subtitle_segment import SubtitleSegment
from app.schemas.subtitle_segment import SubtitleSegmentResponse

class SubtitleService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def parse_text(self, text: str) -> List[dict]:
        """解析文本字幕，按句子分段"""
        # 按句号、问号、感叹号分句
        sentences = re.split(r'(?<=[。！？!?\n])', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        segments = []
        for i, sentence in enumerate(sentences):
            segments.append({
                "content": sentence,
                "start_time": None,
                "end_time": None,
                "sort_order": i
            })
        return segments
    
    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简单实现：提取中文词汇和英文单词）"""
        # 提取中文词汇（2-4字）
        chinese_words = re.findall(r'[一-龥]{2,4}', text)
        # 提取英文单词
        english_words = re.findall(r'[a-zA-Z]+', text)
        
        # 去重并返回
        keywords = list(set(chinese_words + english_words))
        return keywords[:10]  # 最多10个关键词
    
    async def create_segments(self, task_id: UUID, text: str) -> List[SubtitleSegment]:
        """为任务创建字幕片段"""
        parsed = self.parse_text(text)
        segments = []
        
        for item in parsed:
            segment = SubtitleSegment(
                task_id=task_id,
                content=item["content"],
                start_time=item["start_time"],
                end_time=item["end_time"],
                keywords=self.extract_keywords(item["content"]),
                sort_order=item["sort_order"]
            )
            self.db.add(segment)
            segments.append(segment)
        
        await self.db.flush()
        return segments
    
    async def get_segments(self, task_id: UUID) -> List[SubtitleSegment]:
        """获取任务的所有字幕片段"""
        from sqlalchemy import select
        result = await self.db.execute(
            select(SubtitleSegment)
            .where(SubtitleSegment.task_id == task_id)
            .order_by(SubtitleSegment.sort_order)
        )
        return result.scalars().all()
    
    async def update_segment(self, segment_id: UUID, **kwargs) -> Optional[SubtitleSegment]:
        """更新字幕片段"""
        from sqlalchemy import select
        result = await self.db.execute(
            select(SubtitleSegment).where(SubtitleSegment.id == segment_id)
        )
        segment = result.scalar_one_or_none()
        
        if segment:
            for key, value in kwargs.items():
                if value is not None and hasattr(segment, key):
                    setattr(segment, key, value)
            await self.db.flush()
        
        return segment
```

- [ ] **Step 2: 创建test_subtitles.py**

```python
import pytest
from app.services.subtitle_service import SubtitleService

def test_parse_text():
    service = SubtitleService(None)
    text = "今天我们来学习Python。首先安装环境！然后开始编程？"
    segments = service.parse_text(text)
    assert len(segments) == 3
    assert segments[0]["content"] == "今天我们来学习Python。"
    assert segments[1]["content"] == "首先安装环境！"

def test_extract_keywords():
    service = SubtitleService(None)
    text = "今天我们来学习Python编程基础"
    keywords = service.extract_keywords(text)
    assert "Python" in keywords
    assert "编程" in keywords or "学习" in keywords

def test_parse_multiline():
    service = SubtitleService(None)
    text = """第一行字幕
第二行字幕
第三行字幕"""
    segments = service.parse_text(text)
    assert len(segments) == 3
```

- [ ] **Step 3: 运行测试**

Run: `cd backend && pytest tests/test_subtitles.py -v`
Expected: 3 tests passed

- [ ] **Step 4: 提交**

```bash
git add backend/app/services/subtitle_service.py backend/tests/test_subtitles.py
git commit -m "feat: add subtitle parsing and keyword extraction"
```

---

## Task 6: Embedding服务

**Files:**
- Create: `backend/app/services/embedding_service.py`

- [ ] **Step 1: 创建embedding_service.py**

```python
import numpy as np
from typing import List, Optional
import httpx
from app.config import get_settings

settings = get_settings()

class EmbeddingService:
    def __init__(self):
        self.api_key = settings.EMBEDDING_API_KEY
        self.api_url = settings.EMBEDDING_API_URL
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本的embedding向量"""
        if not self.api_key or not self.api_url:
            # 降级：返回随机向量（用于演示）
            return self._dummy_embedding(text)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"input": text, "model": "text-embedding-ada-002"}
                )
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            print(f"Embedding API error: {e}")
            return self._dummy_embedding(text)
    
    def _dummy_embedding(self, text: str) -> List[float]:
        """生成伪embedding（基于文本哈希）"""
        np.random.seed(hash(text) % 2**32)
        return np.random.rand(1536).tolist()
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

- [ ] **Step 2: 测试embedding服务**

Run: `cd backend && python -c "from app.services.embedding_service import EmbeddingService; s = EmbeddingService(); print(len(s._dummy_embedding('test')))" `
Expected: 1536

- [ ] **Step 3: 提交**

```bash
git add backend/app/services/embedding_service.py
git commit -m "feat: add embedding service with fallback"
```

---

## Task 7: 匹配服务

**Files:**
- Create: `backend/app/services/matching_service.py`
- Create: `backend/tests/test_matching.py`

- [ ] **Step 1: 创建matching_service.py**

```python
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.media import Media
from app.models.match_result import MatchResult
from app.services.embedding_service import EmbeddingService
from app.config import get_settings

settings = get_settings()

class MatchingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = EmbeddingService()
    
    def keyword_match(self, segment_keywords: List[str], media_tags: List[str]) -> float:
        """关键词匹配（Jaccard相似度）"""
        if not segment_keywords or not media_tags:
            return 0.0
        intersection = set(segment_keywords) & set(media_tags)
        union = set(segment_keywords) | set(media_tags)
        return len(intersection) / len(union) if union else 0.0
    
    async def semantic_match(self, segment_embedding: List[float], media_embedding: List[float]) -> float:
        """语义匹配（余弦相似度）"""
        if not segment_embedding or not media_embedding:
            return 0.0
        return self.embedding_service.cosine_similarity(segment_embedding, media_embedding)
    
    def generate_reason(self, matched_keywords: List[str], semantic_score: float) -> str:
        """生成匹配理由"""
        reasons = []
        if matched_keywords:
            reasons.append(f"关键词匹配: {', '.join(matched_keywords)}")
        if semantic_score > 0.8:
            reasons.append("语义高度相关")
        elif semantic_score > 0.6:
            reasons.append("语义相关")
        return " | ".join(reasons) if reasons else "无匹配"
    
    async def match_segment(self, segment_id: UUID) -> List[dict]:
        """为单个字幕片段匹配素材"""
        from app.models.subtitle_segment import SubtitleSegment
        
        # 获取字幕片段
        result = await self.db.execute(
            select(SubtitleSegment).where(SubtitleSegment.id == segment_id)
        )
        segment = result.scalar_one_or_none()
        if not segment:
            return []
        
        # 获取所有素材
        media_result = await self.db.execute(select(Media))
        all_media = media_result.scalars().all()
        
        if not all_media:
            return []
        
        # 计算匹配分数
        matches = []
        for media in all_media:
            # 关键词匹配
            kw_score = self.keyword_match(segment.keywords or [], media.tags or [])
            
            # 语义匹配
            sem_score = 0.0
            if segment.embedding and media.embedding:
                sem_score = await self.semantic_match(segment.embedding, media.embedding)
            
            # 混合分数
            total_score = (
                settings.KEYWORD_WEIGHT * kw_score + 
                settings.SEMANTIC_WEIGHT * sem_score
            )
            
            # 匹配关键词
            matched_kw = list(set(segment.keywords or []) & set(media.tags or []))
            
            matches.append({
                "media_id": media.id,
                "score": total_score,
                "keyword_score": kw_score,
                "semantic_score": sem_score,
                "reason": self.generate_reason(matched_kw, sem_score)
            })
        
        # 排序并返回Top3
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:3]
    
    async def save_match_results(self, segment_id: UUID, matches: List[dict]) -> List[MatchResult]:
        """保存匹配结果"""
        results = []
        for i, match in enumerate(matches):
            result = MatchResult(
                segment_id=segment_id,
                media_id=match["media_id"],
                score=match["score"],
                keyword_score=match["keyword_score"],
                semantic_score=match["semantic_score"],
                reason=match["reason"],
                rank=i + 1,
                model="hybrid"
            )
            self.db.add(result)
            results.append(result)
        
        await self.db.flush()
        return results
```

- [ ] **Step 2: 创建test_matching.py**

```python
import pytest
from app.services.matching_service import MatchingService

def test_keyword_match():
    service = MatchingService(None)
    score = service.keyword_match(["Python", "编程"], ["Python", "代码"])
    assert score == 0.5  # 1个共同关键词 / 3个总关键词

def test_keyword_match_empty():
    service = MatchingService(None)
    assert service.keyword_match([], ["Python"]) == 0.0
    assert service.keyword_match(["Python"], []) == 0.0

def test_generate_reason():
    service = MatchingService(None)
    reason = service.generate_reason(["Python", "编程"], 0.85)
    assert "关键词匹配: Python, 编程" in reason
    assert "语义高度相关" in reason
```

- [ ] **Step 3: 运行测试**

Run: `cd backend && pytest tests/test_matching.py -v`
Expected: 3 tests passed

- [ ] **Step 4: 提交**

```bash
git add backend/app/services/matching_service.py backend/tests/test_matching.py
git commit -m "feat: add hybrid matching service with keyword and semantic"
```

---

## Task 8: 任务API接口

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/tasks.py`
- Create: `backend/tests/test_tasks.py`

- [ ] **Step 1: 创建tasks.py**

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.models.task import Task
from app.models.subtitle_segment import SubtitleSegment
from app.schemas.task import TaskCreate, TaskResponse, TaskStatus
from app.schemas.subtitle_segment import SubtitleSegmentResponse
from app.services.subtitle_service import SubtitleService
import os
import uuid

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.post("", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建字幕任务"""
    task = Task(
        type=task_data.type,
        input_text=task_data.content,
        status="pending"
    )
    db.add(task)
    await db.flush()
    
    # 如果是文本类型，直接解析
    if task_data.type == "text" and task_data.content:
        task.status = "processing"
        service = SubtitleService(db)
        await service.create_segments(task.id, task_data.content)
        task.status = "completed"
    
    return task

@router.get("/{task_id}", response_model=TaskStatus)
async def get_task_status(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取任务状态"""
    from sqlalchemy import select, func
    
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 获取片段数量
    count_result = await db.execute(
        select(func.count(SubtitleSegment.id))
        .where(SubtitleSegment.task_id == task_id)
    )
    segments_count = count_result.scalar()
    
    return TaskStatus(
        task_id=task.id,
        status=task.status,
        segments_count=segments_count
    )

@router.get("/{task_id}/segments", response_model=list[SubtitleSegmentResponse])
async def get_task_segments(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取任务的字幕片段"""
    service = SubtitleService(db)
    segments = await service.get_segments(task_id)
    return segments

@router.put("/{task_id}/segments/{segment_id}")
async def update_segment(
    task_id: UUID,
    segment_id: UUID,
    content: Optional[str] = None,
    sort_order: Optional[int] = None,
    selected_media_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """更新字幕片段"""
    service = SubtitleService(db)
    segment = await service.update_segment(
        segment_id,
        content=content,
        sort_order=sort_order,
        selected_media_id=selected_media_id
    )
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    return {"message": "Updated"}

@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """重试任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status == "completed":
        return {"message": "Task already completed", "task_id": task.id}
    
    if task.status == "processing":
        return {"message": "Task is processing", "task_id": task.id}
    
    task.status = "pending"
    return task
```

- [ ] **Step 2: 创建api/__init__.py**

```python
from fastapi import APIRouter
from app.api.tasks import router as tasks_router
from app.api.media import router as media_router

api_router = APIRouter()
api_router.include_router(tasks_router)
api_router.include_router(media_router)
```

- [ ] **Step 3: 更新main.py添加路由**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import api_router  # 添加这行

settings = get_settings()

app = FastAPI(title="AI字幕分析平台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)  # 添加这行

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

- [ ] **Step 4: 创建test_tasks.py**

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_task():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/tasks", json={
            "type": "text",
            "content": "第一句话。第二句话。"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

@pytest.mark.asyncio
async def test_get_task_status():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 创建任务
        create_resp = await client.post("/api/tasks", json={
            "type": "text",
            "content": "测试内容"
        })
        task_id = create_resp.json()["id"]
        
        # 获取状态
        response = await client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && pytest tests/test_tasks.py -v`
Expected: 2 tests passed

- [ ] **Step 6: 提交**

```bash
git add backend/app/api/ backend/tests/test_tasks.py backend/app/main.py
git commit -m "feat: add task API endpoints for CRUD operations"
```

---

## Task 9: 素材API接口

**Files:**
- Create: `backend/app/api/media.py`
- Create: `backend/app/services/media_service.py` (更新)

- [ ] **Step 1: 创建media.py**

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.schemas.media import MediaCreate, MediaResponse, MediaListResponse
from app.services.media_service import MediaService
import os
import uuid

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
    import json
    
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
```

- [ ] **Step 2: 运行测试**

Run: `cd backend && python -c "from app.api.media import router; print('Media API OK')"`
Expected: Media API OK

- [ ] **Step 3: 提交**

```bash
git add backend/app/api/media.py
git commit -m "feat: add media API endpoints for upload and management"
```

---

## Task 10: Celery异步任务

**Files:**
- Create: `backend/app/workers/__init__.py`
- Create: `backend/app/workers/celery_app.py`
- Create: `backend/app/workers/tasks.py`

- [ ] **Step 1: 创建celery_app.py**

```python
from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5分钟超时
    task_soft_time_limit=240,  # 4分钟软超时
)
```

- [ ] **Step 2: 创建tasks.py**

```python
from app.workers.celery_app import celery_app
from app.database import async_session
from app.models.task import Task
from app.models.subtitle_segment import SubtitleSegment
from app.services.subtitle_service import SubtitleService
from app.services.matching_service import MatchingService
from sqlalchemy import select
import asyncio

@celery_app.task(bind=True, name="process_task")
def process_task(self, task_id: str):
    """处理字幕任务"""
    asyncio.run(_process_task_async(self, task_id))

async def _process_task_async(task, task_id: str):
    """异步处理任务"""
    async with async_session() as db:
        try:
            # 更新状态为处理中
            result = await db.execute(select(Task).where(Task.id == task_id))
            task_obj = result.scalar_one_or_none()
            
            if not task_obj:
                return {"error": "Task not found"}
            
            task_obj.status = "processing"
            await db.commit()
            
            # 如果有输入文本，解析字幕
            if task_obj.input_text:
                subtitle_service = SubtitleService(db)
                await subtitle_service.create_segments(task_id, task_obj.input_text)
            
            # 标记完成
            task_obj.status = "completed"
            await db.commit()
            
            return {"status": "completed", "task_id": task_id}
            
        except Exception as e:
            # 标记失败
            task_obj.status = "failed"
            task_obj.error_message = str(e)
            await db.commit()
            return {"error": str(e)}

@celery_app.task(bind=True, name="match_segment")
def match_segment_task(self, segment_id: str):
    """匹配单个字幕片段"""
    asyncio.run(_match_segment_async(self, segment_id))

async def _match_segment_async(task, segment_id: str):
    """异步匹配片段"""
    async with async_session() as db:
        try:
            matching_service = MatchingService(db)
            matches = await matching_service.match_segment(segment_id)
            await matching_service.save_match_results(segment_id, matches)
            await db.commit()
            return {"status": "completed", "segment_id": segment_id}
        except Exception as e:
            return {"error": str(e)}
```

- [ ] **Step 3: 创建workers/__init__.py**

```python
from app.workers.celery_app import celery_app
from app.workers.tasks import process_task, match_segment_task

__all__ = ["celery_app", "process_task", "match_segment_task"]
```

- [ ] **Step 4: 测试导入**

Run: `cd backend && python -c "from app.workers import celery_app; print('Celery OK')"`
Expected: Celery OK

- [ ] **Step 5: 提交**

```bash
git add backend/app/workers/
git commit -m "feat: add Celery worker for async task processing"
```

---

## Task 11: 语音识别接口

**Files:**
- Create: `backend/app/api/transcribe.py`
- Create: `backend/app/services/transcription_service.py`

- [ ] **Step 1: 创建transcription_service.py**

```python
import httpx
from typing import Optional
from app.config import get_settings

settings = get_settings()

class TranscriptionService:
    def __init__(self):
        self.api_key = settings.SPEECH_API_KEY
        self.api_url = settings.SPEECH_API_URL
    
    async def transcribe(self, file_path: str) -> Optional[str]:
        """语音识别"""
        if not self.api_key or not self.api_url:
            # 降级：返回示例文本
            return "这是语音识别的示例文本。请配置真实的语音识别API。"
        
        try:
            async with httpx.AsyncClient() as client:
                with open(file_path, "rb") as f:
                    response = await client.post(
                        self.api_url,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files={"file": f}
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data.get("text", "")
        except Exception as e:
            print(f"Transcription error: {e}")
            return None
```

- [ ] **Step 2: 创建transcribe.py**

```python
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from app.database import get_db
from app.models.task import Task
from app.services.transcription_service import TranscriptionService
from app.services.subtitle_service import SubtitleService
import os

router = APIRouter(prefix="/api/transcribe", tags=["transcribe"])

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("")
async def create_transcription(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """提交语音识别任务"""
    # 保存文件
    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 创建任务
    task = Task(
        type="audio",
        input_file_url=f"/uploads/{file_name}",
        status="processing"
    )
    db.add(task)
    await db.flush()
    
    # 执行识别
    service = TranscriptionService()
    text = await service.transcribe(file_path)
    
    if text:
        task.input_text = text
        # 解析字幕
        subtitle_service = SubtitleService(db)
        await subtitle_service.create_segments(task.id, text)
        task.status = "completed"
    else:
        task.status = "failed"
        task.error_message = "语音识别失败"
    
    return {"task_id": task.id, "status": task.status}

@router.get("/{task_id}")
async def get_transcription(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取识别结果"""
    from sqlalchemy import select
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        return {"error": "Task not found"}
    
    return {
        "status": task.status,
        "text": task.input_text,
        "error": task.error_message
    }
```

- [ ] **Step 3: 更新api/__init__.py添加transcribe路由**

```python
from fastapi import APIRouter
from app.api.tasks import router as tasks_router
from app.api.media import router as media_router
from app.api.transcribe import router as transcribe_router

api_router = APIRouter()
api_router.include_router(tasks_router)
api_router.include_router(media_router)
api_router.include_router(transcribe_router)
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/api/transcribe.py backend/app/services/transcription_service.py backend/app/api/__init__.py
git commit -m "feat: add transcription API with fallback"
```

---

## Task 12: Alembic数据库迁移

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/001_initial.py`

- [ ] **Step 1: 初始化Alembic**

Run: `cd backend && alembic init alembic`

- [ ] **Step 2: 更新alembic.ini**

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost:5432/subtitle

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 3: 更新env.py**

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import Task, SubtitleSegment, Media, MatchResult

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: 生成初始迁移**

Run: `cd backend && alembic revision --autogenerate -m "initial"`
Expected: 生成 `alembic/versions/xxxx_initial.py`

- [ ] **Step 5: 运行迁移**

Run: `cd backend && alembic upgrade head`
Expected: 数据库表创建成功

- [ ] **Step 6: 提交**

```bash
git add backend/alembic/
git commit -m "feat: add Alembic database migrations"
```

---

## Task 13: 前端项目初始化

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/types/index.ts`

- [ ] **Step 1: 创建package.json**

```json
{
  "name": "subtitle-platform-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "element-plus": "^2.4.4",
    "axios": "^1.6.2"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.5.2",
    "typescript": "^5.3.3",
    "vite": "^5.0.10",
    "vue-tsc": "^1.8.25"
  }
}
```

- [ ] **Step 2: 创建vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 3: 创建index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI字幕分析平台</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

- [ ] **Step 4: 创建main.ts**

```typescript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(ElementPlus)
app.use(router)
app.mount('#app')
```

- [ ] **Step 5: 创建App.vue**

```vue
<template>
  <el-container>
    <el-header>
      <el-menu mode="horizontal" :router="true">
        <el-menu-item index="/">字幕任务</el-menu-item>
        <el-menu-item index="/media">素材库</el-menu-item>
      </el-menu>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
</script>

<style>
body {
  margin: 0;
  padding: 0;
}
</style>
```

- [ ] **Step 6: 创建router/index.ts**

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'TaskList',
      component: () => import('../views/TaskList.vue')
    },
    {
      path: '/tasks/new',
      name: 'TaskNew',
      component: () => import('../views/TaskNew.vue')
    },
    {
      path: '/tasks/:id',
      name: 'TaskDetail',
      component: () => import('../views/TaskDetail.vue')
    },
    {
      path: '/media',
      name: 'MediaLibrary',
      component: () => import('../views/MediaLibrary.vue')
    }
  ]
})

export default router
```

- [ ] **Step 7: 创建types/index.ts**

```typescript
export interface Task {
  id: string
  type: 'video' | 'audio' | 'text'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  input_text?: string
  input_file_url?: string
  error_message?: string
  created_at: string
  updated_at: string
}

export interface SubtitleSegment {
  id: string
  task_id: string
  content: string
  start_time?: number
  end_time?: number
  keywords?: string[]
  sort_order: number
  selected_media_id?: string
  matches?: MatchResult[]
}

export interface Media {
  id: string
  type: 'image' | 'video'
  url: string
  thumbnail_url?: string
  name?: string
  tags?: string[]
  keywords?: string[]
  duration?: number
  created_at: string
}

export interface MatchResult {
  id: string
  segment_id: string
  media_id: string
  score?: number
  keyword_score?: number
  semantic_score?: number
  reason?: string
  rank?: number
}
```

- [ ] **Step 8: 安装依赖并测试**

Run: `cd frontend && npm install`
Run: `cd frontend && npm run dev`
Expected: 开发服务器启动成功

- [ ] **Step 9: 提交**

```bash
git add frontend/
git commit -m "feat: initialize Vue3 frontend project"
```

---

## Task 14: 前端API服务

**Files:**
- Create: `frontend/src/api/index.ts`

- [ ] **Step 1: 创建api/index.ts**

```typescript
import axios from 'axios'
import type { Task, SubtitleSegment, Media, MatchResult } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 任务相关API
export const taskApi = {
  create(data: { type: string; content?: string }) {
    return api.post<Task>('/tasks', data)
  },
  
  getStatus(taskId: string) {
    return api.get<{ task_id: string; status: string; segments_count?: number }>(
      `/tasks/${taskId}`
    )
  },
  
  getSegments(taskId: string) {
    return api.get<SubtitleSegment[]>(`/tasks/${taskId}/segments`)
  },
  
  updateSegment(taskId: string, segmentId: string, data: Partial<SubtitleSegment>) {
    return api.put(`/tasks/${taskId}/segments/${segmentId}`, data)
  },
  
  retry(taskId: string) {
    return api.post(`/tasks/${taskId}/retry`)
  }
}

// 素材相关API
export const mediaApi = {
  list(params?: { keyword?: string; page?: number; size?: number }) {
    return api.get<{ items: Media[]; total: number }>('/media', { params })
  },
  
  get(mediaId: string) {
    return api.get<Media>(`/media/${mediaId}`)
  },
  
  upload(file: File, name?: string, tags?: string[]) {
    const formData = new FormData()
    formData.append('file', file)
    if (name) formData.append('name', name)
    if (tags) formData.append('tags', JSON.stringify(tags))
    return api.post<Media>('/media', formData)
  },
  
  delete(mediaId: string) {
    return api.delete(`/media/${mediaId}`)
  }
}

// 语音识别API
export const transcribeApi = {
  create(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<{ task_id: string; status: string }>('/transcribe', formData)
  },
  
  getStatus(taskId: string) {
    return api.get<{ status: string; text?: string; error?: string }>(
      `/transcribe/${taskId}`
    )
  }
}

export default api
```

- [ ] **Step 2: 测试导入**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 3: 提交**

```bash
git add frontend/src/api/
git commit -m "feat: add API service for tasks, media, and transcription"
```

---

## Task 15: 任务列表页面

**Files:**
- Create: `frontend/src/views/TaskList.vue`
- Create: `frontend/src/views/TaskNew.vue`

- [ ] **Step 1: 创建TaskList.vue**

```vue
<template>
  <div class="task-list">
    <el-button type="primary" @click="$router.push('/tasks/new')">
      新建任务
    </el-button>
    
    <el-table :data="tasks" style="width: 100%; margin-top: 20px;">
      <el-table-column prop="id" label="任务ID" width="120" />
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag>{{ row.type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="viewTask(row.id)">查看</el-button>
          <el-button size="small" type="warning" @click="retryTask(row.id)">
            重试
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { taskApi } from '../api'
import type { Task } from '../types'

const router = useRouter()
const tasks = ref<Task[]>([])

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const loadTasks = async () => {
  try {
    // TODO: 实现任务列表API
    tasks.value = []
  } catch (error) {
    ElMessage.error('加载任务列表失败')
  }
}

const viewTask = (id: string) => {
  router.push(`/tasks/${id}`)
}

const retryTask = async (id: string) => {
  try {
    await taskApi.retry(id)
    ElMessage.success('任务已重新提交')
    loadTasks()
  } catch (error) {
    ElMessage.error('重试失败')
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.task-list {
  padding: 20px;
}
</style>
```

- [ ] **Step 2: 创建TaskNew.vue**

```vue
<template>
  <div class="task-new">
    <h2>新建字幕任务</h2>
    
    <el-tabs v-model="activeTab">
      <el-tab-pane label="文本输入" name="text">
        <el-input
          v-model="textContent"
          type="textarea"
          :rows="10"
          placeholder="请输入字幕文本..."
        />
        <el-button 
          type="primary" 
          @click="createTextTask"
          :loading="loading"
          style="margin-top: 20px;"
        >
          创建任务
        </el-button>
      </el-tab-pane>
      
      <el-tab-pane label="上传文件" name="file">
        <el-upload
          class="upload-demo"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          accept=".mp4,.avi,.mov,.mp3,.wav"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 mp4, avi, mov, mp3, wav 格式
            </div>
          </template>
        </el-upload>
        <el-button 
          type="primary" 
          @click="uploadFile"
          :loading="loading"
          :disabled="!selectedFile"
          style="margin-top: 20px;"
        >
          上传并创建任务
        </el-button>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { taskApi, transcribeApi } from '../api'

const router = useRouter()
const activeTab = ref('text')
const textContent = ref('')
const selectedFile = ref<File | null>(null)
const loading = ref(false)

const createTextTask = async () => {
  if (!textContent.value.trim()) {
    ElMessage.warning('请输入字幕文本')
    return
  }
  
  loading.value = true
  try {
    const { data } = await taskApi.create({
      type: 'text',
      content: textContent.value
    })
    ElMessage.success('任务创建成功')
    router.push(`/tasks/${data.id}`)
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    loading.value = false
  }
}

const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
}

const uploadFile = async () => {
  if (!selectedFile.value) return
  
  loading.value = true
  try {
    const { data } = await transcribeApi.create(selectedFile.value)
    ElMessage.success('文件上传成功，正在识别...')
    router.push(`/tasks/${data.task_id}`)
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.task-new {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}
</style>
```

- [ ] **Step 3: 测试构建**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/TaskList.vue frontend/src/views/TaskNew.vue
git commit -m "feat: add task list and create task pages"
```

---

## Task 16: 任务详情页面

**Files:**
- Create: `frontend/src/views/TaskDetail.vue`
- Create: `frontend/src/components/SubtitleSegment.vue`
- Create: `frontend/src/components/MatchResult.vue`

- [ ] **Step 1: 创建MatchResult.vue**

```vue
<template>
  <div class="match-result" :class="{ selected: isSelected }">
    <el-card shadow="hover" @click="$emit('select', match.media_id)">
      <div class="match-info">
        <div class="media-preview">
          <img v-if="media" :src="media.url" :alt="media.name" />
          <div v-else class="placeholder">暂无预览</div>
        </div>
        <div class="match-details">
          <div class="score">
            匹配度: {{ (match.score * 100).toFixed(0) }}%
          </div>
          <div class="reason">{{ match.reason }}</div>
          <div class="scores">
            <span>关键词: {{ (match.keyword_score * 100).toFixed(0) }}%</span>
            <span>语义: {{ (match.semantic_score * 100).toFixed(0) }}%</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { MatchResult, Media } from '../types'

const props = defineProps<{
  match: MatchResult
  media?: Media
  isSelected?: boolean
}>()

defineEmits<{
  select: [mediaId: string]
}>()
</script>

<style scoped>
.match-result {
  cursor: pointer;
  margin-bottom: 10px;
}

.match-result.selected {
  border: 2px solid #409eff;
}

.match-info {
  display: flex;
  gap: 15px;
}

.media-preview {
  width: 100px;
  height: 100px;
  overflow: hidden;
  border-radius: 4px;
}

.media-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #909399;
}

.match-details {
  flex: 1;
}

.score {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.reason {
  color: #606266;
  margin-bottom: 5px;
}

.scores {
  font-size: 12px;
  color: #909399;
}

.scores span {
  margin-right: 10px;
}
</style>
```

- [ ] **Step 2: 创建SubtitleSegment.vue**

```vue
<template>
  <div class="subtitle-segment">
    <el-card class="segment-card">
      <template #header>
        <div class="segment-header">
          <span class="order">[{{ segment.sort_order + 1 }}]</span>
          <el-input
            v-model="editContent"
            type="textarea"
            :rows="2"
            @blur="saveContent"
          />
          <el-button size="small" @click="$emit('reorder', segment.id)">
            拖拽
          </el-button>
        </div>
      </template>
      
      <div class="keywords" v-if="segment.keywords?.length">
        <span>关键词:</span>
        <el-tag
          v-for="keyword in segment.keywords"
          :key="keyword"
          size="small"
          style="margin-left: 5px;"
        >
          {{ keyword }}
        </el-tag>
      </div>
      
      <div class="matches" v-if="segment.matches?.length">
        <h4>推荐素材</h4>
        <MatchResult
          v-for="match in segment.matches"
          :key="match.id"
          :match="match"
          :is-selected="segment.selected_media_id === match.media_id"
          @select="selectMedia"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import MatchResult from './MatchResult.vue'
import type { SubtitleSegment } from '../types'
import { taskApi } from '../api'

const props = defineProps<{
  segment: SubtitleSegment
}>()

const emit = defineEmits<{
  update: []
  reorder: [segmentId: string]
}>()

const editContent = ref(props.segment.content)

watch(() => props.segment.content, (newVal) => {
  editContent.value = newVal
})

const saveContent = async () => {
  if (editContent.value === props.segment.content) return
  
  try {
    await taskApi.updateSegment(props.segment.task_id, props.segment.id, {
      content: editContent.value
    })
    ElMessage.success('已保存')
    emit('update')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const selectMedia = async (mediaId: string) => {
  try {
    await taskApi.updateSegment(props.segment.task_id, props.segment.id, {
      selected_media_id: mediaId
    })
    ElMessage.success('已选择素材')
    emit('update')
  } catch (error) {
    ElMessage.error('选择失败')
  }
}
</script>

<style scoped>
.segment-card {
  margin-bottom: 20px;
}

.segment-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.order {
  font-weight: bold;
  color: #409eff;
}

.keywords {
  margin-top: 10px;
  color: #606266;
}

.matches {
  margin-top: 15px;
}

.matches h4 {
  margin-bottom: 10px;
  color: #303133;
}
</style>
```

- [ ] **Step 3: 创建TaskDetail.vue**

```vue
<template>
  <div class="task-detail">
    <div class="task-header">
      <h2>任务详情</h2>
      <el-tag :type="getStatusType(task?.status)">
        {{ task?.status }}
      </el-tag>
    </div>
    
    <div v-if="loading" class="loading">
      <el-skeleton :rows="5" animated />
    </div>
    
    <div v-else-if="task?.status === 'processing'" class="processing">
      <el-progress :percentage="50" status="warning" />
      <p>任务处理中，请稍候...</p>
    </div>
    
    <div v-else-if="task?.status === 'failed'" class="failed">
      <el-alert
        :title="task.error_message || '任务处理失败'"
        type="error"
        show-icon
      />
      <el-button type="primary" @click="retryTask" style="margin-top: 20px;">
        重试
      </el-button>
    </div>
    
    <div v-else class="segments">
      <SubtitleSegment
        v-for="segment in segments"
        :key="segment.id"
        :segment="segment"
        @update="loadSegments"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { taskApi } from '../api'
import type { Task, SubtitleSegment } from '../types'
import SubtitleSegmentComponent from '../components/SubtitleSegment.vue'

const route = useRoute()
const taskId = route.params.id as string

const task = ref<Task | null>(null)
const segments = ref<SubtitleSegment[]>([])
const loading = ref(true)
let pollTimer: number | null = null

const getStatusType = (status?: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status || ''] || 'info'
}

const loadTask = async () => {
  try {
    const { data } = await taskApi.getStatus(taskId)
    task.value = {
      ...data,
      id: data.task_id
    } as Task
  } catch (error) {
    ElMessage.error('加载任务失败')
  }
}

const loadSegments = async () => {
  try {
    const { data } = await taskApi.getSegments(taskId)
    segments.value = data
  } catch (error) {
    ElMessage.error('加载字幕片段失败')
  }
}

const startPolling = () => {
  pollTimer = window.setInterval(async () => {
    await loadTask()
    if (task.value?.status === 'completed') {
      await loadSegments()
      stopPolling()
    } else if (task.value?.status === 'failed') {
      stopPolling()
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const retryTask = async () => {
  try {
    await taskApi.retry(taskId)
    ElMessage.success('任务已重新提交')
    loading.value = true
    await loadTask()
    startPolling()
  } catch (error) {
    ElMessage.error('重试失败')
  }
}

onMounted(async () => {
  await loadTask()
  if (task.value?.status === 'completed') {
    await loadSegments()
  } else if (task.value?.status === 'processing') {
    startPolling()
  }
  loading.value = false
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.task-detail {
  padding: 20px;
}

.task-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
}

.loading, .processing, .failed {
  text-align: center;
  padding: 50px;
}
</style>
```

- [ ] **Step 4: 测试构建**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/TaskDetail.vue frontend/src/components/
git commit -m "feat: add task detail page with segment editing"
```

---

## Task 17: 素材库页面

**Files:**
- Create: `frontend/src/views/MediaLibrary.vue`
- Create: `frontend/src/components/MediaCard.vue`

- [ ] **Step 1: 创建MediaCard.vue**

```vue
<template>
  <el-card class="media-card" shadow="hover">
    <div class="media-preview">
      <img v-if="media.type === 'image'" :src="media.url" :alt="media.name" />
      <video v-else :src="media.url" controls />
    </div>
    <div class="media-info">
      <div class="name">{{ media.name }}</div>
      <div class="tags">
        <el-tag
          v-for="tag in media.tags"
          :key="tag"
          size="small"
          style="margin-right: 5px;"
        >
          {{ tag }}
        </el-tag>
      </div>
      <div class="actions">
        <el-button size="small" type="danger" @click="$emit('delete')">
          删除
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { Media } from '../types'

defineProps<{
  media: Media
}>()

defineEmits<{
  delete: []
}>()
</script>

<style scoped>
.media-card {
  margin-bottom: 20px;
}

.media-preview {
  height: 200px;
  overflow: hidden;
  margin-bottom: 10px;
}

.media-preview img,
.media-preview video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.name {
  font-weight: bold;
  margin-bottom: 5px;
}

.tags {
  margin-bottom: 10px;
}
</style>
```

- [ ] **Step 2: 创建MediaLibrary.vue**

```vue
<template>
  <div class="media-library">
    <div class="header">
      <h2>素材库</h2>
      <el-upload
        :auto-upload="false"
        :on-change="handleUpload"
        :show-file-list="false"
      >
        <el-button type="primary">上传素材</el-button>
      </el-upload>
    </div>
    
    <div class="search">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索素材..."
        @input="searchMedia"
        clearable
      />
    </div>
    
    <div class="media-grid">
      <MediaCard
        v-for="media in mediaList"
        :key="media.id"
        :media="media"
        @delete="deleteMedia(media.id)"
      />
    </div>
    
    <el-empty v-if="mediaList.length === 0" description="暂无素材" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { mediaApi } from '../api'
import type { Media } from '../types'
import MediaCard from '../components/MediaCard.vue'

const mediaList = ref<Media[]>([])
const searchKeyword = ref('')

const loadMedia = async () => {
  try {
    const { data } = await mediaApi.list({ keyword: searchKeyword.value })
    mediaList.value = data.items
  } catch (error) {
    ElMessage.error('加载素材失败')
  }
}

const searchMedia = () => {
  loadMedia()
}

const handleUpload = async (file: any) => {
  try {
    await mediaApi.upload(file.raw, file.name)
    ElMessage.success('上传成功')
    loadMedia()
  } catch (error) {
    ElMessage.error('上传失败')
  }
}

const deleteMedia = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定删除该素材？', '提示', {
      type: 'warning'
    })
    await mediaApi.delete(id)
    ElMessage.success('删除成功')
    loadMedia()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadMedia()
})
</script>

<style scoped>
.media-library {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.search {
  margin-bottom: 20px;
  max-width: 400px;
}

.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}
</style>
```

- [ ] **Step 3: 测试构建**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/MediaLibrary.vue frontend/src/components/MediaCard.vue
git commit -m "feat: add media library page with upload and search"
```

---

## Task 18: Docker配置

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `nginx/nginx.conf`
- Create: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: 创建backend/Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: 创建frontend/Dockerfile**

```dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

- [ ] **Step 3: 创建nginx/nginx.conf**

```nginx
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

- [ ] **Step 4: 创建docker-compose.yml**

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - api
  
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/subtitle
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - uploads:/app/uploads
  
  celery:
    build: ./backend
    command: celery -A app.workers.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/subtitle
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=subtitle
    volumes:
      - pgdata:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine

volumes:
  pgdata:
  uploads:
```

- [ ] **Step 5: 创建.env.example**

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/subtitle

# Redis
REDIS_URL=redis://localhost:6379/0

# AI服务（可选）
EMBEDDING_API_KEY=
EMBEDDING_API_URL=
SPEECH_API_KEY=
SPEECH_API_URL=

# 匹配权重
KEYWORD_WEIGHT=0.4
SEMANTIC_WEIGHT=0.6
```

- [ ] **Step 6: 测试Docker构建**

Run: `docker-compose build`
Expected: 构建成功

- [ ] **Step 7: 提交**

```bash
git add backend/Dockerfile frontend/Dockerfile nginx/ docker-compose.yml .env.example
git commit -m "feat: add Docker configuration for deployment"
```

---

## Task 19: README文档

**Files:**
- Create: `README.md`

- [ ] **Step 1: 创建README.md**

```markdown
# AI 字幕分析与素材匹配平台

一个轻量化的视频制作辅助平台，完成"字幕输入→语义分段→素材匹配→人工调整→结果保存"的业务闭环。

## 功能特性

- ✅ 字幕文本粘贴输入
- ✅ 视频/音频上传 + 语音识别
- ✅ 异步任务处理 + 进度展示
- ✅ 字幕语义分段
- ✅ 关键词提取
- ✅ 素材上传与管理
- ✅ 混合匹配（关键词+语义）
- ✅ 匹配理由展示
- ✅ 人工替换素材
- ✅ 结果持久化（刷新后保留）

## 技术栈

- **前端**: Vue3 + TypeScript + Element Plus
- **后端**: FastAPI + Python
- **数据库**: PostgreSQL
- **任务队列**: Redis + Celery
- **AI匹配**: 关键词 + Embedding混合

## 快速开始

### 环境要求

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### 使用Docker部署

```bash
# 克隆项目
git clone <repository-url>
cd subtitle-platform

# 启动服务
docker-compose up -d

# 访问应用
http://localhost
```

### 本地开发

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

## 项目结构

```
project/
├── backend/          # FastAPI后端
│   ├── app/         # 应用代码
│   ├── tests/       # 测试
│   └── alembic/     # 数据库迁移
├── frontend/        # Vue3前端
│   └── src/        # 源代码
├── nginx/           # Nginx配置
└── docker-compose.yml
```

## API接口

- `POST /api/tasks` - 创建任务
- `GET /api/tasks/{id}` - 获取任务状态
- `GET /api/tasks/{id}/segments` - 获取字幕片段
- `PUT /api/tasks/{id}/segments/{segment_id}` - 更新片段
- `POST /api/media` - 上传素材
- `GET /api/media` - 获取素材列表

## 配置说明

复制 `.env.example` 为 `.env`，配置以下环境变量：

- `DATABASE_URL` - 数据库连接
- `REDIS_URL` - Redis连接
- `EMBEDDING_API_KEY` - Embedding API密钥（可选）
- `SPEECH_API_KEY` - 语音识别API密钥（可选）

## 已知问题

1. Embedding API需要配置，否则使用伪向量
2. 语音识别需要配置API密钥
3. 不支持视频时间轴预览

## 后续优化

- [ ] 拖拽调整字幕顺序
- [ ] AI自动生成素材标签
- [ ] 视频预览功能
- [ ] 更多语音识别服务支持

## License

MIT
```

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: add README with setup instructions"
```

---

## Task 20: 数据库初始化与演示数据

**Files:**
- Create: `backend/scripts/init_db.py`
- Create: `backend/scripts/seed_demo_data.py`

- [ ] **Step 1: 创建init_db.py**

```python
import asyncio
from app.database import engine, Base
from app.models import Task, SubtitleSegment, Media, MatchResult

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully")

if __name__ == "__main__":
    asyncio.run(init_db())
```

- [ ] **Step 2: 创建seed_demo_data.py**

```python
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
```

- [ ] **Step 3: 测试脚本**

Run: `cd backend && python scripts/init_db.py`
Expected: Database tables created successfully

- [ ] **Step 4: 提交**

```bash
git add backend/scripts/
git commit -m "feat: add database initialization and demo data scripts"
```

---

## 实现计划完成

**总计任务数**: 20个任务  
**预计工时**: 2-3天  
**核心闭环覆盖**: ✅ 完整

### 任务依赖关系

```
Task 1 (后端初始化)
  ↓
Task 2 (数据库模型) → Task 3 (Schemas)
  ↓
Task 4 (素材服务) → Task 5 (字幕服务) → Task 6 (Embedding)
  ↓
Task 7 (匹配服务)
  ↓
Task 8 (任务API) → Task 9 (素材API) → Task 10 (Celery)
  ↓
Task 11 (语音识别) → Task 12 (Alembic)
  ↓
Task 13 (前端初始化) → Task 14 (API服务)
  ↓
Task 15 (任务列表) → Task 16 (任务详情)
  ↓
Task 17 (素材库)
  ↓
Task 18 (Docker) → Task 19 (README) → Task 20 (初始化)
```

### 加分项实现情况

- ✅ 混合匹配（关键词+语义）
- ✅ 匹配理由展示
- ✅ 任务失败重试
- ✅ 演示素材预置（10个）
- ⏳ 拖拽调整顺序（Task 16中预留）
- ⏳ AI自动生成标签（可扩展）

---

*计划创建时间: 2026-07-15*
*状态: 待执行*
