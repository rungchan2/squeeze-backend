"""
캐싱 서비스
Redis를 사용한 캐싱 기능 제공
"""
import json
import hashlib
from typing import Optional, Any, Dict
from datetime import datetime
import structlog
from app.db.redis import get_redis_client
from app.core.config import get_settings

settings = get_settings()
logger = structlog.get_logger()

# 캐시 TTL 설정 (초)
CACHE_TTL = {
    "text_analysis": 3600,  # 1시간
    "range_analysis": 1800,  # 30분
    "word_grouping": 7200,  # 2시간
    "user_session": 86400,  # 24시간
}


def _serialize_value(value: Any) -> str:
    """
    값을 JSON 문자열로 직렬화합니다.
    """
    if isinstance(value, datetime):
        value = value.isoformat()
    return json.dumps(value, ensure_ascii=False, default=str)


def _deserialize_value(value: str) -> Any:
    """
    JSON 문자열을 값으로 역직렬화합니다.
    """
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def get_cache_key(prefix: str, **kwargs) -> str:
    """
    캐시 키를 생성합니다.

    Args:
        prefix: 키 접두사
        **kwargs: 키 구성 요소

    Returns:
        생성된 캐시 키
    """
    # 키워드 인수를 정렬하여 일관된 키 생성
    sorted_kwargs = sorted(kwargs.items())
    key_data = f"{prefix}:" + ":".join([f"{k}={v}" for k, v in sorted_kwargs])

    # 너무 긴 키는 해시로 축약
    if len(key_data) > 200:
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:hash:{key_hash}"

    return key_data


def get_text_analysis_cache_key(text: str, options: Dict[str, Any] = None) -> str:
    """
    텍스트 분석 캐시 키를 생성합니다.
    """
    text_hash = hashlib.md5(text.encode()).hexdigest()
    options_str = _serialize_value(options or {})
    options_hash = hashlib.md5(options_str.encode()).hexdigest()

    return f"text_analysis:{text_hash}:{options_hash}"


def get_range_analysis_cache_key(
    journey_id: Optional[str] = None,
    journey_week_id: Optional[str] = None,
    mission_instance_id: Optional[str] = None,
    user_id: Optional[str] = None,
    top_n: int = 50,
    min_count: int = 1,
) -> str:
    """
    범위별 분석 캐시 키를 생성합니다.
    """
    return get_cache_key(
        "range_analysis",
        journey_id=journey_id,
        journey_week_id=journey_week_id,
        mission_instance_id=mission_instance_id,
        user_id=user_id,
        top_n=top_n,
        min_count=min_count,
    )


async def get_cached_value(key: str) -> Optional[Any]:
    """
    캐시에서 값을 조회합니다.

    Args:
        key: 캐시 키

    Returns:
        캐시된 값 (없으면 None)
    """
    try:
        redis_client = await get_redis_client()
        if not redis_client:
            return None

        cached_value = await redis_client.get(key)
        if cached_value is None:
            return None

        return _deserialize_value(cached_value)

    except Exception as e:
        logger.warning(f"Error getting cached value for key {key}: {e}")
        return None


async def set_cached_value(
    key: str, value: Any, ttl: Optional[int] = None, cache_type: str = "default"
) -> bool:
    """
    값을 캐시에 저장합니다.

    Args:
        key: 캐시 키
        value: 저장할 값
        ttl: TTL (초, None이면 기본값 사용)
        cache_type: 캐시 타입 (TTL 기본값 결정)

    Returns:
        저장 성공 여부
    """
    try:
        redis_client = await get_redis_client()
        if not redis_client:
            return False

        # TTL 설정
        if ttl is None:
            ttl = CACHE_TTL.get(cache_type, 3600)

        # 값 직렬화
        serialized_value = _serialize_value(value)

        # Redis에 저장
        await redis_client.setex(key, ttl, serialized_value)

        logger.debug(f"Cached value for key {key} with TTL {ttl}")
        return True

    except Exception as e:
        logger.warning(f"Error setting cached value for key {key}: {e}")
        return False


async def get_cached_analysis(
    text: str, options: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """
    텍스트 분석 결과를 캐시에서 조회합니다.

    Args:
        text: 분석 텍스트
        options: 분석 옵션

    Returns:
        캐시된 분석 결과
    """
    cache_key = get_text_analysis_cache_key(text, options)
    return await get_cached_value(cache_key)


async def set_cached_analysis(
    text: str, result: Dict[str, Any], options: Dict[str, Any] = None
) -> bool:
    """
    텍스트 분석 결과를 캐시에 저장합니다.

    Args:
        text: 분석 텍스트
        result: 분석 결과
        options: 분석 옵션

    Returns:
        저장 성공 여부
    """
    cache_key = get_text_analysis_cache_key(text, options)
    return await set_cached_value(cache_key, result, cache_type="text_analysis")


async def get_cached_range_analysis(
    journey_id: Optional[str] = None,
    journey_week_id: Optional[str] = None,
    mission_instance_id: Optional[str] = None,
    user_id: Optional[str] = None,
    top_n: int = 50,
    min_count: int = 1,
) -> Optional[Dict[str, Any]]:
    """
    범위별 분석 결과를 캐시에서 조회합니다.
    """
    cache_key = get_range_analysis_cache_key(
        journey_id=journey_id,
        journey_week_id=journey_week_id,
        mission_instance_id=mission_instance_id,
        user_id=user_id,
        top_n=top_n,
        min_count=min_count,
    )
    return await get_cached_value(cache_key)


async def set_cached_range_analysis(
    result: Dict[str, Any],
    journey_id: Optional[str] = None,
    journey_week_id: Optional[str] = None,
    mission_instance_id: Optional[str] = None,
    user_id: Optional[str] = None,
    top_n: int = 50,
    min_count: int = 1,
) -> bool:
    """
    범위별 분석 결과를 캐시에 저장합니다.
    """
    cache_key = get_range_analysis_cache_key(
        journey_id=journey_id,
        journey_week_id=journey_week_id,
        mission_instance_id=mission_instance_id,
        user_id=user_id,
        top_n=top_n,
        min_count=min_count,
    )
    return await set_cached_value(cache_key, result, cache_type="range_analysis")


async def invalidate_cache_pattern(pattern: str) -> int:
    """
    패턴에 맞는 캐시 키들을 무효화합니다.

    Args:
        pattern: 키 패턴 (Redis SCAN 패턴)

    Returns:
        무효화된 키의 개수
    """
    try:
        redis_client = await get_redis_client()
        if not redis_client:
            return 0

        deleted_count = 0
        async for key in redis_client.scan_iter(match=pattern):
            await redis_client.delete(key)
            deleted_count += 1

        logger.info(
            f"Invalidated {deleted_count} cache keys matching pattern: {pattern}"
        )
        return deleted_count

    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {e}")
        return 0


async def invalidate_user_cache(user_id: str) -> int:
    """
    특정 사용자의 캐시를 무효화합니다.
    """
    return await invalidate_cache_pattern(f"*user_id={user_id}*")


async def invalidate_analysis_cache() -> int:
    """
    모든 분석 캐시를 무효화합니다.
    """
    patterns = ["text_analysis:*", "range_analysis:*", "word_grouping:*"]

    total_deleted = 0
    for pattern in patterns:
        total_deleted += await invalidate_cache_pattern(pattern)

    return total_deleted


async def get_cache_stats() -> Dict[str, Any]:
    """
    캐시 통계를 조회합니다.
    """
    try:
        redis_client = await get_redis_client()
        if not redis_client:
            return {"status": "unavailable"}

        info = await redis_client.info()

        return {
            "status": "available",
            "total_keys": info.get("db0", {}).get("keys", 0),
            "used_memory": info.get("used_memory_human", "0B"),
            "connected_clients": info.get("connected_clients", 0),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
        }

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"status": "error", "error": str(e)}
