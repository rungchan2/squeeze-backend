"""
커스텀 예외 클래스 정의
API에서 사용할 도메인별 예외를 정의합니다.
"""
from fastapi import HTTPException, status
from typing import Any, Optional, Dict


class SqueezeException(HTTPException):
    """Squeeze API 기본 예외 클래스"""

    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class AuthenticationError(SqueezeException):
    """인증 실패 예외"""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(SqueezeException):
    """권한 부족 예외"""

    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundError(SqueezeException):
    """리소스를 찾을 수 없음 예외"""

    def __init__(self, resource: str, id: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id {id} not found",
        )


class ValidationError(SqueezeException):
    """입력 검증 실패 예외"""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class TextAnalysisError(SqueezeException):
    """텍스트 분석 실패 예외"""

    def __init__(self, detail: str = "Text analysis failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )


class CacheError(SqueezeException):
    """캐시 관련 예외 (서비스는 계속 동작)"""

    def __init__(self, detail: str = "Cache operation failed"):
        # 캐시 에러는 로깅만 하고 서비스는 계속 동작
        super().__init__(
            status_code=status.HTTP_200_OK, detail=detail  # 클라이언트에는 성공으로 응답
        )


class DatabaseError(SqueezeException):
    """데이터베이스 관련 예외"""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
