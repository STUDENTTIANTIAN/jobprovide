import httpx
from typing import Optional
from app.config import get_settings

settings = get_settings()

class TranscriptionService:
    def __init__(self):
        self.api_key = settings.SPEECH_API_KEY
        self.api_url = settings.SPEECH_API_URL

    async def transcribe(self, file_path: str) -> Optional[str]:
        """语音识别"""
        if not self.api_key or not self.api_url:
            # 降级：返回示例文本
            return "这是语音识别的示例文本。请配置真实的语音识别API。"

        try:
            async with httpx.AsyncClient() as client:
                with open(file_path, "rb") as f:
                    response = await client.post(
                        self.api_url,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files={"file": f}
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data.get("text", "")
        except Exception as e:
            print(f"Transcription error: {e}")
            return None