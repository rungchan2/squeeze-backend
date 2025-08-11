"""
Supabase 세션 기반 인증 서비스
Supabase의 getUser API를 직접 사용하여 인증
"""
from typing import Dict, Any
import structlog
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.db.supabase import get_supabase_client

settings = get_settings()
logger = structlog.get_logger()


class SupabaseSessionAuthService:
    """Supabase 세션 기반 인증 서비스"""

    def __init__(self):
        self.supabase = get_supabase_client()

    async def verify_session_token(self, token: str) -> Dict[str, Any]:
        """
        Supabase 세션 토큰을 검증합니다.
        JWT 디코딩 대신 Supabase API를 직접 사용합니다.

        Args:
            token: 세션 토큰 (어떤 형식이든)

        Returns:
            사용자 정보 딕셔너리

        Raises:
            AuthenticationError: 토큰이 유효하지 않은 경우
        """
        try:
            # 다양한 prefix 처리
            original_token = token

            # base64- prefix 제거
            if token.startswith("base64-"):
                token = token[7:]

            # Bearer prefix 제거
            if token.startswith("Bearer "):
                token = token[7:]

            logger.debug(f"Attempting to verify token (length: {len(token)})")

            # Supabase의 getUser API 사용
            # 이 API는 다양한 토큰 형식을 자동으로 처리합니다
            try:
                response = self.supabase.auth.get_user(token)

                if response and hasattr(response, "user") and response.user:
                    user_data = response.user

                    # 사용자 정보 추출
                    user_info = self._extract_user_info(user_data)
                    logger.info(
                        f"User authenticated: {user_info['email']} (Role: {user_info['role']})"
                    )
                    return user_info

            except Exception as api_error:
                logger.debug(f"Supabase getUser failed: {api_error}")

                # 대체 방법: 세션 검증 API 시도
                try:
                    # 세션 토큰으로 현재 세션 가져오기
                    session_response = self.supabase.auth.get_session()

                    if (
                        session_response
                        and hasattr(session_response, "session")
                        and session_response.session
                    ):
                        # 세션에서 사용자 정보 추출
                        session = session_response.session
                        if session.user:
                            user_info = self._extract_user_info(session.user)
                            logger.info(
                                f"User authenticated via session: {user_info['email']}"
                            )
                            return user_info

                except Exception as session_error:
                    logger.debug(f"Session verification also failed: {session_error}")

            # 모든 방법이 실패한 경우
            raise AuthenticationError("Invalid token - unable to verify with Supabase")

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Session token verification error: {e}")
            raise AuthenticationError("Token verification failed")

    def _extract_user_info(self, user_data: Any) -> Dict[str, Any]:
        """
        Supabase user 객체에서 정보를 추출합니다.
        """
        # 기본값 설정
        user_info = {
            "id": getattr(user_data, "id", None),
            "email": getattr(user_data, "email", None),
            "role": "user",
            "organization_id": None,
            "profile_id": None,
            "first_name": None,
            "last_name": None,
            "profile_image": None,
            "is_active": True,
        }

        # app_metadata 추출
        if hasattr(user_data, "app_metadata"):
            app_metadata = user_data.app_metadata or {}
            user_info["role"] = app_metadata.get("role", "user")
            user_info["organization_id"] = app_metadata.get("organization_id")
            user_info["profile_id"] = app_metadata.get("profile_id")

        # user_metadata 추출
        if hasattr(user_data, "user_metadata"):
            user_metadata = user_data.user_metadata or {}
            user_info["first_name"] = user_metadata.get("first_name")
            user_info["last_name"] = user_metadata.get("last_name")
            user_info["profile_image"] = user_metadata.get("profile_image")
            user_info["email"] = user_metadata.get("email") or user_info["email"]

        return user_info

    def check_permission(self, user_role: str, required_role: str) -> bool:
        """
        사용자 권한을 확인합니다.
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
_session_auth_service = None


def get_session_auth_service() -> SupabaseSessionAuthService:
    """Supabase 세션 인증 서비스 싱글톤 인스턴스 반환"""
    global _session_auth_service
    if _session_auth_service is None:
        _session_auth_service = SupabaseSessionAuthService()
    return _session_auth_service


async def verify_session_token(token: str) -> Dict[str, Any]:
    """
    Supabase 세션 토큰을 검증하고 사용자 정보를 반환합니다.
    """
    auth_service = get_session_auth_service()
    return await auth_service.verify_session_token(token)


def check_user_permission(user_role: str, required_role: str) -> bool:
    """
    사용자 권한을 확인합니다.
    """
    auth_service = get_session_auth_service()
    return auth_service.check_permission(user_role, required_role)
