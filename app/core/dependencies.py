"""
의존성 주입을 위한 모듈
FastAPI의 Depends를 활용하여 DB, Redis, Auth 등의 의존성을 관리합니다.
"""
from typing import AsyncGenerator, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from app.db.supabase import get_supabase_client
from app.db.redis import get_redis_client
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.services.supabase_unified_auth import authenticate_token, check_user_permission
import structlog

logger = structlog.get_logger()
settings = get_settings()


async def get_db() -> AsyncGenerator:
    """Supabase 클라이언트를 의존성으로 제공"""
    try:
        client = get_supabase_client()
        yield client
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        )


async def get_cache() -> AsyncGenerator:
    """Redis 클라이언트를 의존성으로 제공"""
    try:
        client = await get_redis_client()
        yield client
    except Exception as e:
        logger.error(f"Cache connection error: {e}")
        # Redis 연결 실패 시에도 서비스는 계속 동작하도록 None 반환
        yield None


async def get_supabase_token(request: Request) -> str:
    """
    쿠키 또는 Authorization 헤더에서 Supabase access_token을 추출합니다.

    우선순위:
    1. Authorization 헤더의 Bearer 토큰
    2. 쿠키의 sb-access-token
    """
    # 1. Authorization 헤더 확인
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        if token:
            return token

    # 2. 쿠키에서 Supabase 토큰 확인
    # 일반적인 Supabase 쿠키 이름들
    cookie_names = [
        "sb-access-token",
        "supabase-access-token",
        "sb-" + settings.SUPABASE_URL.split("://")[1].split(".")[0] + "-auth-token",
    ]

    for cookie_name in cookie_names:
        token = request.cookies.get(cookie_name)
        if token:
            return token

    # 토큰을 찾을 수 없는 경우
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 토큰이 필요합니다. 쿠키 또는 Authorization 헤더에 토큰을 포함해주세요.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(token: str = Depends(get_supabase_token)) -> Dict[str, Any]:
    """Supabase 토큰에서 현재 사용자 정보를 추출합니다."""
    try:
        user_info = await authenticate_token(token)
        logger.debug(
            f"User authenticated: {user_info.get('email')} (Role: {user_info.get('role')})"
        )
        return user_info

    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 처리 중 오류가 발생했습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_teacher_role(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Teacher 이상의 권한을 요구하는 의존성"""
    user_role = current_user.get("role", "user")

    if not check_user_permission(user_role, "teacher"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Teacher 이상의 권한이 필요합니다"
        )

    return current_user


async def require_admin_role(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Admin 권한을 요구하는 의존성"""
    user_role = current_user.get("role", "user")

    if not check_user_permission(user_role, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin 권한이 필요합니다"
        )

    return current_user


async def require_user_role(current_user: Dict[str, Any] = Depends(get_current_user)):
    """User 이상의 권한을 요구하는 의존성 (기본적으로 인증된 사용자)"""
    user_role = current_user.get("role", "user")

    if not check_user_permission(user_role, "user"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="로그인이 필요합니다")

    return current_user
