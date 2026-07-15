# 云端部署指南

## 部署清单

### 1. 服务器要求

| 资源 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **CPU** | 4核 | 8核 |
| **内存** | 8GB | 16GB |
| **磁盘** | 50GB SSD | 100GB SSD |
| **系统** | Ubuntu 20.04+ / CentOS 7+ |
| **Docker** | 20.10+ |
| **Docker Compose** | 2.0+ |

### 2. 服务组件

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 80 | Vue3 SPA |
| API | 8000 | FastAPI后端 |
| TEI | 8081 | HuggingFace Embedding (bge-large-zh-v1.5) |
| Qdrant | 6333/6334 | 向量数据库 |
| PostgreSQL | 5432 | 关系型数据库 |
| Redis | 6379 | 缓存/消息队列 |

### 3. 部署步骤

#### 3.1 安装Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo apt install docker-compose-plugin
```

#### 3.2 上传代码

```bash
# 在本地打包
cd D:\agent\project
tar -czf subtitle-platform.tar.gz --exclude=node_modules --exclude=__pycache__ .

# 上传到服务器
scp subtitle-platform.tar.gz user@your-server:/home/user/
```

#### 3.3 服务器部署

```bash
# 解压代码
ssh user@your-server
cd /home/user
tar -xzf subtitle-platform.tar.gz
cd project

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库密码等

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

#### 3.4 初始化数据库

```bash
# 进入API容器
docker-compose exec api bash

# 运行数据库迁移
alembic upgrade head

# 导入演示数据
python scripts/seed_demo_data.py

# 退出容器
exit
```

#### 3.5 验证部署

```bash
# 检查服务状态
curl http://localhost/health
curl http://localhost/info

# 检查TEI服务
curl http://localhost:8081/health

# 检查Qdrant服务
curl http://localhost:6333/collections
```

### 4. 环境变量配置

编辑 `.env` 文件：

```env
# 数据库（修改密码）
DATABASE_URL=postgresql+asyncpg://user:YOUR_PASSWORD@db:5432/subtitle

# Redis
REDIS_URL=redis://redis:6379/0

# TEI (内部网络)
TEI_URL=http://tei:80

# Qdrant (内部网络)
QDRANT_URL=http://qdrant:6333

# 语音识别（可选）
SPEECH_API_KEY=your-api-key
SPEECH_API_URL=your-api-url
```

### 5. Docker Compose 配置

修改 `docker-compose.yml` 中的密码：

```yaml
services:
  api:
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:YOUR_PASSWORD@db:5432/subtitle

  db:
    environment:
      - POSTGRES_PASSWORD=YOUR_PASSWORD  # 修改这里
```

### 6. 防火墙配置

开放以下端口：

| 端口 | 用途 |
|------|------|
| 80 | HTTP (前端) |
| 443 | HTTPS (可选) |
| 8000 | API (可选，如需直接访问) |

### 7. 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启API
docker-compose restart api

# 查看日志
docker-compose logs -f

# 进入容器
docker-compose exec api bash

# 数据库备份
docker-compose exec db pg_dump -U user subtitle > backup.sql

# 数据库恢复
docker-compose exec db psql -U user subtitle < backup.sql
```

### 8. 性能优化

#### 8.1 TEI优化

如果服务器有GPU，可以使用GPU版本：

```yaml
tei:
  image: ghcr.io/huggingface/text-embeddings-inference:1.5-gpu
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

#### 8.2 Qdrant优化

调整Qdrant内存限制：

```yaml
qdrant:
  environment:
    - QDRANT__STORAGE__OPTIMIZERS__MEMMAP_THRESHOLD_KB=20000
```

### 9. 监控

```bash
# 查看容器资源使用
docker stats

# 查看服务状态
docker-compose ps

# 查看API健康状态
curl http://localhost/health
```

### 10. 故障排查

```bash
# 查看API日志
docker-compose logs api

# 查看TEI日志
docker-compose logs tei

# 查看Qdrant日志
docker-compose logs qdrant

# 检查数据库连接
docker-compose exec api python -c "from app.database import engine; print('DB OK')"
```

## 快速部署脚本

```bash
#!/bin/bash
# deploy.sh

set -e

echo "Starting deployment..."

# 停止旧服务
docker-compose down

# 拉取最新镜像
docker-compose pull

# 启动服务
docker-compose up -d

# 等待服务启动
sleep 30

# 初始化数据库
docker-compose exec -T api alembic upgrade head

echo "Deployment complete!"
echo "Frontend: http://$(hostname -I | awk '{print $1}')"
echo "API: http://$(hostname -I | awk '{print $1}'):8000"
```

## 注意事项

1. **TEI首次启动**：需要下载模型（约1.3GB），请耐心等待
2. **内存占用**：TEI服务约占用2-4GB内存
3. **磁盘空间**：Qdrant向量数据会持续增长，建议定期清理
4. **备份**：定期备份PostgreSQL和Qdrant数据
