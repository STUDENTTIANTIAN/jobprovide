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