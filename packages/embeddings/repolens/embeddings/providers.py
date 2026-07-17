import hashlib
import random
from typing import List, Optional
import httpx

from repolens.embeddings.interface import EmbeddingProvider


class HashedMockEmbeddingProvider(EmbeddingProvider):
    """
    A stable, deterministic local provider that hashes strings into vector floats.
    Ensures zero dependency overhead and zero network requests while developing.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _hash_to_vector(self, text: str) -> List[float]:
        # Generate a deterministic pseudo-random float vector from text hash
        sha = hashlib.sha256(text.encode("utf-8")).digest()
        random.seed(int.from_bytes(sha, "big"))
        return [random.uniform(-1.0, 1.0) for _ in range(self.dimension)]

    async def get_embedding(self, text: str) -> List[float]:
        return self._hash_to_vector(text)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_to_vector(t) for t in texts]

    def get_dimension(self) -> int:
        return self.dimension


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    Vectorizes chunks using OpenAI's API.
    """
    def __init__(self, api_key: str, model: str = "text-embedding-3-small", dimension: int = 1536):
        self.api_key = api_key
        self.model = model
        self.dimension = dimension

    async def get_embedding(self, text: str) -> List[float]:
        res = await self.get_embeddings([text])
        return res[0]

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            # Fallback mock if key not set
            mock = HashedMockEmbeddingProvider(self.dimension)
            return await mock.get_embeddings(texts)
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": texts,
                    "model": self.model
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]

    def get_dimension(self) -> int:
        return self.dimension


class SentenceTransformersProvider(EmbeddingProvider):
    """
    Loads Sentence Transformers using FastEmbed, falling back to HashedMock if offline.
    """
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension
        self._model = None
        self._initialized = False

    def _init_model(self):
        if self._initialized:
            return
        try:
            from fastembed import TextEmbedding
            self._model = TextEmbedding(model_name=self.model_name)
            self._initialized = True
        except ImportError:
            print("fastembed library not installed. Falling back to deterministic HashedMockEmbeddingProvider.")
            self._initialized = True

    async def get_embedding(self, text: str) -> List[float]:
        self._init_model()
        if self._model:
            # Sync generation run in executor thread
            import asyncio
            loop = asyncio.get_event_loop()
            embeddings_iter = await loop.run_in_executor(
                None, 
                lambda: list(self._model.embed([text]))
            )
            return embeddings_iter[0].tolist()
        
        fallback = HashedMockEmbeddingProvider(self.dimension)
        return await fallback.get_embedding(text)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        self._init_model()
        if self._model:
            import asyncio
            loop = asyncio.get_event_loop()
            embeddings_iter = await loop.run_in_executor(
                None, 
                lambda: list(self._model.embed(texts))
            )
            return [vec.tolist() for vec in embeddings_iter]

        fallback = HashedMockEmbeddingProvider(self.dimension)
        return await fallback.get_embeddings(texts)

    def get_dimension(self) -> int:
        return self.dimension
