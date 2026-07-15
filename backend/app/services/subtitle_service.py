import re
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from app.models.subtitle_segment import SubtitleSegment

class SubtitleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def parse_text(self, text: str) -> List[dict]:
        """解析文本字幕，按句子分段"""
        # 按句号、问号、感叹号分句
        sentences = re.split(r'(?<=[。！？!?\n])', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        segments = []
        for i, sentence in enumerate(sentences):
            segments.append({
                "content": sentence,
                "start_time": None,
                "end_time": None,
                "sort_order": i
            })
        return segments

    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简单实现：提取中文词汇和英文单词）"""
        # 提取英文单词
        english_words = re.findall(r'[a-zA-Z]+', text)
        # 提取中文词汇：按非中文字符分段，提取2-4字词组
        chinese_runs = re.findall(r'[一-龥]+', text)
        chinese_words = []
        for run in chinese_runs:
            # 如果段落长度在2-4字之间，直接作为关键词
            if 2 <= len(run) <= 4:
                chinese_words.append(run)
            else:
                # 否则提取所有2字重叠窗口
                for i in range(len(run) - 1):
                    chinese_words.append(run[i:i + 2])

        # 去重并返回（保持英文优先）
        keywords = list(dict.fromkeys(english_words + chinese_words))
        return keywords[:10]  # 最多10个关键词

    async def create_segments(self, task_id: UUID, text: str) -> List[SubtitleSegment]:
        """为任务创建字幕片段"""
        parsed = self.parse_text(text)
        segments = []

        for item in parsed:
            segment = SubtitleSegment(
                task_id=task_id,
                content=item["content"],
                start_time=item["start_time"],
                end_time=item["end_time"],
                keywords=self.extract_keywords(item["content"]),
                sort_order=item["sort_order"]
            )
            self.db.add(segment)
            segments.append(segment)

        await self.db.flush()
        return segments

    async def get_segments(self, task_id: UUID) -> List[SubtitleSegment]:
        """获取任务的所有字幕片段"""
        result = await self.db.execute(
            select(SubtitleSegment)
            .where(SubtitleSegment.task_id == task_id)
            .order_by(SubtitleSegment.sort_order)
        )
        return result.scalars().all()

    async def update_segment(self, segment_id: UUID, **kwargs) -> Optional[SubtitleSegment]:
        """更新字幕片段"""
        result = await self.db.execute(
            select(SubtitleSegment).where(SubtitleSegment.id == segment_id)
        )
        segment = result.scalar_one_or_none()

        if segment:
            for key, value in kwargs.items():
                if value is not None and hasattr(segment, key):
                    setattr(segment, key, value)
            await self.db.flush()

        return segment