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
- **Embedding**: HuggingFace TEI (bge-large-zh-v1.5)
- **向量数据库**: Qdrant
- **AI匹配**: 关键词 + 语义向量混合

## 架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                            │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Vue3)  →  Nginx  →  API (FastAPI)               │
│                                            ↓                │
│                              ┌─────────────┴─────────────┐  │
│                              ↓                           ↓  │
│                     PostgreSQL                    Redis/Celery│
│                              ↓                           ↓  │
│              ┌───────────────┴───────────────┐              │
│              ↓                               ↓              │
│    HuggingFace TEI                    Qdrant Vector DB      │
│    (bge-large-zh-v1.5)               (向量检索)             │
└─────────────────────────────────────────────────────────────┘
```

### Embedding方案

参考 `E:\shangagent\data_agent` 项目，采用相同的技术方案：

| 组件 | 技术 | 说明 |
|------|------|------|
| **Embedding模型** | BAAI/bge-large-zh-v1.5 | 中文语义向量，1024维 |
| **部署方式** | HuggingFace TEI (Docker) | 自托管，端口8081 |
| **向量数据库** | Qdrant v1.16 | 专用于向量存储和检索 |
| **相似度算法** | COSINE | 阈值0.6 |

### 匹配流程

1. **字幕分段** → 提取关键词 → 生成embedding向量
2. **素材上传** → 拼接name+tags → 生成embedding向量
3. **匹配时** → 用Qdrant搜索相似素材（向量检索）→ 结合关键词计算混合分数
4. **降级方案** → TEI/Qdrant不可用时，自动降级到本地计算

## 快速开始

### 环境要求

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### 使用Docker部署（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd subtitle-platform

# 启动所有服务（含TEI和Qdrant）
docker-compose up -d

# 访问应用
http://localhost
```

服务列表：
- 前端: http://localhost
- API: http://localhost:8000
- TEI Embedding: http://localhost:8081
- Qdrant: http://localhost:6333

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

本地开发需要单独启动TEI和Qdrant：

```bash
# 启动TEI (需要GPU或耐心等待CPU推理)
docker run -p 8081:80 ghcr.io/huggingface/text-embeddings-inference:cpu-1.8 \
  --model-id BAAI/bge-large-zh-v1.5

# 启动Qdrant
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.16
```

## 项目结构

```
project/
├── backend/          # FastAPI后端
│   ├── app/
│   │   ├── api/         # API接口
│   │   ├── models/      # 数据库模型
│   │   ├── schemas/     # Pydantic数据模型
│   │   ├── services/    # 业务服务
│   │   │   ├── embedding_service.py  # TEI客户端
│   │   │   ├── qdrant_service.py     # Qdrant向量检索
│   │   │   └── matching_service.py   # 混合匹配
│   │   └── workers/     # Celery任务
│   ├── tests/        # 测试
│   └── alembic/      # 数据库迁移
├── frontend/         # Vue3前端
│   └── src/
├── nginx/            # Nginx配置
└── docker-compose.yml
```

## API接口

- `POST /api/tasks` - 创建任务
- `GET /api/tasks/{id}` - 获取任务状态
- `GET /api/tasks/{id}/segments` - 获取字幕片段
- `PUT /api/tasks/{id}/segments/{segment_id}` - 更新片段
- `POST /api/media` - 上传素材
- `GET /api/media` - 获取素材列表
- `GET /health` - 健康检查
- `GET /info` - 系统信息（TEI/Qdrant连接状态）

## 配置说明

复制 `.env.example` 为 `.env`，配置以下环境变量：

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/subtitle

# Redis
REDIS_URL=redis://localhost:6379/0

# HuggingFace TEI
TEI_URL=http://localhost:8081

# Qdrant
QDRANT_URL=http://localhost:6333
```

## 已知问题

1. TEI首次启动需要下载模型（约1.3GB），请耐心等待
2. 语音识别需要配置API密钥
3. 不支持视频时间轴预览

## 后续优化

- [ ] 拖拽调整字幕顺序
- [ ] AI自动生成素材标签
- [ ] 视频预览功能
- [ ] 更多语音识别服务支持


## License

MIT
