"""
Supabase 통합 인증 서비스
세션 토큰에서 JWT 추출 또는 직접 사용자 정보 추출
"""
from typing import Dict, Any
import structlog
from jose import jwt
import json
import base64
from app.core.exceptions import AuthenticationError
from app.services.supabase_token_extractor import get_token_extractor
from app.services.supabase_session_auth import get_session_auth_service

logger = structlog.get_logger()


class SupabaseUnifiedAuthService:
    """Supabase 통합 인증 서비스"""

    def __init__(self):
        self.token_extractor = get_token_extractor()
        self.session_auth = get_session_auth_service()

    async def authenticate_token(self, token: str) -> Dict[str, Any]:
        """
        토큰을 인증하고 사용자 정보를 반환합니다.
        여러 방법을 순차적으로 시도합니다.

        Args:
            token: 인증 토큰 (다양한 형식 지원)

        Returns:
            사용자 정보

        Raises:
            AuthenticationError: 모든 인증 방법 실패 시
        """
        logger.debug(f"Attempting to authenticate token (length: {len(token)})")

        # Method 1: JWT access_token 직접 처리
        try:
            # Bearer prefix 제거
            clean_token = token
            if token.startswith("Bearer "):
                clean_token = token[7:]

            # JWT 토큰인지 확인 (JWT는 보통 3개의 점으로 구분된 부분을 가짐)
            if clean_token.count(".") == 2 and not clean_token.startswith("base64-"):
                # JWT 디코드 시도
                decoded_jwt = jwt.decode(
                    clean_token,
                    key="",
                    options={
                        "verify_signature": False,
                        "verify_aud": False,
                        "verify_iss": False,
                        "verify_exp": False,
                    },
                )

                # 사용자 정보 추출
                user_info = {
                    "id": decoded_jwt.get("sub"),
                    "email": decoded_jwt.get("email"),
                    "role": "user",  # 기본값
                    "organization_id": None,
                    "profile_id": decoded_jwt.get("sub"),
                    "first_name": None,
                    "last_name": None,
                    "profile_image": None,
                    "is_active": True,
                }

                # app_metadata에서 role과 organization_id 추출
                app_metadata = decoded_jwt.get("app_metadata", {})
                if app_metadata:
                    user_info["role"] = app_metadata.get("role", "user")
                    user_info["organization_id"] = app_metadata.get("organization_id")

                # user_metadata에서 개인정보 추출
                user_metadata = decoded_jwt.get("user_metadata", {})
                if user_metadata:
                    user_info["first_name"] = user_metadata.get(
                        "first_name"
                    ) or user_metadata.get("name")
                    user_info["last_name"] = user_metadata.get("last_name")
                    user_info["profile_image"] = (
                        user_metadata.get("profile_image")
                        or user_metadata.get("avatar_url")
                        or user_metadata.get("picture")
                    )

                logger.info(
                    f"Method 1 success: Direct JWT decode - {user_info['email']} (Role: {user_info['role']})"
                )
                return user_info

        except Exception as e:
            logger.debug(f"Method 1 failed (Direct JWT decode): {e}")

        # Method 2: Bearer 토큰 처리 (base64 인코딩된 세션 데이터)
        try:
            # Bearer prefix 제거
            if token.startswith("Bearer "):
                encoded_token = token[7:]
            elif token.startswith("base64-"):
                # base64- prefix 제거
                encoded_token = token[7:]
            else:
                encoded_token = token

            # base64로 인코딩된 세션 데이터인지 확인 (길이가 충분히 긴 경우)
            if len(encoded_token) > 100:
                # Base64 디코딩
                try:
                    # URL-safe base64 디코딩 시도
                    decoded = base64.urlsafe_b64decode(
                        encoded_token + "=" * (4 - len(encoded_token) % 4)
                    )
                except:
                    # 일반 base64 디코딩 시도
                    decoded = base64.b64decode(
                        encoded_token + "=" * (4 - len(encoded_token) % 4)
                    )

                # JSON 파싱
                session_data = json.loads(decoded.decode("utf-8"))

                # access_token 추출
                access_token = session_data.get("access_token")

                if access_token:
                    # JWT 디코드 (모든 검증 건너뛰기)
                    decoded_jwt = jwt.decode(
                        access_token,
                        key="",
                        options={
                            "verify_signature": False,
                            "verify_aud": False,
                            "verify_iss": False,
                            "verify_exp": False,
                        },
                    )

                    # 사용자 정보 추출
                    user_info = {
                        "id": decoded_jwt.get("sub"),
                        "email": decoded_jwt.get("email"),
                        "role": "user",  # 기본값
                        "organization_id": None,
                        "profile_id": decoded_jwt.get("sub"),
                        "first_name": None,
                        "last_name": None,
                        "profile_image": None,
                        "is_active": True,
                    }

                    # app_metadata에서 role과 organization_id 추출
                    app_metadata = decoded_jwt.get("app_metadata", {})
                    if app_metadata:
                        user_info["role"] = app_metadata.get("role", "user")
                        user_info["organization_id"] = app_metadata.get(
                            "organization_id"
                        )

                    # user_metadata에서 개인정보 추출
                    user_metadata = decoded_jwt.get("user_metadata", {})
                    if user_metadata:
                        user_info["first_name"] = user_metadata.get(
                            "first_name"
                        ) or user_metadata.get("name")
                        user_info["last_name"] = user_metadata.get("last_name")
                        user_info["profile_image"] = (
                            user_metadata.get("profile_image")
                            or user_metadata.get("avatar_url")
                            or user_metadata.get("picture")
                        )

                    logger.info(
                        f"Method 2 success: JWT decode from Bearer token - {user_info['email']} (Role: {user_info['role']})"
                    )
                    return user_info

        except Exception as e:
            logger.debug(f"Method 2 failed (JWT decode from Bearer token): {e}")

        # Method 3: 세션 토큰에서 사용자 정보 직접 추출 (기존 방식)
        try:
            if token.startswith("base64-") and len(token) > 200:  # 긴 세션 토큰
                user_info = self.token_extractor.extract_user_from_session_token(token)
                logger.info("Method 3 success: Direct user extraction from session")
                return user_info
        except Exception as e:
            logger.debug(f"Method 3 failed (direct user extraction): {e}")

        # Method 4: 세션 토큰에서 JWT 추출 후 Supabase API 사용
        try:
            if token.startswith("base64-"):
                jwt_token = self.token_extractor.extract_jwt_from_session_token(token)
                user_info = await self.session_auth.verify_session_token(jwt_token)
                logger.info("Method 4 success: JWT extraction + API verification")
                return user_info
        except Exception as e:
            logger.debug(f"Method 4 failed (JWT extraction): {e}")

        # Method 5: 토큰을 그대로 Supabase API에 전달
        try:
            user_info = await self.session_auth.verify_session_token(token)
            logger.info("Method 5 success: Direct API verification")
            return user_info
        except Exception as e:
            logger.debug(f"Method 5 failed (direct API): {e}")

        # 모든 방법 실패
        raise AuthenticationError("Unable to authenticate token with any method")

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
_unified_auth_service = None


def get_unified_auth_service() -> SupabaseUnifiedAuthService:
    """통합 인증 서비스 싱글톤 인스턴스 반환"""
    global _unified_auth_service
    if _unified_auth_service is None:
        _unified_auth_service = SupabaseUnifiedAuthService()
    return _unified_auth_service


async def authenticate_token(token: str) -> Dict[str, Any]:
    """
    토큰을 인증하고 사용자 정보를 반환합니다.
    """
    auth_service = get_unified_auth_service()
    return await auth_service.authenticate_token(token)


def check_user_permission(user_role: str, required_role: str) -> bool:
    """
    사용자 권한을 확인합니다.
    """
    auth_service = get_unified_auth_service()
    return auth_service.check_permission(user_role, required_role)
