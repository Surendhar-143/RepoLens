import logging
from redis.asyncio import Redis, from_url
from app.core.config import settings

logger = logging.getLogger("repolens.redis")

# Global Redis client reference
redis_client: Redis | None = None


def get_redis_client() -> Redis:
    global redis_client
    if redis_client is None:
        redis_client = from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None
        logger.info("Redis connection closed.")


async def verify_redis_connection() -> bool:
    try:
        client = get_redis_client()
        # Ping returns True if connection is successful
        await client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {str(e)}")
        return False
