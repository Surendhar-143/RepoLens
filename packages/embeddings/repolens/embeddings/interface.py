import abc
from typing import List


class EmbeddingProvider(abc.ABC):
    @abc.abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Convert a text chunk into an embedding float vector"""
        pass

    @abc.abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Batch convert multiple text chunks into list of embedding vectors"""
        pass

    @abc.abstractmethod
    def get_dimension(self) -> int:
        """Return the vector dimensionality of the embedding model"""
        pass
