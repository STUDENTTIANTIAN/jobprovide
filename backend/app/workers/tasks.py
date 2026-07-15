from app.workers.celery_app import celery_app
from app.database import async_session
from app.models.task import Task
from app.models.subtitle_segment import SubtitleSegment
from app.services.subtitle_service import SubtitleService
from sqlalchemy import select
import asyncio

@celery_app.task(bind=True, name="process_task")
def process_task(self, task_id: str):
    """处理字幕任务"""
    asyncio.run(_process_task_async(self, task_id))

async def _process_task_async(task, task_id: str):
    """异步处理任务"""
    async with async_session() as db:
        try:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task_obj = result.scalar_one_or_none()

            if not task_obj:
                return {"error": "Task not found"}

            task_obj.status = "processing"
            await db.commit()

            if task_obj.input_text:
                subtitle_service = SubtitleService(db)
                await subtitle_service.create_segments(task_id, task_obj.input_text)

            task_obj.status = "completed"
            await db.commit()

            return {"status": "completed", "task_id": task_id}

        except Exception as e:
            task_obj.status = "failed"
            task_obj.error_message = str(e)
            await db.commit()
            return {"error": str(e)}

@celery_app.task(bind=True, name="match_segment")
def match_segment_task(self, segment_id: str):
    """匹配单个字幕片段"""
    asyncio.run(_match_segment_async(self, segment_id))

async def _match_segment_async(task, segment_id: str):
    """异步匹配片段"""
    async with async_session() as db:
        try:
            from app.services.matching_service import MatchingService
            matching_service = MatchingService(db)
            matches = await matching_service.match_segment(segment_id)
            await matching_service.save_match_results(segment_id, matches)
            await db.commit()
            return {"status": "completed", "segment_id": segment_id}
        except Exception as e:
            return {"error": str(e)}
