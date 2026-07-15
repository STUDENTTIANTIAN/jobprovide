# 业务闭环修复设计文档

## 1. 问题分析

### 1.1 当前问题

项目的核心业务闭环断裂：

```
当前流程（断裂）：
创建任务 → 字幕分段 → ❌ 缺少匹配 → ❌ 缺少结果展示
```

### 1.2 期望流程

```
期望流程（完整闭环）：
创建任务 → 字幕分段 → 素材匹配 → 人工调整 → 结果保存
```

### 1.3 缺失功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 素材匹配触发 | ❌ 未实现 | 没有API端点触发匹配 |
| 匹配结果返回 | ❌ 未实现 | API不返回matches数据 |
| 匹配结果展示 | ❌ 未实现 | 前端不显示推荐素材 |
| 任务重试 | ⚠️ 不完整 | 仅重置状态，不重新执行 |

---

## 2. 设计方案

### 2.1 整体流程

```
用户输入文本
    │
    ↓
POST /api/tasks {"type":"text","content":"..."}
    │
    ↓
创建Task记录 (status=pending)
    │
    ↓
SubtitleService.create_segments()
    │
    ├─→ 按句子分段
    ├─→ 提取关键词
    └─→ 保存SubtitleSegment记录
    │
    ↓
MatchingService.match_task_segments()  ← 自动触发
    │
    ├─→ 遍历每个片段
    ├─→ 生成embedding (TEI)
    ├─→ 搜索相似素材 (Qdrant)
    ├─→ 关键词匹配
    ├─→ 混合排序 → Top3
    └─→ 保存MatchResult记录
    │
    ↓
Task.status = "completed"
    │
    ↓
前端轮询 GET /api/tasks/{id}
    │
    ↓
显示任务详情，每个片段显示3个推荐素材
```

### 2.2 设计决策

- **匹配触发方式**：后端自动触发（任务分段完成后自动执行）
- **结果展示方式**：内联展示（每个片段下方直接显示推荐素材）
- **不需要额外汇总页**

---

## 3. API变更

### 3.1 修改：获取任务详情

```
GET /api/tasks/{task_id}
```

**响应变更：** 返回结果中包含 `segments` 和每个segment的 `matches`

```json
{
  "task_id": "uuid",
  "status": "completed",
  "segments": [
    {
      "id": "segment-uuid",
      "content": "今天我们来学习Python",
      "keywords": ["Python", "编程"],
      "sort_order": 0,
      "selected_media_id": null,
      "matches": [
        {
          "media_id": "media-uuid",
          "score": 0.85,
          "keyword_score": 0.7,
          "semantic_score": 0.9,
          "reason": "关键词匹配: Python | 语义高度相关",
          "media_name": "Python代码",
          "media_url": "/uploads/python.jpg"
        }
      ]
    }
  ]
}
```

### 3.2 修改：获取片段列表

```
GET /api/tasks/{task_id}/segments
```

**响应变更：** 每个segment包含 `matches` 字段

### 3.3 保持不变

- `POST /api/tasks` - 创建任务
- `PUT /api/tasks/{task_id}/segments/{segment_id}` - 更新选择

---

## 4. 后端变更

### 4.1 修改文件

| 文件 | 变更 |
|------|------|
| `backend/app/api/tasks.py` | 修改任务创建逻辑，分段后自动触发匹配 |
| `backend/app/services/matching_service.py` | 添加批量匹配方法 |
| `backend/app/schemas/task.py` | TaskStatus添加segments字段 |
| `backend/app/schemas/subtitle_segment.py` | SubtitleSegmentResponse添加matches字段 |

### 4.2 核心代码

#### 任务创建后自动触发匹配

```python
@router.post("", response_model=TaskResponse)
async def create_task(task_data: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = Task(type=task_data.type, input_text=task_data.content, status="pending")
    db.add(task)
    await db.flush()
    
    if task_data.type == "text" and task_data.content:
        task.status = "processing"
        
        # 1. 分段处理
        subtitle_service = SubtitleService(db)
        segments = await subtitle_service.create_segments(task.id, task_data.content)
        
        # 2. 自动触发匹配
        matching_service = MatchingService(db)
        await matching_service.match_task_segments(task.id)
        
        task.status = "completed"
    
    return task
```

#### 批量匹配方法

```python
async def match_task_segments(self, task_id: UUID):
    """批量匹配任务的所有片段"""
    from app.models.subtitle_segment import SubtitleSegment
    
    result = await self.db.execute(
        select(SubtitleSegment)
        .where(SubtitleSegment.task_id == task_id)
        .order_by(SubtitleSegment.sort_order)
    )
    segments = result.scalars().all()
    
    for segment in segments:
        matches = await self.match_segment(segment.id)
        await self.save_match_results(segment.id, matches)
    
    return len(segments)
```

#### Schema变更

```python
class SubtitleSegmentResponse(BaseModel):
    id: UUID
    task_id: UUID
    content: str
    keywords: Optional[List[str]]
    sort_order: int
    selected_media_id: Optional[UUID]
    matches: Optional[List[MatchResultResponse]] = None  # 新增
    created_at: datetime
```

---

## 5. 前端变更

### 5.1 修改文件

| 文件 | 变更 |
|------|------|
| `frontend/src/views/TaskDetail.vue` | 重构，从任务详情获取segments |
| `frontend/src/components/SubtitleSegment.vue` | 显示推荐素材列表 |
| `frontend/src/components/MatchResult.vue` | 优化显示，支持选择 |
| `frontend/src/api/index.ts` | 更新API调用 |

### 5.2 页面布局

```
┌─────────────────────────────────────────────────────────────────┐
│  任务详情 - 状态: ✅ 已完成                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ 片段 1 ──────────────────────────────────────────────────┐ │
│  │  "今天我们来学习Python编程基础"                             │ │
│  │  关键词: Python, 编程, 学习                                 │ │
│  │                                                            │ │
│  │  ┌─ 推荐素材 ──────────────────────────────────────────┐  │ │
│  │  │ [选中] 🖼️ Python代码    匹配度:92%  关键词匹配       │  │ │
│  │  │        🖼️ 编程教学     匹配度:85%  语义相关          │  │ │
│  │  │        🖼️ 代码编辑器   匹配度:78%  主题相关          │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 前端逻辑

```typescript
// TaskDetail.vue
const loadTask = async () => {
  const { data } = await taskApi.getStatus(taskId)
  task.value = data
  segments.value = data.segments || []  // 从任务详情中获取segments
}

// 轮询时检查匹配状态
const startPolling = () => {
  pollTimer = setInterval(async () => {
    await loadTask()
    if (task.value?.status === 'completed') {
      stopPolling()  // 匹配完成，停止轮询
    }
  }, 2000)
}
```

---

## 6. 实现步骤

### Step 1: 后端Schema变更
- 修改 `subtitle_segment.py` 添加 matches 字段
- 修改 `task.py` 添加 segments 字段

### Step 2: 后端匹配服务
- 添加 `match_task_segments` 批量匹配方法

### Step 3: 后端API变更
- 修改任务创建逻辑，自动触发匹配
- 修改获取任务详情，返回segments和matches

### Step 4: 前端API更新
- 更新 `getStatus` 返回类型

### Step 5: 前端页面重构
- 重构 `TaskDetail.vue` 显示匹配结果
- 优化 `SubtitleSegment.vue` 显示推荐素材

### Step 6: 测试验证
- 测试完整业务流程
- 验证刷新后数据保留

---

## 7. 验收标准

| 验收项 | 标准 |
|--------|------|
| 任务创建 | 输入文本后自动分段和匹配 |
| 匹配结果 | 每个片段显示3个推荐素材 |
| 匹配理由 | 显示关键词匹配和语义相关度 |
| 人工选择 | 点击可选择/替换素材 |
| 数据持久化 | 刷新页面后选择仍保留 |
| 任务重试 | 失败任务可重新执行 |

---

*文档创建时间: 2026-07-15*
*状态: 待审核*
