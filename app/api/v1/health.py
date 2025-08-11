"""
헬스체크 엔드포인트
서비스 상태를 확인하는 API를 제공합니다.
"""
from fastapi import APIRouter
from app.models.schemas import HealthCheckResponse, ServiceStatus
from app.core.config import get_settings
from app.db.redis import check_redis_connection
from app.db.supabase import check_supabase_connection
import time

settings = get_settings()
router = APIRouter()

# 서버 시작 시간을 기록
START_TIME = time.time()


@router.get(
    "/",
    response_model=HealthCheckResponse,
    summary="헬스체크",
    description="서비스 상태 및 데이터베이스 연결을 확인합니다.",
)
async def health_check() -> HealthCheckResponse:
    """
    서비스 헬스체크 엔드포인트

    Returns:
        서비스 상태 정보
    """
    # 각 서비스 상태 확인
    redis_ok = await check_redis_connection()
    supabase_ok = await check_supabase_connection()

    # 전체 상태 결정
    overall_status = "healthy" if (redis_ok and supabase_ok) else "degraded"

    # 가동 시간 계산
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
