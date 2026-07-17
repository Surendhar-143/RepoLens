import logging
from qdrant_client import AsyncQdrantClient
from app.core.config import settings

logger = logging.getLogger("repolens.qdrant")

_qdrant_client: AsyncQdrantClient | None = None


def get_qdrant_client() -> AsyncQdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY,
            timeout=5.0
        )
    return _qdrant_client


async def close_qdrant() -> None:
    global _qdrant_client
    if _qdrant_client is not None:
        await _qdrant_client.close()
        _qdrant_client = None
        logger.info("Qdrant connection closed.")


async def verify_qdrant_connection() -> bool:
    try:
        client = get_qdrant_client()
        # Retrieve cluster details or collections list to verify endpoint availability
        await client.get_collections()
        return True
    except Exception as e:
        logger.error(f"Qdrant connection failed: {str(e)}")
        return False
