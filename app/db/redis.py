from redis import asyncio as aioredis
from typing import Optional
import json
import hashlib
import structlog
from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """Get or create Redis client singleton"""
    global _redis_client

    if _redis_client is None:
        try:
            _redis_client = await aioredis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
            logger.info("Redis client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise

    return _redis_client


async def close_redis_client():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")


def generate_cache_key(
    org_id: str, journey_id: str, analysis_type: str, params: dict = None
) -> str:
    """Generate cache key for analysis results"""
    base_key = f"{org_id}:{journey_id}:{analysis_type}"

    if params:
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
        return f"{base_key}:{params_hash}"

    return base_key


async def get_cached_result(key: str) -> Optional[dict]:
    """Get cached result from Redis"""
    try:
        client = await get_redis_client()
        result = await client.get(key)

        if result:
            logger.info(f"Cache hit for key: {key}")
            return json.loads(result)

        logger.info(f"Cache miss for key: {key}")
        return None
    except Exception as e:
        logger.error(f"Error getting cached result: {e}")
        return None


async def set_cached_result(key: str, value: dict, ttl: Optional[int] = None) -> bool:
    """Set cached result in Redis"""
    try:
        client = await get_redis_client()
        ttl = ttl or settings.REDIS_TTL

        await client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        logger.info(f"Cached result for key: {key} with TTL: {ttl}")
        return True
    except Exception as e:
        logger.error(f"Error setting cached result: {e}")
        return False


async def delete_cached_result(key: str) -> bool:
    """Delete cached result from Redis"""
    try:
        client = await get_redis_client()
        result = await client.delete(key)
        logger.info(f"Deleted cache key: {key}")
        return bool(result)
    except Exception as e:
        logger.error(f"Error deleting cached result: {e}")
        return False


async def check_redis_connection() -> bool:
    """Check if Redis connection is healthy"""
    try:
        client = await get_redis_client()
        await client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection check failed: {e}")
        return False
