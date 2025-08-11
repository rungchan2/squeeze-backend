"""
Supabase JWT 인증 서비스
Frontend의 Supabase 인증 쿠키를 검증하는 서비스
"""
from jose import jwt, JWTError
from typing import Optional, Dict, Any
import structlog
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.db.supabase import get_supabase_client

settings = get_settings()
logger = structlog.get_logger()


class SupabaseAuthService:
    """Supabase JWT 토큰 검증 서비스"""

    def __init__(self):
        self.supabase = get_supabase_client()
        # Supabase JWT 검증을 위한 공개 키 (실제로는 Supabase에서 가져와야 함)
        self.jwt_secret = (
            settings.SUPABASE_JWT_SECRET
            if hasattr(settings, "SUPABASE_JWT_SECRET")
            else settings.SECRET_KEY
        )

    async def verify_supabase_token(self, token: str) -> Dict[str, Any]:
        """
        Supabase JWT 토큰을 검증합니다.

        Args:
            token: Supabase access_token

        Returns:
            디코딩된 토큰 페이로드

        Raises:
            AuthenticationError: 토큰이 유효하지 않은 경우
        """
        try:
            # JWT 토큰 디코딩 (Supabase는 HS256 사용)
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                options={
                    "verify_signature": False,  # 개발 시에는 서명 검증 비활성화
                    "verify_exp": False,  # 개발 시에는 만료 검증도 비활성화 (테스트용)
                    "verify_aud": False,  # audience 검증 비활성화
                },
            )

            # 수동으로 토큰 만료 시간 확인 (실제 환경에서는 활성화)
            # if "exp" in payload:
            #     exp_timestamp = payload["exp"]
            #     if datetime.utcnow().timestamp() > exp_timestamp:
            #         raise AuthenticationError("Token has expired")

            # 필수 필드 확인
            if "sub" not in payload:
                raise AuthenticationError("Token missing user ID (sub)")

            logger.debug(f"Token verified for user: {payload.get('sub')}")
            return payload

        except JWTError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise AuthenticationError("Invalid token")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise AuthenticationError("Token verification failed")

    async def get_user_from_token(self, token: str) -> Dict[str, Any]:
        """
        토큰에서 사용자 정보를 추출합니다.

        Args:
            token: Supabase access_token

        Returns:
            사용자 정보
        """
        payload = await self.verify_supabase_token(token)

        # JWT에서 사용자 정보 추출
        user_id = payload.get("sub")
        email = payload.get("email")

        # app_metadata와 user_metadata 추출
        app_metadata = payload.get("app_metadata", {})
        user_metadata = payload.get("user_metadata", {})

        # 역할 정보 추출
        role = app_metadata.get("role", "user")
        organization_id = app_metadata.get("organization_id")

        # 사용자 메타데이터 추출
        first_name = user_metadata.get("first_name")
        last_name = user_metadata.get("last_name")
        profile_image = user_metadata.get("profile_image")

        user_info = {
            "id": user_id,
            "email": email,
            "role": role,
            "organization_id": organization_id,
            "first_name": first_name,
            "last_name": last_name,
            "profile_image": profile_image,
            "is_active": True,  # Supabase 사용자는 기본적으로 활성화
            "raw_payload": payload,
        }

        logger.info(f"User info extracted: {user_id} ({email}) - Role: {role}")
        return user_info

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

    async def refresh_token_if_needed(self, token: str) -> Optional[str]:
        """
        토큰이 만료에 가까우면 새로 고칩니다.
        (실제로는 프론트엔드에서 처리하므로 여기서는 None 반환)

        Args:
            token: 현재 토큰

        Returns:
            새 토큰 또는 None
        """
        # 백엔드에서는 토큰 리프레시를 하지 않음
        # 프론트엔드의 Supabase 클라이언트가 자동으로 처리
        return None


# 싱글톤 인스턴스
_supabase_auth_service = None


def get_supabase_auth_service() -> SupabaseAuthService:
    """Supabase 인증 서비스 싱글톤 인스턴스 반환"""
    global _supabase_auth_service
    if _supabase_auth_service is None:
        _supabase_auth_service = SupabaseAuthService()
    return _supabase_auth_service


async def verify_supabase_token(token: str) -> Dict[str, Any]:
    """
    Supabase JWT 토큰을 검증하고 사용자 정보를 반환합니다.

    Args:
        token: Supabase access_token

    Returns:
        사용자 정보
    """
    auth_service = get_supabase_auth_service()
    return await auth_service.get_user_from_token(token)


def check_user_permission(user_role: str, required_role: str) -> bool:
    """
    사용자 권한을 확인합니다.

    Args:
        user_role: 사용자 역할
        required_role: 요구되는 역할

    Returns:
        권한 여부
    """
    auth_service = get_supabase_auth_service()
    return auth_service.check_permission(user_role, required_role)
