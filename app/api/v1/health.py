"""
헬스체크 엔드포인트
서비스 상태를 확인하는 API를 제공합니다.
"""
from fastapi import APIRouter
import asyncio
import os
from app.models.schemas import HealthCheckResponse, ServiceStatus
from app.core.config import get_settings
from app.db.redis import check_redis_connection
from app.db.supabase import check_supabase_connection
import time
import structlog

logger = structlog.get_logger()
settings = get_settings()
router = APIRouter()

# 서버 시작 시간을 기록
START_TIME = time.time()
IS_SERVERLESS = os.getenv("VERCEL") is not None


async def _check_service_with_timeout(service_name: str, check_func, timeout: float = 3.0):
    """Check service health with timeout and proper error handling"""
    try:
        result = await asyncio.wait_for(check_func(), timeout=timeout)
        logger.info(f"{service_name} health check: {'healthy' if result else 'unhealthy'}")
        return result
    except asyncio.TimeoutError:
        logger.warning(f"{service_name} health check timed out after {timeout}s")
        return False
    except Exception as e:
        logger.error(f"{service_name} health check failed: {e}")
        return False


@router.get(
    "/",
    response_model=HealthCheckResponse,
    summary="헬스체크",
    description="서비스 상태 및 데이터베이스 연결을 확인합니다.",
)
async def health_check() -> HealthCheckResponse:
    """
    서비스 헬스체크 엔드포인트 (Serverless 최적화)

    Returns:
        서비스 상태 정보
    """
    # 병렬로 서비스 상태 확인 (타임아웃 적용)
    redis_task = _check_service_with_timeout("Redis", check_redis_connection, 2.0)
    supabase_task = _check_service_with_timeout("Supabase", check_supabase_connection, 3.0)
    
    # 동시에 실행
    redis_ok, supabase_ok = await asyncio.gather(redis_task, supabase_task, return_exceptions=True)
    
    # Exception 결과 처리
    if isinstance(redis_ok, Exception):
        logger.error(f"Redis health check exception: {redis_ok}")
        redis_ok = False
    if isinstance(supabase_ok, Exception):
        logger.error(f"Supabase health check exception: {supabase_ok}")
        supabase_ok = False

    # Serverless 환경에서는 Redis 실패에 더 관대하게 처리
    if IS_SERVERLESS:
        # Supabase만 필수, Redis는 캐시이므로 선택적
        overall_status = "healthy" if supabase_ok else "degraded"
        if not redis_ok:
            logger.info("Redis unhealthy in serverless - treating as non-critical")
    else:
        # 개발 환경에서는 모든 서비스가 정상이어야 함
        overall_status = "healthy" if (redis_ok and supabase_ok) else "degraded"

    # 가동 시간 계산 (serverless에서는 의미 없지만 호환성 유지)
    uptime_seconds = int(time.time() - START_TIME)

    return HealthCheckResponse(
        status=overall_status,
        version=settings.VERSION,
        services=ServiceStatus(
            redis="healthy" if redis_ok else "unhealthy",
            supabase="healthy" if supabase_ok else "unhealthy",
        ),
        uptime_seconds=uptime_seconds,
    )
