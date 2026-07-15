# AI 字幕分析与素材匹配平台 - 技术文档

> 本文档详细介绍了项目的技术架构、实现原理和开发指南，适合学习和参考。

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [技术栈详解](#3-技术栈详解)
4. [数据库设计](#4-数据库设计)
5. [后端实现](#5-后端实现)
6. [前端实现](#6-前端实现)
7. [AI匹配算法](#7-ai匹配算法)
8. [部署指南](#8-部署指南)
9. [开发指南](#9-开发指南)

---

## 1. 项目概述

### 1.1 业务目标

开发一个轻量化的视频制作辅助平台，完成"内容输入→字幕处理→素材匹配→人工调整→结果保存"的业务闭环。

### 1.2 核心功能

```
┌─────────────────────────────────────────────────────────────┐
│                      核心业务流程                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐│
│  │ 内容输入 │ → │ 字幕处理 │ → │ 素材匹配 │ → │ 人工调整 ││
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘│
│       │              │              │              │        │
│       ↓              ↓              ↓              ↓        │
│  • 文本粘贴     • 语义分段     • 关键词匹配   • 编辑字幕   │
│  • 文件上传     • 关键词提取   • 语义匹配     • 替换素材   │
│  • 语音识别     • Embedding    • 混合排序     • 保存结果   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 技术亮点

| 技术点 | 实现方案 | 说明 |
|--------|---------|------|
| **语义分段** | 正则表达式 + 语义分析 | 按句子自动分段 |
| **关键词提取** | jieba分词 | 中文关键词提取 |
| **向量化** | HuggingFace TEI | bge-large-zh-v1.5模型 |
| **向量检索** | Qdrant | 专业向量数据库 |
| **混合匹配** | 关键词+语义 | 加权融合排序 |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户界面层                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Vue3 + Element Plus                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │ 任务列表 │  │ 新建任务 │  │ 任务详情 │  │ 素材库   │       │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ↓ HTTP                              │
├─────────────────────────────────────────────────────────────────────────┤
│                           服务层                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Nginx 反向代理                                │   │
│  │              静态资源 + API转发                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ↓                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI 应用服务                              │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │ 任务API  │  │ 素材API  │  │ 识别API  │  │ 匹配服务 │       │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│          ┌─────────────────────────┼─────────────────────────┐         │
│          ↓                         ↓                         ↓         │
├─────────────────────────────────────────────────────────────────────────┤
│                           数据层                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  PostgreSQL  │  │    Redis     │  │    Qdrant    │                 │
│  │  关系数据    │  │  缓存/队列   │  │  向量检索    │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                           AI服务层                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  HuggingFace │  │  小米MiMo    │  │   Celery     │                 │
│  │  TEI (Embed) │  │  ASR (语音)  │  │  异步任务    │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
用户上传文件
    │
    ├─→ 文件保存到本地/云存储
    │
    ├─→ 创建任务记录 (PostgreSQL)
    │
    ├─→ 异步处理 (Celery)
    │       │
    │       ├─→ 语音识别 (MiMo ASR)
    │       │       │
    │       │       └─→ 返回字幕文本
    │       │
    │       ├─→ 语义分段
    │       │       │
    │       │       └─→ 生成字幕片段列表
    │       │
    │       ├─→ 关键词提取
    │       │       │
    │       │       └─→ 为每个片段提取关键词
    │       │
    │       └─→ 向量化 (TEI)
    │               │
    │               └─→ 生成embedding向量
    │
    ├─→ 素材匹配 (Qdrant)
    │       │
    │       ├─→ 向量检索 (语义匹配)
    │       │
    │       ├─→ 关键词匹配
    │       │
    │       └─→ 混合排序 → Top3
    │
    └─→ 返回结果给前端
```

---

## 3. 技术栈详解

### 3.1 后端技术栈

| 技术 | 版本 | 用途 | 学习资源 |
|------|------|------|---------|
| **Python** | 3.11+ | 主要编程语言 | https://docs.python.org/zh-cn/3/ |
| **FastAPI** | 0.104.1 | Web框架 | https://fastapi.tiangolo.com/zh/ |
| **SQLAlchemy** | 2.0.23 | ORM框架 | https://docs.sqlalchemy.org/ |
| **Alembic** | 1.13.0 | 数据库迁移 | https://alembic.sqlalchemy.org/ |
| **Celery** | 5.3.6 | 异步任务队列 | https://docs.celeryq.dev/ |
| **Pydantic** | 2.5.3 | 数据验证 | https://docs.pydantic.dev/ |

### 3.2 前端技术栈

| 技术 | 版本 | 用途 | 学习资源 |
|------|------|------|---------|
| **Vue.js** | 3.4+ | 前端框架 | https://cn.vuejs.org/ |
| **TypeScript** | 5.3+ | 类型系统 | https://www.typescriptlang.org/ |
| **Element Plus** | 2.4+ | UI组件库 | https://element-plus.org/zh-CN/ |
| **Vite** | 5.0+ | 构建工具 | https://cn.vitejs.dev/ |
| **Axios** | 1.6+ | HTTP客户端 | https://axios-http.com/ |

### 3.3 数据库与存储

| 技术 | 用途 | 特点 |
|------|------|------|
| **PostgreSQL** | 关系数据存储 | 支持JSON、数组类型 |
| **Redis** | 缓存、消息队列 | 高性能、支持持久化 |
| **Qdrant** | 向量数据库 | 专为向量检索优化 |

### 3.4 AI服务

| 服务 | 用途 | 部署方式 |
|------|------|---------|
| **HuggingFace TEI** | 文本向量化 | Docker自托管 |
| **bge-large-zh-v1.5** | 中文Embedding模型 | 1024维向量 |
| **小米MiMo ASR** | 语音识别 | 云API |

---

## 4. 数据库设计

### 4.1 ER图

```
┌─────────────────────┐       ┌─────────────────────┐
│       tasks         │       │   subtitle_segments  │
├─────────────────────┤       ├─────────────────────┤
│ id (UUID, PK)       │──1:N──│ id (UUID, PK)       │
│ type (VARCHAR)      │       │ task_id (UUID, FK)   │
│ status (VARCHAR)    │       │ content (TEXT)       │
│ input_text (TEXT)   │       │ keywords (JSON)     │
│ input_file_url (TEXT)│      │ embedding (JSON)    │
│ created_at (TIMESTAMP)      │ sort_order (INT)    │
│ updated_at (TIMESTAMP)      │ selected_media_id   │
└─────────────────────┘       └─────────────────────┘
                                       │
                                       │ N:1
                                       ↓
┌─────────────────────┐       ┌─────────────────────┐
│    match_results    │       │       media         │
├─────────────────────┤       ├─────────────────────┤
│ id (UUID, PK)       │       │ id (UUID, PK)       │
│ segment_id (UUID, FK)│      │ type (VARCHAR)      │
│ media_id (UUID, FK)  │──N:1─│ url (TEXT)          │
│ score (FLOAT)       │       │ name (VARCHAR)      │
│ keyword_score (FLOAT)│      │ tags (JSON)         │
│ semantic_score (FLOAT)      │ keywords (JSON)     │
│ reason (TEXT)       │       │ embedding (JSON)    │
│ rank (INT)          │       │ created_at          │
└─────────────────────┘       └─────────────────────┘
```

### 4.2 表结构详解

#### tasks 表 - 任务表

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL,          -- text/audio/video
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending/processing/completed/failed
    input_text TEXT,                     -- 原始输入文本
    input_file_url TEXT,                 -- 上传的文件URL
    error_message TEXT,                  -- 失败原因
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### subtitle_segments 表 - 字幕片段表

```sql
CREATE TABLE subtitle_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    content TEXT NOT NULL,               -- 字幕文本
    start_time INTEGER,                 -- 开始时间（毫秒）
    end_time INTEGER,                   -- 结束时间（毫秒）
    keywords JSON,                      -- 关键词列表 ["Python", "编程"]
    embedding JSON,                     -- 向量 [0.12, -0.34, ...]
    sort_order INTEGER NOT NULL,        -- 排序顺序
    selected_media_id UUID,             -- 选择的素材ID
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### media 表 - 素材表

```sql
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(10) NOT NULL,          -- image/video
    url TEXT NOT NULL,                  -- 文件URL
    thumbnail_url TEXT,                 -- 缩略图URL
    name VARCHAR(255),                  -- 素材名称
    tags JSON,                          -- 标签 ["科技", "编程"]
    keywords JSON,                      -- 关键词
    embedding JSON,                     -- 向量
    duration INTEGER,                   -- 视频时长（秒）
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### match_results 表 - 匹配结果表

```sql
CREATE TABLE match_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_id UUID REFERENCES subtitle_segments(id) ON DELETE CASCADE,
    media_id UUID REFERENCES media(id) ON DELETE CASCADE,
    score FLOAT,                        -- 综合得分
    keyword_score FLOAT,                -- 关键词匹配分
    semantic_score FLOAT,               -- 语义匹配分
    reason TEXT,                        -- 匹配理由
    rank INTEGER,                       -- 排名
    model VARCHAR(50),                  -- 使用的模型
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. 后端实现

### 5.1 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── api/                 # API接口
│   │   ├── __init__.py
│   │   ├── tasks.py         # 任务API
│   │   ├── media.py         # 素材API
│   │   └── transcribe.py    # 语音识别API
│   ├── models/              # 数据库模型
│   │   ├── task.py
│   │   ├── subtitle_segment.py
│   │   ├── media.py
│   │   └── match_result.py
│   ├── schemas/             # Pydantic数据模型
│   │   ├── task.py
│   │   ├── subtitle_segment.py
│   │   ├── media.py
│   │   └── match_result.py
│   ├── services/            # 业务服务
│   │   ├── subtitle_service.py      # 字幕处理
│   │   ├── media_service.py         # 素材管理
│   │   ├── matching_service.py      # 混合匹配
│   │   ├── embedding_service.py     # TEI客户端
│   │   ├── qdrant_service.py        # Qdrant向量服务
│   │   └── transcription_service.py # 语音识别
│   └── workers/             # Celery任务
│       ├── celery_app.py
│       └── tasks.py
├── tests/                   # 测试
├── alembic/                 # 数据库迁移
└── scripts/                 # 脚本
```

### 5.2 核心代码解析

#### 5.2.1 FastAPI应用入口 (main.py)

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.services.qdrant_service import qdrant_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化Qdrant集合
    await qdrant_service.ensure_collections()
    yield
    # 关闭时清理连接
    await qdrant_service.close()

app = FastAPI(
    title="AI字幕分析平台",
    lifespan=lifespan
)
```

**学习点：**
- 使用 `asynccontextmanager` 管理应用生命周期
- 在启动时初始化外部服务连接
- 在关闭时清理资源

#### 5.2.2 数据库连接 (database.py)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# 创建异步引擎
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# 创建会话工厂
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 声明基类
class Base(DeclarativeBase):
    pass

# 依赖注入：获取数据库会话
async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**学习点：**
- 使用 `create_async_engine` 支持异步数据库操作
- 使用 `async_sessionmaker` 创建会话工厂
- 依赖注入模式管理数据库会话
- 异常处理：提交失败时回滚

#### 5.2.3 Embedding服务 (embedding_service.py)

```python
import httpx

class TextEmbeddingsInferenceEmbeddings:
    """HuggingFace TEI 客户端"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def aembed_query(self, text: str) -> list[float]:
        """获取单个文本的embedding"""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/embed",
                json={"inputs": [text]}
            )
            response.raise_for_status()
            data = response.json()
            return data[0]  # 返回1024维向量

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量获取embedding"""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/embed",
                json={"inputs": texts}
            )
            response.raise_for_status()
            return response.json()
```

**学习点：**
- 使用 `httpx` 进行异步HTTP请求
- TEI API格式：POST `/embed`，body为 `{"inputs": ["text1", "text2"]}`
- 返回1024维向量（bge-large-zh-v1.5模型）
- 批量处理提高效率

#### 5.2.4 Qdrant向量服务 (qdrant_service.py)

```python
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

class QdrantService:
    def __init__(self):
        self.client = AsyncQdrantClient(url=settings.QDRANT_URL)

    async def ensure_collections(self):
        """确保集合存在"""
        # 字幕片段集合
        if not await self.client.collection_exists("subtitle_segments"):
            await self.client.create_collection(
                collection_name="subtitle_segments",
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )

    async def search_similar_media(self, query_embedding, score_threshold=0.6, limit=3):
        """搜索相似素材"""
        result = await self.client.query_points(
            collection_name="media_items",
            query=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        return [{"media_id": p.id, "score": p.score} for p in result.points]
```

**学习点：**
- Qdrant使用余弦相似度（COSINE）
- 向量维度为1024（与bge-large-zh-v1.5匹配）
- `score_threshold` 设置相似度阈值
- `limit` 返回最相似的N个结果

#### 5.2.5 混合匹配服务 (matching_service.py)

```python
class MatchingService:
    def keyword_match(self, segment_keywords, media_tags):
        """关键词匹配（Jaccard相似度）"""
        intersection = set(segment_keywords) & set(media_tags)
        union = set(segment_keywords) | set(media_tags)
        return len(intersection) / len(union) if union else 0.0

    async def match_segment(self, segment_id):
        """混合匹配"""
        # 1. 从Qdrant搜索相似素材（向量检索）
        similar_media = await qdrant_service.search_similar_media(
            query_embedding=segment.embedding,
            score_threshold=0.5,
            limit=10
        )

        # 2. 计算混合分数
        for item in similar_media:
            # 关键词匹配
            kw_score = self.keyword_match(segment.keywords, media.tags)

            # 语义匹配（来自Qdrant）
            sem_score = item["score"]

            # 混合分数 = 0.4 * 关键词 + 0.6 * 语义
            total_score = 0.4 * kw_score + 0.6 * sem_score
```

**学习点：**
- Jaccard相似度：交集/并集
- 混合评分公式：`score = α * keyword_score + β * semantic_score`
- 优先使用向量检索，降级到本地计算

---

## 6. 前端实现

### 6.1 项目结构

```
frontend/
├── src/
│   ├── App.vue              # 根组件
│   ├── main.ts              # 入口文件
│   ├── router/
│   │   └── index.ts         # 路由配置
│   ├── views/               # 页面组件
│   │   ├── TaskList.vue     # 任务列表
│   │   ├── TaskNew.vue      # 新建任务
│   │   ├── TaskDetail.vue   # 任务详情
│   │   └── MediaLibrary.vue # 素材库
│   ├── components/          # 公共组件
│   │   ├── SubtitleSegment.vue  # 字幕片段
│   │   ├── MatchResult.vue      # 匹配结果
│   │   └── MediaCard.vue        # 素材卡片
│   ├── api/
│   │   └── index.ts         # API调用
│   └── types/
│       └── index.ts         # TypeScript类型
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### 6.2 核心代码解析

#### 6.2.1 API调用 (api/index.ts)

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 任务API
export const taskApi = {
  // 获取任务列表
  list(params?: { skip?: number; limit?: number }) {
    return api.get<Task[]>('/tasks', { params })
  },

  // 创建任务
  create(data: { type: string; content?: string }) {
    return api.post<Task>('/tasks', data)
  },

  // 获取任务状态
  getStatus(taskId: string) {
    return api.get(`/tasks/${taskId}`)
  },

  // 获取字幕片段
  getSegments(taskId: string) {
    return api.get(`/tasks/${taskId}/segments`)
  },

  // 更新片段
  updateSegment(taskId: string, segmentId: string, data: Partial<SubtitleSegment>) {
    return api.put(`/tasks/${taskId}/segments/${segmentId}`, data)
  }
}
```

**学习点：**
- 使用 `axios` 封装HTTP请求
- TypeScript类型定义提高代码安全性
- RESTful API设计规范

#### 6.2.2 路由配置 (router/index.ts)

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'TaskList',
      component: () => import('../views/TaskList.vue')  // 懒加载
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
```

**学习点：**
- 使用 `createWebHistory` 支持HTML5 History模式
- 路由懒加载减少初始加载时间
- 动态路由参数 `:id`

#### 6.2.3 任务列表页 (TaskList.vue)

```vue
<template>
  <div class="task-list">
    <el-button type="primary" @click="$router.push('/tasks/new')">
      新建任务
    </el-button>

    <el-table :data="tasks" v-loading="loading">
      <el-table-column prop="id" label="任务ID" />
      <el-table-column prop="type" label="类型">
        <template #default="{ row }">
          <el-tag :type="getTypeColor(row.type)">
            {{ getTypeName(row.type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusName(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button @click="viewTask(row.id)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { taskApi } from '../api'

const tasks = ref<Task[]>([])
const loading = ref(false)

const loadTasks = async () => {
  loading.value = true
  try {
    const { data } = await taskApi.list()
    tasks.value = data
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTasks()
})
</script>
```

**学习点：**
- Vue 3 Composition API
- Element Plus 组件使用
- 响应式数据 `ref`
- 生命周期钩子 `onMounted`
- 插槽 `template #default` 自定义列内容

---

## 7. AI匹配算法

### 7.1 算法流程

```
输入: 字幕片段 "今天我们来学习Python编程基础"
              │
              ↓
┌─────────────────────────────────────────┐
│  Step 1: 关键词提取                       │
│  使用正则表达式提取中文词汇和英文单词      │
│  结果: ["Python", "编程", "学习"]         │
└─────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│  Step 2: 向量化                          │
│  使用bge-large-zh-v1.5模型生成1024维向量  │
│  结果: [0.12, -0.34, 0.56, ...]         │
└─────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│  Step 3: 向量检索 (Qdrant)               │
│  搜索最相似的素材（余弦相似度 > 0.6）     │
│  结果: [{media_id, score}, ...]          │
└─────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│  Step 4: 关键词匹配                      │
│  计算字幕关键词与素材标签的Jaccard相似度   │
│  结果: 0.5 (1个共同词 / 2个总词)         │
└─────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│  Step 5: 混合排序                        │
│  score = 0.4 * keyword + 0.6 * semantic  │
│  结果: 排序后返回Top3                    │
└─────────────────────────────────────────┘
```

### 7.2 关键词匹配

```python
def keyword_match(segment_keywords: list, media_tags: list) -> float:
    """
    Jaccard相似度计算

    公式: |A ∩ B| / |A ∪ B|

    示例:
    segment_keywords = ["Python", "编程", "学习"]
    media_tags = ["Python", "代码", "开发"]

    交集 = {"Python"} → 1
    并集 = {"Python", "编程", "学习", "代码", "开发"} → 5
    相似度 = 1 / 5 = 0.2
    """
    intersection = set(segment_keywords) & set(media_tags)
    union = set(segment_keywords) | set(media_tags)
    return len(intersection) / len(union) if union else 0.0
```

### 7.3 语义匹配

```python
def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    余弦相似度计算

    公式: (A · B) / (||A|| * ||B||)

    衡量两个向量的方向相似性，与长度无关。
    结果范围: [-1, 1]，越接近1越相似。
    """
    import numpy as np
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

### 7.4 混合评分

```python
def hybrid_score(keyword_score: float, semantic_score: float) -> float:
    """
    混合评分公式

    score = α * keyword_score + β * semantic_score

    其中:
    - α = 0.4 (关键词权重)
    - β = 0.6 (语义权重)

    为什么语义权重更高？
    - 关键词匹配只能捕捉字面重叠
    - 语义匹配能理解深层含义
    - 例如: "Python" 和 "编程语言" 语义相关但关键词不重叠
    """
    KEYWORD_WEIGHT = 0.4
    SEMANTIC_WEIGHT = 0.6
    return KEYWORD_WEIGHT * keyword_score + SEMANTIC_WEIGHT * semantic_score
```

---

## 8. 部署指南

### 8.1 Docker Compose 配置

```yaml
version: '3.8'

services:
  # 前端
  frontend:
    build: ./frontend
    ports:
      - "80:80"

  # 后端API
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/subtitle
      - REDIS_URL=redis://redis:6379/0
      - TEI_URL=http://tei:80
      - QDRANT_URL=http://qdrant:6333

  # 异步任务
  celery:
    build: ./backend
    command: celery -A app.workers.celery_app worker

  # Embedding服务
  tei:
    image: ghcr.io/huggingface/text-embeddings-inference:cpu-1.8
    command: --model-id BAAI/bge-large-zh-v1.5
    ports:
      - "8081:80"

  # 向量数据库
  qdrant:
    image: qdrant/qdrant:v1.16
    ports:
      - "6333:6333"

  # 关系数据库
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=subtitle

  # 缓存
  redis:
    image: redis:7-alpine
```

### 8.2 部署命令

```bash
# 1. 克隆代码
git clone <repository-url>
cd subtitle-platform

# 2. 配置环境变量
cp .env.example .env

# 3. 启动所有服务
docker-compose up -d

# 4. 初始化数据库
docker-compose exec api python -c "
from app.database import engine, Base
from app.models import *
import asyncio
asyncio.run(asyncio.ensure_future(
    engine.begin().then(lambda conn: conn.run_sync(Base.metadata.create_all))
))
"

# 5. 导入演示数据
docker-compose exec api python scripts/seed_demo_data.py

# 6. 访问应用
# 前端: http://localhost
# API: http://localhost:8000
```

### 8.3 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 80 | 前端页面 |
| API | 8000 | 后端接口 |
| TEI | 8081 | Embedding服务 |
| Qdrant | 6333 | 向量数据库 |
| PostgreSQL | 5432 | 关系数据库 |
| Redis | 6379 | 缓存 |

---

## 9. 开发指南

### 9.1 本地开发环境

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### 9.2 API接口文档

启动后端后访问: http://localhost:8000/docs

主要接口:

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tasks` | 获取任务列表 |
| POST | `/api/tasks` | 创建任务 |
| GET | `/api/tasks/{id}` | 获取任务状态 |
| GET | `/api/tasks/{id}/segments` | 获取字幕片段 |
| PUT | `/api/tasks/{id}/segments/{segment_id}` | 更新片段 |
| GET | `/api/media` | 获取素材列表 |
| POST | `/api/media` | 上传素材 |

### 9.3 测试

```bash
# 后端测试
cd backend
pytest tests/ -v

# 前端构建检查
cd frontend
npm run build
```

### 9.4 常见问题

#### Q1: 数据库连接失败

```bash
# 检查PostgreSQL是否运行
docker-compose ps db

# 查看日志
docker-compose logs db
```

#### Q2: TEI服务启动慢

首次启动需要下载模型（约1.3GB），请耐心等待。

```bash
# 查看下载进度
docker-compose logs -f tei
```

#### Q3: Qdrant连接失败

```bash
# 检查Qdrant是否运行
curl http://localhost:6333/collections
```

---

## 附录

### A. 环境变量说明

| 变量 | 必需 | 说明 |
|------|------|------|
| `DATABASE_URL` | ✅ | PostgreSQL连接字符串 |
| `REDIS_URL` | ✅ | Redis连接字符串 |
| `TEI_URL` | ✅ | HuggingFace TEI地址 |
| `QDRANT_URL` | ✅ | Qdrant地址 |
| `MIMO_API_KEY` | ⚪ | 小米MiMo API密钥 |
| `MIMO_API_URL` | ⚪ | MiMo API地址 |

### B. 参考资源

- FastAPI文档: https://fastapi.tiangolo.com/zh/
- SQLAlchemy文档: https://docs.sqlalchemy.org/
- Vue.js文档: https://cn.vuejs.org/
- Element Plus文档: https://element-plus.org/zh-CN/
- HuggingFace TEI: https://huggingface.co/docs/text-embeddings-inference
- Qdrant文档: https://qdrant.tech/documentation/

---

*文档生成时间: 2026-07-15*
*版本: 1.0.0*
