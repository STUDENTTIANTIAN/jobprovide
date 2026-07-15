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
