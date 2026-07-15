from fastapi import APIRouter
from app.api.tasks import router as tasks_router
from app.api.media import router as media_router

api_router = APIRouter()
api_router.include_router(tasks_router)
api_router.include_router(media_router)