"""
Supabase 토큰 추출 서비스
세션 데이터에서 실제 JWT 토큰을 추출합니다.
"""
import json
import base64
from typing import Dict, Any
import structlog
from app.core.exceptions import AuthenticationError

logger = structlog.get_logger()


class SupabaseTokenExtractor:
    """Supabase 세션 토큰에서 실제 JWT를 추출하는 서비스"""

    def extract_jwt_from_session_token(self, session_token: str) -> str:
        """
        Supabase 세션 토큰에서 실제 JWT access_token을 추출합니다.

        Args:
            session_token: base64- 형태의 세션 토큰

        Returns:
            실제 JWT access_token

        Raises:
            AuthenticationError: 토큰 추출 실패 시
        """
        try:
            # base64- prefix 제거
            if session_token.startswith("base64-"):
                session_token = session_token[7:]

            # Base64 디코딩
            try:
                # URL-safe base64 디코딩 시도
                decoded = base64.urlsafe_b64decode(
                    session_token + "=" * (4 - len(session_token) % 4)
                )
            except:
                # 일반 base64 디코딩 시도
                decoded = base64.b64decode(
                    session_token + "=" * (4 - len(session_token) % 4)
                )

            # JSON 파싱
            session_data = json.loads(decoded.decode("utf-8"))

            # access_token 추출
            access_token = session_data.get("access_token")

            if not access_token:
                raise AuthenticationError("No access_token found in session")

            logger.debug(
                f"Successfully extracted JWT from session token (length: {len(access_token)})"
            )
            return access_token

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse session JSON: {e}")
            raise AuthenticationError("Invalid session token format")
        except Exception as e:
            logger.error(f"Token extraction error: {e}")
            raise AuthenticationError("Failed to extract token")

    def extract_user_from_session_token(self, session_token: str) -> Dict[str, Any]:
        """
        세션 토큰에서 사용자 정보를 직접 추출합니다.

        Args:
            session_token: base64- 형태의 세션 토큰

        Returns:
            사용자 정보
        """
        try:
            # base64- prefix 제거
            if session_token.startswith("base64-"):
                session_token = session_token[7:]

            # Base64 디코딩
            try:
                decoded = base64.urlsafe_b64decode(
                    session_token + "=" * (4 - len(session_token) % 4)
                )
            except:
                decoded = base64.b64decode(
                    session_token + "=" * (4 - len(session_token) % 4)
                )

            # JSON 파싱
            session_data = json.loads(decoded.decode("utf-8"))

            # user 객체 추출
            user_data = session_data.get("user", {})

            if not user_data:
                raise AuthenticationError("No user data found in session")

            # 사용자 정보 추출
            user_info = {
                "id": user_data.get("id"),
                "email": user_data.get("email"),
                "role": "user",  # 기본값
                "organization_id": None,
                "profile_id": user_data.get("id"),
                "first_name": None,
                "last_name": None,
                "profile_image": None,
                "is_active": True,
            }

            # app_metadata에서 role 추출
            app_metadata = user_data.get("app_metadata", {})
            if app_metadata:
                user_info["role"] = app_metadata.get("role", "user")
                user_info["organization_id"] = app_metadata.get("organization_id")

            # user_metadata에서 개인정보 추출
            user_metadata = user_data.get("user_metadata", {})
            if user_metadata:
                user_info["first_name"] = user_metadata.get(
                    "first_name"
                ) or user_metadata.get("name")
                user_info["last_name"] = user_metadata.get("last_name")
                user_info["profile_image"] = user_metadata.get(
                    "avatar_url"
                ) or user_metadata.get("picture")

            logger.debug(
                f"Extracted user info: {user_info['email']} (Role: {user_info['role']})"
            )
            return user_info

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse session JSON: {e}")
            raise AuthenticationError("Invalid session token format")
        except Exception as e:
            logger.error(f"User extraction error: {e}")
            raise AuthenticationError("Failed to extract user info")


# 싱글톤 인스턴스
_token_extractor = None


def get_token_extractor() -> SupabaseTokenExtractor:
    """토큰 추출기 싱글톤 인스턴스 반환"""
    global _token_extractor
    if _token_extractor is None:
        _token_extractor = SupabaseTokenExtractor()
    return _token_extractor
