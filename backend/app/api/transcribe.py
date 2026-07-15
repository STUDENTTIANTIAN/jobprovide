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