# 业务闭环修复实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复AI字幕平台的业务闭环，实现任务创建后自动触发匹配、API返回匹配结果、前端显示推荐素材

**Architecture:** 后端在任务创建并分段后自动调用MatchingService执行匹配，API返回时包含segments和matches数据，前端轮询获取结果并内联展示推荐素材

**Tech Stack:** FastAPI, SQLAlchemy, Vue3, Element Plus

---

## 文件结构

```
backend/app/schemas/
├── subtitle_segment.py      # 修改: 添加matches字段
└── task.py                  # 修改: 添加segments字段

backend/app/services/
└── matching_service.py      # 修改: 添加match_task_segments方法

backend/app/api/
└── tasks.py                 # 修改: 任务创建后自动匹配，返回segments

frontend/src/api/
└── index.ts                 # 修改: 更新getStatus返回类型

frontend/src/views/
└── TaskDetail.vue           # 修改: 从任务详情获取segments

frontend/src/components/
├── SubtitleSegment.vue      # 修改: 显示推荐素材列表
└── MatchResult.vue          # 修改: 优化显示
```

---

## Task 1: 后端Schema变更

**Files:**
- Modify: `backend/app/schemas/subtitle_segment.py`
- Modify: `backend/app/schemas/task.py`

- [ ] **Step 1: 修改SubtitleSegmentResponse添加matches字段**

```python
# backend/app/schemas/subtitle_segment.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# 先导入MatchResultResponse（避免循环导入，在使用时延迟导入）
class SubtitleSegmentResponse(BaseModel):
    id: UUID
    task_id: UUID
    content: str
    start_time: Optional[int]
    end_time: Optional[int]
    keywords: Optional[List[str]]
    sort_order: int
    selected_media_id: Optional[UUID]
    matches: Optional[List[dict]] = None  # 匹配结果列表
    created_at: datetime

    class Config:
        from_attributes = True

class SubtitleSegmentUpdate(BaseModel):
    content: Optional[str]
    sort_order: Optional[int]
    selected_media_id: Optional[UUID]
```

- [ ] **Step 2: 测试导入**

Run: `cd backend && python -c "from app.schemas.subtitle_segment import SubtitleSegmentResponse; print('OK')"`
Expected: OK

- [ ] **Step 3: 提交**

```bash
git add backend/app/schemas/subtitle_segment.py
git commit -m "feat: add matches field to SubtitleSegmentResponse"
```

---

## Task 2: 后端匹配服务添加批量方法

**Files:**
- Modify: `backend/app/services/matching_service.py`

- [ ] **Step 1: 添加match_task_segments方法**

在 `MatchingService` 类末尾添加：

```python
    async def match_task_segments(self, task_id: UUID) -> int:
        """批量匹配任务的所有片段
        
        Returns:
            int: 匹配的片段数量
        """
        from app.models.subtitle_segment import SubtitleSegment
        
        # 获取所有片段
        result = await self.db.execute(
            select(SubtitleSegment)
            .where(SubtitleSegment.task_id == task_id)
            .order_by(SubtitleSegment.sort_order)
        )
        segments = result.scalars().all()
        
        # 为每个片段执行匹配
        matched_count = 0
        for segment in segments:
            try:
                matches = await self.match_segment(segment.id)
                if matches:
                    await self.save_match_results(segment.id, matches)
                    matched_count += 1
            except Exception as e:
                print(f"Match failed for segment {segment.id}: {e}")
                continue
        
        return matched_count
```

- [ ] **Step 2: 测试导入**

Run: `cd backend && python -c "from app.services.matching_service import MatchingService; print('OK')"`
Expected: OK

- [ ] **Step 3: 提交**

```bash
git add backend/app/services/matching_service.py
git commit -m "feat: add match_task_segments batch method"
```

---

## Task 3: 后端API变更 - 任务创建自动匹配

**Files:**
- Modify: `backend/app/api/tasks.py`

- [ ] **Step 1: 修改create_task自动触发匹配**

```python
# backend/app/api/tasks.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.models.task import Task
from app.models.subtitle_segment import SubtitleSegment
from app.models.match_result import MatchResult
from app.schemas.task import TaskCreate, TaskResponse, TaskStatus
from app.schemas.subtitle_segment import SubtitleSegmentResponse
from app.services.subtitle_service import SubtitleService
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    result = await db.execute(
        select(Task)
        .order_by(Task.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    tasks = result.scalars().all()
    return tasks


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

    # 如果是文本类型，直接处理
    if task_data.type == "text" and task_data.content:
        task.status = "processing"
        
        # 1. 分段处理
        subtitle_service = SubtitleService(db)
        await subtitle_service.create_segments(task.id, task_data.content)
        
        # 2. 自动触发匹配
        matching_service = MatchingService(db)
        await matching_service.match_task_segments(task.id)
        
        task.status = "completed"

    return task


@router.get("/{task_id}")
async def get_task_detail(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取任务详情（包含segments和matches）"""
    # 获取任务
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 获取片段及其匹配结果
    segments_result = await db.execute(
        select(SubtitleSegment)
        .where(SubtitleSegment.task_id == task_id)
        .order_by(SubtitleSegment.sort_order)
    )
    segments = segments_result.scalars().all()
    
    segments_with_matches = []
    for segment in segments:
        # 获取该片段的匹配结果
        matches_result = await db.execute(
            select(MatchResult)
            .where(MatchResult.segment_id == segment.id)
            .order_by(MatchResult.rank)
        )
        matches = matches_result.scalars().all()
        
        # 获取素材详情
        matches_data = []
        for match in matches:
            from app.models.media import Media
            media_result = await db.execute(
                select(Media).where(Media.id == match.media_id)
            )
            media = media_result.scalar_one_or_none()
            
            matches_data.append({
                "id": str(match.id),
                "media_id": str(match.media_id),
                "score": match.score,
                "keyword_score": match.keyword_score,
                "semantic_score": match.semantic_score,
                "reason": match.reason,
                "rank": match.rank,
                "media_name": media.name if media else None,
                "media_url": media.url if media else None,
                "media_type": media.type if media else None,
            })
        
        segments_with_matches.append({
            "id": str(segment.id),
            "task_id": str(segment.task_id),
            "content": segment.content,
            "keywords": segment.keywords,
            "sort_order": segment.sort_order,
            "selected_media_id": str(segment.selected_media_id) if segment.selected_media_id else None,
            "matches": matches_data,
            "created_at": segment.created_at.isoformat() if segment.created_at else None,
        })

    return {
        "task_id": str(task.id),
        "type": task.type,
        "status": task.status,
        "input_text": task.input_text,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "segments": segments_with_matches,
    }


@router.get("/{task_id}/segments")
async def get_task_segments(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取任务的字幕片段（包含matches）"""
    # 获取片段
    result = await db.execute(
        select(SubtitleSegment)
        .where(SubtitleSegment.task_id == task_id)
        .order_by(SubtitleSegment.sort_order)
    )
    segments = result.scalars().all()
    
    segments_with_matches = []
    for segment in segments:
        # 获取匹配结果
        matches_result = await db.execute(
            select(MatchResult)
            .where(MatchResult.segment_id == segment.id)
            .order_by(MatchResult.rank)
        )
        matches = matches_result.scalars().all()
        
        matches_data = []
        for match in matches:
            from app.models.media import Media
            media_result = await db.execute(
                select(Media).where(Media.id == match.media_id)
            )
            media = media_result.scalar_one_or_none()
            
            matches_data.append({
                "id": str(match.id),
                "media_id": str(match.media_id),
                "score": match.score,
                "keyword_score": match.keyword_score,
                "semantic_score": match.semantic_score,
                "reason": match.reason,
                "rank": match.rank,
                "media_name": media.name if media else None,
                "media_url": media.url if media else None,
                "media_type": media.type if media else None,
            })
        
        segments_with_matches.append({
            "id": str(segment.id),
            "task_id": str(segment.task_id),
            "content": segment.content,
            "keywords": segment.keywords,
            "sort_order": segment.sort_order,
            "selected_media_id": str(segment.selected_media_id) if segment.selected_media_id else None,
            "matches": matches_data,
            "created_at": segment.created_at.isoformat() if segment.created_at else None,
        })
    
    return segments_with_matches


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


@router.post("/{task_id}/retry")
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
        return {"message": "Task already completed", "task_id": str(task.id)}

    if task.status == "processing":
        return {"message": "Task is processing", "task_id": str(task.id)}

    # 重置状态并重新执行
    task.status = "processing"
    task.error_message = None
    
    # 重新执行匹配
    matching_service = MatchingService(db)
    await matching_service.match_task_segments(task.id)
    
    task.status = "completed"
    
    return {"message": "Task retried", "task_id": str(task.id)}
```

- [ ] **Step 4: 测试导入**

Run: `cd backend && python -c "from app.api.tasks import router; print('OK')"`
Expected: OK

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/tasks.py
git commit -m "feat: add auto-matching and segments in task detail"
```

---

## Task 4: 前端API更新

**Files:**
- Modify: `frontend/src/api/index.ts`

- [ ] **Step 1: 更新getStatus返回类型**

```typescript
// frontend/src/api/index.ts

import axios from 'axios'
import type { Task, SubtitleSegment, Media } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// Task APIs
export const taskApi = {
  list(params?: { skip?: number; limit?: number }) {
    return api.get<Task[]>('/tasks', { params })
  },

  create(data: { type: string; content?: string }) {
    return api.post<Task>('/tasks', data)
  },

  getStatus(taskId: string) {
    return api.get<{
      task_id: string
      type: string
      status: string
      input_text?: string
      error_message?: string
      created_at?: string
      updated_at?: string
      segments?: Array<{
        id: string
        task_id: string
        content: string
        keywords?: string[]
        sort_order: number
        selected_media_id?: string
        matches?: Array<{
          id: string
          media_id: string
          score: number
          keyword_score: number
          semantic_score: number
          reason: string
          rank: number
          media_name?: string
          media_url?: string
          media_type?: string
        }>
      }>
    }>(`/tasks/${taskId}`)
  },

  getSegments(taskId: string) {
    return api.get<Array<{
      id: string
      task_id: string
      content: string
      keywords?: string[]
      sort_order: number
      selected_media_id?: string
      matches?: Array<{
        id: string
        media_id: string
        score: number
        keyword_score: number
        semantic_score: number
        reason: string
        rank: number
        media_name?: string
        media_url?: string
        media_type?: string
      }>
    }>>(`/tasks/${taskId}/segments`)
  },

  updateSegment(taskId: string, segmentId: string, data: { content?: string; sort_order?: number; selected_media_id?: string }) {
    return api.put(`/tasks/${taskId}/segments/${segmentId}`, data)
  },

  retry(taskId: string) {
    return api.post(`/tasks/${taskId}/retry`)
  }
}

// Media APIs
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

// Transcription APIs
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

- [ ] **Step 2: 测试构建**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 3: 提交**

```bash
git add frontend/src/api/index.ts
git commit -m "feat: update API types for segments and matches"
```

---

## Task 5: 前端TaskDetail.vue重构

**Files:**
- Modify: `frontend/src/views/TaskDetail.vue`

- [ ] **Step 1: 重构TaskDetail.vue**

```vue
<template>
  <div class="task-detail">
    <div class="task-header">
      <h2>任务详情</h2>
      <el-tag :type="getStatusType(task?.status)">
        {{ getStatusName(task?.status) }}
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
      <SubtitleSegmentComponent
        v-for="segment in segments"
        :key="segment.id"
        :segment="segment"
        @select-media="handleSelectMedia"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { taskApi } from '../api'
import SubtitleSegmentComponent from '../components/SubtitleSegment.vue'

interface MatchResult {
  id: string
  media_id: string
  score: number
  keyword_score: number
  semantic_score: number
  reason: string
  rank: number
  media_name?: string
  media_url?: string
  media_type?: string
}

interface Segment {
  id: string
  task_id: string
  content: string
  keywords?: string[]
  sort_order: number
  selected_media_id?: string
  matches?: MatchResult[]
}

interface TaskDetail {
  task_id: string
  type: string
  status: string
  input_text?: string
  error_message?: string
  segments?: Segment[]
}

const route = useRoute()
const taskId = route.params.id as string

const task = ref<TaskDetail | null>(null)
const segments = ref<Segment[]>([])
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

const getStatusName = (status?: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status || ''] || status || ''
}

const loadTask = async () => {
  try {
    const { data } = await taskApi.getStatus(taskId)
    task.value = data
    segments.value = data.segments || []
  } catch (error) {
    ElMessage.error('加载任务失败')
  }
}

const startPolling = () => {
  pollTimer = window.setInterval(async () => {
    await loadTask()
    if (task.value?.status === 'completed' || task.value?.status === 'failed') {
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

const handleSelectMedia = async (segmentId: string, mediaId: string) => {
  try {
    await taskApi.updateSegment(taskId, segmentId, {
      selected_media_id: mediaId
    })
    ElMessage.success('已选择素材')
    // 更新本地状态
    const segment = segments.value.find(s => s.id === segmentId)
    if (segment) {
      segment.selected_media_id = mediaId
    }
  } catch (error) {
    ElMessage.error('选择失败')
  }
}

const retryTask = async () => {
  try {
    await taskApi.retry(taskId)
    ElMessage.success('任务已重新提交')
    loading.value = true
    await loadTask()
    if (task.value?.status === 'processing') {
      startPolling()
    }
    loading.value = false
  } catch (error) {
    ElMessage.error('重试失败')
  }
}

onMounted(async () => {
  await loadTask()
  if (task.value?.status === 'processing') {
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

.segments {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
```

- [ ] **Step 2: 测试构建**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/TaskDetail.vue
git commit -m "feat: refactor TaskDetail to display matches inline"
```

---

## Task 6: 前端SubtitleSegment.vue优化

**Files:**
- Modify: `frontend/src/components/SubtitleSegment.vue`

- [ ] **Step 1: 优化SubtitleSegment.vue**

```vue
<template>
  <div class="subtitle-segment">
    <el-card class="segment-card">
      <template #header>
        <div class="segment-header">
          <span class="order">[{{ segment.sort_order + 1 }}]</span>
          <div class="segment-content">
            <el-input
              v-model="editContent"
              type="textarea"
              :rows="2"
              @blur="saveContent"
            />
          </div>
        </div>
      </template>
      
      <div class="keywords" v-if="segment.keywords?.length">
        <span class="label">关键词:</span>
        <el-tag
          v-for="keyword in segment.keywords"
          :key="keyword"
          size="small"
          type="info"
        >
          {{ keyword }}
        </el-tag>
      </div>
      
      <div class="matches-section" v-if="segment.matches?.length">
        <h4>推荐素材</h4>
        <div class="matches-list">
          <div
            v-for="match in segment.matches"
            :key="match.id"
            class="match-item"
            :class="{ selected: segment.selected_media_id === match.media_id }"
            @click="$emit('select-media', segment.id, match.media_id)"
          >
            <div class="media-preview">
              <img v-if="match.media_url" :src="match.media_url" :alt="match.media_name" />
              <div v-else class="placeholder">暂无预览</div>
            </div>
            <div class="match-info">
              <div class="media-name">{{ match.media_name || '未命名素材' }}</div>
              <div class="match-score">
                匹配度: {{ (match.score * 100).toFixed(0) }}%
              </div>
              <div class="match-reason">{{ match.reason }}</div>
              <div class="match-details">
                <span>关键词: {{ (match.keyword_score * 100).toFixed(0) }}%</span>
                <span>语义: {{ (match.semantic_score * 100).toFixed(0) }}%</span>
              </div>
            </div>
            <div class="select-indicator" v-if="segment.selected_media_id === match.media_id">
              ✓ 已选择
            </div>
          </div>
        </div>
      </div>
      
      <div class="no-matches" v-else-if="segment.matches?.length === 0">
        <el-empty description="暂无匹配素材" :image-size="60" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { taskApi } from '../api'

interface MatchResult {
  id: string
  media_id: string
  score: number
  keyword_score: number
  semantic_score: number
  reason: string
  rank: number
  media_name?: string
  media_url?: string
  media_type?: string
}

const props = defineProps<{
  segment: {
    id: string
    task_id: string
    content: string
    keywords?: string[]
    sort_order: number
    selected_media_id?: string
    matches?: MatchResult[]
  }
}>()

const emit = defineEmits<{
  'select-media': [segmentId: string, mediaId: string]
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
  } catch (error) {
    ElMessage.error('保存失败')
  }
}
</script>

<style scoped>
.segment-card {
  margin-bottom: 0;
}

.segment-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.order {
  font-weight: bold;
  color: #409eff;
  min-width: 30px;
}

.segment-content {
  flex: 1;
}

.keywords {
  margin: 10px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.keywords .label {
  color: #606266;
  font-size: 14px;
}

.keywords .el-tag {
  margin: 0;
}

.matches-section {
  margin-top: 15px;
  border-top: 1px solid #ebeef5;
  padding-top: 15px;
}

.matches-section h4 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 14px;
}

.matches-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.match-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.match-item:hover {
  border-color: #409eff;
  background-color: #f5f7fa;
}

.match-item.selected {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.media-preview {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
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
  font-size: 12px;
}

.match-info {
  flex: 1;
  min-width: 0;
}

.media-name {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.match-score {
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
  margin-bottom: 4px;
}

.match-reason {
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.match-details {
  font-size: 12px;
  color: #909399;
}

.match-details span {
  margin-right: 12px;
}

.select-indicator {
  color: #67c23a;
  font-weight: 500;
  font-size: 12px;
}

.no-matches {
  padding: 20px;
  text-align: center;
}
</style>
```

- [ ] **Step 2: 测试构建**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/SubtitleSegment.vue
git commit -m "feat: optimize SubtitleSegment with inline match display"
```

---

## Task 7: 端到端测试

- [ ] **Step 1: 重启后端服务**

```bash
cd D:\agent\project
docker-compose restart api
```

- [ ] **Step 2: 测试创建任务**

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"type":"text","content":"大家好，欢迎来到Python编程课程。今天我们将学习基础语法。"}'
```

Expected: 返回任务详情，status为completed，segments包含matches

- [ ] **Step 3: 测试获取任务详情**

```bash
curl http://localhost:8000/api/tasks/{task_id}
```

Expected: 返回segments数组，每个segment包含matches数组

- [ ] **Step 4: 验证前端显示**

1. 打开 http://localhost
2. 创建新任务
3. 查看任务详情
4. 确认每个片段显示3个推荐素材
5. 点击选择素材
6. 刷新页面，确认选择保留

- [ ] **Step 5: 最终提交**

```bash
git add -A
git commit -m "feat: complete business loop - auto matching and inline display"
```

---

## 实现计划完成

**总计任务数**: 7个任务  
**预计工时**: 1-2小时

### 任务依赖关系

```
Task 1 (Schema变更)
    ↓
Task 2 (匹配服务)
    ↓
Task 3 (API变更)
    ↓
Task 4 (前端API)
    ↓
Task 5 (TaskDetail重构)
    ↓
Task 6 (SubtitleSegment优化)
    ↓
Task 7 (端到端测试)
```

---

*计划创建时间: 2026-07-15*
*状态: 待执行*
