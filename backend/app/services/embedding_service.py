import asyncio
import numpy as np
from typing import List, Optional
import httpx
from app.config import get_settings

settings = get_settings()


class TextEmbeddingsInferenceEmbeddings:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        with httpx.Client(timeout=60, trust_env=False) as client:
            response = self._post_with_retry(client, texts)
            return self._parse_response(response.json())

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=60, trust_env=False) as client:
            response = await self._apost_with_retry(client, texts)
            return self._parse_response(response.json())

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    async def aembed_query(self, text: str) -> list[float]:
        return (await self.aembed_documents([text]))[0]

    @staticmethod
    def _parse_response(data) -> list[list[float]]:
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("data"), list):
            return [item["embedding"] for item in data["data"]]
        raise ValueError(f"Unexpected embedding response: {data}")

    def _post_with_retry(self, client: httpx.Client, texts: list[str], attempts: int = 3) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                response = client.post(f"{self.base_url}/embed", json={"inputs": texts})
                response.raise_for_status()
                return response
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_error = exc
                if not self._should_retry(exc) or attempt == attempts - 1:
                    raise
                asyncio.sleep(0.5 * (attempt + 1))
        raise RuntimeError("Embedding request failed") from last_error

    async def _apost_with_retry(self, client: httpx.AsyncClient, texts: list[str], attempts: int = 3) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                response = await client.post(f"{self.base_url}/embed", json={"inputs": texts})
                response.raise_for_status()
                return response
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_error = exc
                if not self._should_retry(exc) or attempt == attempts - 1:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))
        raise RuntimeError("Embedding request failed") from last_error

    @staticmethod
    def _should_retry(exc: Exception) -> bool:
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in {502, 503, 504}
        return isinstance(exc, httpx.TransportError)


class EmbeddingService:
    def __init__(self):
        self.tei_url = settings.TEI_URL
        self.client: Optional[TextEmbeddingsInferenceEmbeddings] = None
        self._init_client()

    def _init_client(self):
        if self.tei_url:
            self.client = TextEmbeddingsInferenceEmbeddings(self.tei_url)

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        if not self.client:
            return self._dummy_embedding(text)

        try:
            return await self.client.aembed_query(text)
        except Exception as e:
            print(f"Embedding API error: {e}")
            return self._dummy_embedding(text)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.client:
            return [self._dummy_embedding(text) for text in texts]

        try:
            return await self.client.aembed_documents(texts)
        except Exception as e:
            print(f"Embedding API error: {e}")
            return [self._dummy_embedding(text) for text in texts]

    def _dummy_embedding(self, text: str) -> List[float]:
        np.random.seed(hash(text) % 2**32)
        return np.random.rand(1024).tolist()

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
