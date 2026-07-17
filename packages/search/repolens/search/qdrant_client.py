import logging
from typing import List, Dict, Any, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

logger = logging.getLogger("repolens.search.qdrant")


class QdrantSearchClient:
    def __init__(self, host: str = "localhost", port: int = 6333, api_key: Optional[str] = None):
        self.client = AsyncQdrantClient(host=host, port=port, api_key=api_key)

    def _get_collection_name(self, repository_id: str) -> str:
        # Clean collection name (UUID compliant format)
        clean_id = repository_id.replace("-", "")
        return f"repolens_repo_{clean_id}"

    async def ensure_collection(self, repository_id: str, dimension: int) -> str:
        """Create Qdrant collection if it does not already exist"""
        collection_name = self._get_collection_name(repository_id)
        exists = await self.client.collection_exists(collection_name)
        if not exists:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
            )
            logger.info(f"Created Qdrant vector collection: {collection_name}")
        return collection_name

    async def delete_collection(self, repository_id: str) -> None:
        """Purge whole collection"""
        collection_name = self._get_collection_name(repository_id)
        exists = await self.client.collection_exists(collection_name)
        if exists:
            await self.client.delete_collection(collection_name)
            logger.info(f"Purged Qdrant collection: {collection_name}")

    async def delete_file_points(self, repository_id: str, file_id: str) -> None:
        """Delete all points associated with a specific file (for incremental updates)"""
        collection_name = self._get_collection_name(repository_id)
        exists = await self.client.collection_exists(collection_name)
        if exists:
            await self.client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="file_id",
                            match=MatchValue(value=file_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted old vectors for file {file_id} in {collection_name}")

    async def upsert_chunks(self, repository_id: str, chunks: List[Any], embeddings: List[List[float]], dimension: int) -> None:
        """Batch upsert points to Qdrant collection"""
        collection_name = await self.ensure_collection(repository_id, dimension)
        points = []
        for i, chunk in enumerate(chunks):
            points.append(PointStruct(
                id=chunk.id,
                vector=embeddings[i],
                payload={
                    "file_id": chunk.file_id,
                    "file_path": chunk.file_path,
                    "content": chunk.content,
                    "type": chunk.chunk_type,
                    "metadata": chunk.metadata
                }
            ))

        if points:
            await self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} vector points into Qdrant collection {collection_name}")

    async def search_similarity(
        self,
        repository_id: str,
        query_vector: List[float],
        limit: int = 10,
        chunk_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform similarity search on Qdrant vectors matching a query vector"""
        collection_name = self._get_collection_name(repository_id)
        exists = await self.client.collection_exists(collection_name)
        if not exists:
            return []

        search_filter = None
        if chunk_type:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="type",
                        match=MatchValue(value=chunk_type)
                    )
                ]
            )

        res = await self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=limit
        )

        results = []
        for hit in res:
            results.append({
                "id": str(hit.id),
                "score": hit.score,
                "file_id": hit.payload.get("file_id"),
                "file_path": hit.payload.get("file_path"),
                "content": hit.payload.get("content"),
                "type": hit.payload.get("type"),
                "metadata": hit.payload.get("metadata", {})
            })
        return results
