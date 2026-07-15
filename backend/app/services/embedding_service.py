import numpy as np
from typing import List, Optional
import httpx
from app.config import get_settings

settings = get_settings()

class EmbeddingService:
    def __init__(self):
        self.api_key = settings.EMBEDDING_API_KEY
        self.api_url = settings.EMBEDDING_API_URL

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本的embedding向量"""
        if not self.api_key or not self.api_url:
            # 降级：返回伪向量（用于演示）
            return self._dummy_embedding(text)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"input": text, "model": "text-embedding-ada-002"}
                )
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            print(f"Embedding API error: {e}")
            return self._dummy_embedding(text)

    def _dummy_embedding(self, text: str) -> List[float]:
        """生成伪embedding（基于文本哈希）"""
        np.random.seed(hash(text) % 2**32)
        return np.random.rand(1536).tolist()

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
