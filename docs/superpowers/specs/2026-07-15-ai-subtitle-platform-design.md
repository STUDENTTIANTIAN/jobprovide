# AI 字幕分析与素材匹配平台 - 技术设计文档

## 1. 项目概述

### 1.1 业务目标

开发一个轻量化的视频制作辅助平台，完成"内容输入→字幕处理→素材匹配→人工调整→结果保存"的业务闭环。

### 1.2 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue3 + TypeScript + Element Plus | SPA单页应用 |
| 后端 | FastAPI + Python | 异步高性能 |
| 数据库 | PostgreSQL | 结构化数据 + JSONB |
| 任务队列 | Redis + Celery | 异步任务处理 |
| 文件存储 | 本地磁盘 / 云OSS | 素材文件存储 |
| 语音识别 | 国内语音服务API | 音视频转字幕 |
| AI匹配 | 关键词 + Embedding混合 | 带降级保障 |

### 1.3 架构选择

采用**单体后端 + SPA前端**架构（方案A），原因：
- 2-3天交付时间，开发效率最高
- 云服务器一台即可部署
- FastAPI + Celery + Redis 是Python生态最成熟的异步方案
- 核心闭环优先策略下，简单架构更容易保证稳定性

## 2. 整体架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    阿里云/腾讯云服务器                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Nginx     │  │   FastAPI   │  │   Celery    │        │
│  │  (反向代理) │→│  (API服务)  │  │  (任务队列) │        │
│  │  :80/:443   │  │  :8000      │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         ↓               ↓               ↓                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Vue3 SPA   │  │ PostgreSQL  │  │    Redis    │        │
│  │  (静态文件) │  │  :5432      │  │  :6379      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心数据流

```
用户上传(视频/音频/文本)
        ↓
┌─────────────────────────┐
│  1. 内容输入与任务创建   │
│  - 文件上传 → 异步处理   │
│  - 文本粘贴 → 直接解析   │
└─────────────────────────┘
        ↓
┌─────────────────────────┐
│  2. 字幕处理             │
│  - 语音识别(如需)        │
│  - 语义分段              │
│  - 关键词提取            │
│  - Embedding向量化       │
└─────────────────────────┘
        ↓
┌─────────────────────────┐
│  3. 素材智能匹配         │
│  - 关键词匹配(40%)       │
│  - 语义匹配(60%)         │
│  - 混合排序 → Top3       │
│  - 生成匹配理由          │
└─────────────────────────┘
        ↓
┌─────────────────────────┐
│  4. 人工调整与保存       │
│  - 查看推荐素材          │
│  - 替换/确认素材         │
│  - 拖拽调整顺序(加分)    │
│  - 保存最终结果          │
└─────────────────────────┘
```

## 3. 数据库设计

### 3.1 表结构

```sql
-- 任务表：记录每次字幕处理任务
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL,          -- 'video', 'audio', 'text'
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending/processing/completed/failed
    input_text TEXT,                     -- 原始输入文本（粘贴字幕）
    input_file_url TEXT,                 -- 上传的文件URL
    error_message TEXT,                  -- 失败原因
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 字幕片段表
CREATE TABLE subtitle_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    content TEXT NOT NULL,               -- 字幕文本
    start_time DECIMAL(10,3),            -- 开始时间（秒）
    end_time DECIMAL(10,3),              -- 结束时间（秒）
    keywords JSONB,                      -- 提取的关键词 ["Python", "编程"]
    embedding FLOAT8[],                  -- 向量嵌入（1536维）
    sort_order INT NOT NULL,             -- 排序顺序
    selected_media_id UUID,              -- 最终选择的素材
    created_at TIMESTAMP DEFAULT NOW()
);

-- 素材表
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(10) NOT NULL,           -- 'image', 'video'
    url TEXT NOT NULL,                   -- 文件URL
    thumbnail_url TEXT,                  -- 缩略图URL
    name VARCHAR(255),                   -- 素材名称
    tags JSONB,                          -- 人工标签 ["科技", "编程"]
    keywords JSONB,                      -- AI生成关键词
    embedding FLOAT8[],                  -- 向量嵌入
    duration DECIMAL(10,3),              -- 视频时长（秒）
    created_at TIMESTAMP DEFAULT NOW()
);

-- 匹配结果表
CREATE TABLE match_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_id UUID REFERENCES subtitle_segments(id) ON DELETE CASCADE,
    media_id UUID REFERENCES media(id) ON DELETE CASCADE,
    score DECIMAL(5,4),                  -- 综合得分 0-1
    keyword_score DECIMAL(5,4),          -- 关键词匹配分
    semantic_score DECIMAL(5,4),         -- 语义匹配分
    reason TEXT,                         -- 匹配理由
    rank INT,                            -- 排名 1-3
    model VARCHAR(50),                   -- 使用的模型
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3.2 设计要点

1. **task_id 贯穿全流程** — 字幕片段和匹配结果都关联到任务，方便追溯
2. **embedding 字段** — 用于向量相似度查询，PostgreSQL支持数组类型
3. **match_results 保存匹配理由** — 满足题目"不能只给出无法解释的分数"的要求
4. **ON DELETE CASCADE** — 删除任务时自动清理关联数据

## 4. API 接口设计

### 4.1 字幕任务接口

```python
# 创建任务
POST /api/tasks
Body: { "type": "text", "content": "字幕文本..." }
   或 { "type": "video", "file": <上传文件> }
Response: { "task_id": "uuid", "status": "processing" }

# 获取任务状态
GET /api/tasks/{task_id}
Response: { "task_id", "status", "progress": 75, "segments_count": 5 }

# 获取任务的字幕片段
GET /api/tasks/{task_id}/segments
Response: [{ "id", "content", "keywords", "sort_order", "selected_media_id", "matches": [...] }]

# 更新字幕片段（修改文本/顺序/选择素材）
PUT /api/tasks/{task_id}/segments/{segment_id}
Body: { "content": "修改后的文本", "sort_order": 2, "selected_media_id": "uuid" }

# 重新执行任务
POST /api/tasks/{task_id}/retry
Response: { "task_id", "status": "processing" }
```

### 4.2 素材管理接口

```python
# 获取素材列表（支持搜索）
GET /api/media?keyword=科技&page=1&size=20
Response: { "items": [...], "total": 100 }

# 上传素材
POST /api/media
Body: multipart/form-data { "file", "name", "tags": ["科技"] }
Response: { "media_id": "uuid", "url": "..." }

# AI自动生成标签
POST /api/media/{media_id}/auto-tag
Response: { "tags": ["编程", "代码", "Python"] }

# 删除素材
DELETE /api/media/{media_id}
```

### 4.3 语音识别接口

```python
# 提交语音识别任务
POST /api/transcribe
Body: multipart/form-data { "file": <音频/视频文件> }
Response: { "task_id": "uuid", "status": "processing" }

# 获取识别结果
GET /api/transcribe/{task_id}
Response: { "status": "completed", "text": "识别出的字幕文本", "segments": [...] }
```

### 4.4 设计要点

1. **RESTful 风格** — 标准CRUD接口，易于理解和调试
2. **异步任务模式** — 上传文件后返回task_id，前端轮询或WebSocket获取进度
3. **匹配结果内嵌** — 获取片段时直接返回Top3匹配素材，减少请求次数
4. **幂等设计** — retry接口支持重复执行，已完成的任务不重复处理

## 5. 前端页面设计

### 5.1 页面结构

```
┌─────────────────────────────────────────────────────────────┐
│  顶部导航栏：Logo │ 字幕任务 │ 素材库 │                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              主内容区（路由视图）                     │   │
│  │                                                     │   │
│  │  /tasks          → 任务列表页                       │   │
│  │  /tasks/new      → 新建任务页                       │   │
│  │  /tasks/:id      → 任务详情页（字幕+匹配）          │   │
│  │  /media          → 素材库页面                       │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 核心页面：任务详情页

```
┌─────────────────────────────────────────────────────────────┐
│  任务详情 - 任务ID: abc123  状态: ✅ 已完成                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ 字幕片段列表 ──────────────────────────────────────┐   │
│  │  [1] "今天我们来学习Python编程基础"                   │   │
│  │      关键词: Python, 编程, 学习                       │   │
│  │      ┌─ 推荐素材 ─────────────────────────────────┐ │   │
│  │      │ [选中] 🖼️ python代码图  匹配度:92%  关键词匹配│ │   │
│  │      │        🖼️ 编程教学图   匹配度:85%  语义相关  │ │   │
│  │      │        🖼️ 代码编辑器   匹配度:78%  主题相关  │ │   │
│  │      └─────────────────────────────────────────────┘ │   │
│  ├───────────────────────────────────────────────────────┤   │
│  │  [2] "首先安装Python开发环境"                         │   │
│  │      关键词: Python, 安装, 环境                       │   │
│  │      ┌─ 推荐素材 ─────────────────────────────────┐ │   │
│  │      │ [选中] 🖼️ 终端安装图   匹配度:88%  关键词匹配│ │   │
│  │      │        🖼️ 环境配置图   匹配度:82%  语义相关  │ │   │
│  │      │        🖼️ 命令行界面   匹配度:75%  主题相关  │ │   │
│  │      └─────────────────────────────────────────────┘ │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                             │
│  [保存结果]  [导出字幕]                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 交互设计

1. **字幕编辑** — 点击文本可直接编辑，支持拖拽调整顺序（加分项）
2. **素材替换** — 点击推荐素材可展开素材库选择器，支持搜索替换
3. **匹配理由** — 每个推荐素材下方显示匹配原因（关键词匹配/语义相似度）
4. **状态反馈** — 任务处理中显示进度条，失败显示错误信息和重试按钮

## 6. AI 匹配策略

### 6.1 混合匹配流程

```
字幕片段文本: "今天我们来学习Python编程基础"
        ↓
┌─────────────────────────┐
│  1. 提取关键词           │
│  [Python, 编程, 学习]   │
└─────────────────────────┘
        ↓
┌─────────────────────────┐
│  2. 生成文本Embedding    │
│  (1536维向量)           │
└─────────────────────────┘
        ↓
   ┌────┴────┐
   ↓         ↓
┌──────────┐ ┌──────────┐
│关键词匹配│ │语义匹配  │
│ (40%)    │ │ (60%)    │
└──────────┘ └──────────┘
   ↓         ↓
   └────┬────┘
        ↓
┌─────────────────────────┐
│  3. 混合打分 + 排序      │
│  score = 0.4*kw + 0.6*sem│
└─────────────────────────┘
        ↓
┌─────────────────────────┐
│  4. 返回 Top3 + 理由     │
└─────────────────────────┘
```

### 6.2 关键词匹配

使用Jaccard相似度计算关键词匹配分数：

```python
def keyword_match(segment_keywords: list, media_tags: list) -> float:
    if not segment_keywords or not media_tags:
        return 0.0
    intersection = set(segment_keywords) & set(media_tags)
    union = set(segment_keywords) | set(media_tags)
    return len(intersection) / len(union)
```

### 6.3 语义匹配

使用余弦相似度计算语义匹配分数：

```python
def semantic_match(segment_embedding: list, media_embedding: list) -> float:
    dot_product = np.dot(segment_embedding, media_embedding)
    norm_a = np.linalg.norm(segment_embedding)
    norm_b = np.linalg.norm(media_embedding)
    return dot_product / (norm_a * norm_b)
```

### 6.4 匹配理由生成

```python
def generate_reason(matched_keywords, semantic_score):
    reasons = []
    if matched_keywords:
        reasons.append(f"关键词匹配: {', '.join(matched_keywords)}")
    if semantic_score > 0.8:
        reasons.append("语义高度相关")
    elif semantic_score > 0.6:
        reasons.append("语义相关")
    return " | ".join(reasons)
```

### 6.5 降级方案

```python
async def match_with_fallback(segment):
    try:
        return await hybrid_match(segment)
    except Exception as e:
        logger.warning(f"AI匹配失败，降级到关键词: {e}")
        return await keyword_only_match(segment)
```

## 7. 异常处理与稳定性

### 7.1 错误处理矩阵

| 场景 | 处理方式 | 用户反馈 |
|------|---------|---------|
| 文件上传失败 | 重试3次，记录日志 | "上传失败，请检查网络后重试" |
| 语音识别超时 | 任务标记失败，支持重试 | "识别超时，请重试" |
| AI匹配服务不可用 | 降级到关键词匹配 | "语义匹配暂时不可用，已使用关键词匹配" |
| 数据库连接失败 | 重试+报警 | "系统繁忙，请稍后重试" |
| 文件格式不支持 | 前端校验+后端校验 | "不支持的文件格式，请上传mp4/wav/mp3" |

### 7.2 任务状态机

```
pending → processing → completed
                  ↓
                failed → (retry) → processing
```

### 7.3 幂等性设计

```python
@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str):
    task = await db.get_task(task_id)
    if task.status == "completed":
        return {"message": "任务已完成", "task_id": task_id}
    if task.status == "processing":
        return {"message": "任务处理中", "task_id": task_id}
    await task_queue.retry(task_id)
```

### 7.4 断网恢复

```python
# 前端：自动重连
const socket = io(SOCKET_URL, {
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
});

socket.on('connect', () => {
    resubscribeToActiveTasks();
});
```

## 8. 部署方案

### 8.1 Docker Compose

```yaml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html

  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/subtitle
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  celery:
    build: ./backend
    command: celery -A app.worker worker
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/subtitle
      - REDIS_URL=redis://redis:6379

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
```

### 8.2 部署步骤

1. **服务器准备** — 安装Docker和Docker Compose
2. **代码部署** — git clone + 配置环境变量
3. **构建启动** — `docker-compose up -d`
4. **初始化** — 运行数据库迁移 + 导入演示素材
5. **域名配置** — Nginx配置 + SSL证书（可选）

## 9. 功能范围

### 9.1 核心功能（必须）

- [ ] 字幕文本粘贴输入
- [ ] 视频/音频上传 + 语音识别
- [ ] 异步任务处理 + 进度展示
- [ ] 字幕语义分段
- [ ] 关键词提取
- [ ] 素材上传与管理
- [ ] 混合匹配（关键词+语义）
- [ ] 匹配理由展示
- [ ] 人工替换素材
- [ ] 结果持久化（刷新后保留）

### 9.2 加分项（视时间）

- [ ] 拖拽调整字幕顺序
- [ ] AI自动生成素材标签
- [ ] 向量相似度 + 关键词混合排序
- [ ] 任务失败重试
- [ ] 演示素材预置（10+）

## 10. 已知限制

1. **Embedding方案** — 需要Embedding API（如OpenAI或国内服务），否则降级到纯关键词匹配
2. **语音识别** — 依赖国内语音服务API，需要配置API密钥
3. **视频预览** — 不支持视频时间轴预览（可作为后续优化）
4. **并发处理** — 单体架构并发能力有限，但对演示场景足够

---

*文档创建时间: 2026-07-15*
*状态: 待审核*
