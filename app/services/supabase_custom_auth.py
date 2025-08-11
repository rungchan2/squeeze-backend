"""
Supabase Custom Auth Hook 인증 서비스
Custom Auth Hook을 사용하는 Supabase 토큰 검증
"""
import base64
import json
from typing import Dict, Any
import structlog
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.db.supabase import get_supabase_client

settings = get_settings()
logger = structlog.get_logger()


class SupabaseCustomAuthService:
    """Supabase Custom Auth Hook 토큰 검증 서비스"""

    def __init__(self):
        self.supabase = get_supabase_client()

    async def verify_custom_token(self, token: str) -> Dict[str, Any]:
        """
        Supabase Custom Auth Hook 토큰을 검증합니다.

        Args:
            token: base64- prefix가 포함된 토큰 또는 순수 토큰

        Returns:
            사용자 정보 딕셔너리

        Raises:
            AuthenticationError: 토큰이 유효하지 않은 경우
        """
        try:
            # base64- prefix 제거
            if token.startswith("base64-"):
                token = token[7:]  # "base64-" 제거

            # Bearer prefix 제거 (있는 경우)
            if token.startswith("Bearer "):
                token = token[7:]  # "Bearer " 제거

            # Supabase로 토큰 검증 (getUser API 사용)
            try:
                # Supabase Python 클라이언트를 통한 사용자 정보 조회
                # Custom Auth Hook을 통해 JWT에 포함된 정보를 가져옴
                response = self.supabase.auth.get_user(token)

                if response and response.user:
                    user_data = response.user

                    # Custom Auth Hook으로 추가된 메타데이터 추출
                    app_metadata = user_data.app_metadata or {}
                    user_metadata = user_data.user_metadata or {}

                    # 사용자 정보 구성
                    user_info = {
                        "id": user_data.id,
                        "email": user_data.email,
                        "role": app_metadata.get("role", "user"),
                        "organization_id": app_metadata.get("organization_id"),
                        "profile_id": app_metadata.get("profile_id"),
                        "first_name": user_metadata.get("first_name"),
                        "last_name": user_metadata.get("last_name"),
                        "profile_image": user_metadata.get("profile_image"),
                        "is_active": True,
                    }

                    logger.info(
                        f"User authenticated via custom token: {user_info['email']} (Role: {user_info['role']})"
                    )
                    return user_info
                else:
                    raise AuthenticationError("Invalid token - no user found")

            except Exception as e:
                # getUser가 실패하면 토큰을 직접 파싱 시도 (fallback)
                logger.debug(f"Supabase getUser failed, trying direct parsing: {e}")
                return await self._parse_custom_token_directly(token)

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Custom token verification error: {e}")
            raise AuthenticationError("Token verification failed")

    async def _parse_custom_token_directly(self, token: str) -> Dict[str, Any]:
        """
        Custom Auth Hook 토큰을 직접 파싱합니다 (fallback 방법).

        Args:
            token: 토큰 문자열

        Returns:
            사용자 정보
        """
        try:
            # Base64 디코딩 시도
            # JWT는 일반적으로 3부분으로 구성: header.payload.signature
            parts = token.split(".")

            if len(parts) != 3:
                raise AuthenticationError("Invalid token format")

            # Payload 부분 디코딩 (두 번째 부분)
            # Base64 URL 디코딩을 위해 패딩 추가
            payload_part = parts[1]
            payload_part += "=" * (4 - len(payload_part) % 4)  # 패딩 추가

            # URL-safe base64 디코딩
            payload_bytes = base64.urlsafe_b64decode(payload_part)
            payload = json.loads(payload_bytes)

            # Custom Auth Hook으로 추가된 정보 추출
            app_metadata = payload.get("app_metadata", {})
            user_metadata = payload.get("user_metadata", {})

            user_info = {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "role": app_metadata.get("role", "user"),
                "organization_id": app_metadata.get("organization_id"),
                "profile_id": app_metadata.get("profile_id"),
                "first_name": user_metadata.get("first_name"),
                "last_name": user_metadata.get("last_name"),
                "profile_image": user_metadata.get("profile_image"),
                "is_active": True,
            }

            logger.debug(
                f"Token parsed directly: {user_info['email']} (Role: {user_info['role']})"
            )
            return user_info

        except Exception as e:
            logger.error(f"Direct token parsing failed: {e}")
            raise AuthenticationError("Failed to parse token")

    def check_permission(self, user_role: str, required_role: str) -> bool:
        """
        사용자 권한을 확인합니다.

        Args:
            user_role: 사용자 역할
            required_role: 요구되는 역할

        Returns:
            권한 여부
        """
        role_hierarchy = {
            "user": 1,
            "teacher": 2,
            "admin": 3,
        }

        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 999)

        return user_level >= required_level


# 싱글톤 인스턴스
_custom_auth_service = None


def get_custom_auth_service() -> SupabaseCustomAuthService:
    """Supabase Custom Auth 서비스 싱글톤 인스턴스 반환"""
    global _custom_auth_service
    if _custom_auth_service is None:
        _custom_auth_service = SupabaseCustomAuthService()
    return _custom_auth_service


async def verify_custom_token(token: str) -> Dict[str, Any]:
    """
    Supabase Custom Auth Hook 토큰을 검증하고 사용자 정보를 반환합니다.

    Args:
        token: base64- prefix가 포함된 토큰 또는 순수 토큰

    Returns:
        사용자 정보
    """
    auth_service = get_custom_auth_service()
    return await auth_service.verify_custom_token(token)


def check_user_permission(user_role: str, required_role: str) -> bool:
    """
    사용자 권한을 확인합니다.

    Args:
        user_role: 사용자 역할
        required_role: 요구되는 역할

    Returns:
        권한 여부
    """
    auth_service = get_custom_auth_service()
    return auth_service.check_permission(user_role, required_role)
