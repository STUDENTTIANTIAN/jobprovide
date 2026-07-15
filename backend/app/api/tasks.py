from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.models.task import Task
from app.models.subtitle_segment import SubtitleSegment
from app.schemas.task import TaskCreate, TaskResponse, TaskStatus
from app.schemas.subtitle_segment import SubtitleSegmentResponse
from app.services.subtitle_service import SubtitleService

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
        return task

    if task.status == "processing":
        return task

    task.status = "pending"
    return task