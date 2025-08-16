"""
FastAPI 미들웨어 설정
CORS, 로깅, 에러 핸들링 등의 미들웨어를 정의합니다.
"""
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid
import structlog
from app.core.config import get_settings
from app.db.redis import close_redis_client

logger = structlog.get_logger()
settings = get_settings()


def setup_cors(app):
    """CORS 미들웨어 설정 - localhost 기본 허용 + 환경변수 origins"""
    allowed_origins = settings.cors_origins
    
    logger.info(f"Setting up CORS with origins: {allowed_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization", 
            "Accept",
            "Origin",
            "User-Agent",
            "X-Requested-With",
            "sb-access-token",
            "sb-refresh-token"
        ],
        expose_headers=["*"],
    )


class LoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        # 요청 ID 생성
        request_id = str(uuid.uuid4())

        # 로깅 컨텍스트에 request_id 추가
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # 요청 시작 시간
        start_time = time.time()

        # 요청 로깅
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )

        try:
            # 실제 요청 처리
            response = await call_next(request)

            # 처리 시간 계산
            process_time = time.time() - start_time

            # 응답 로깅
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=f"{process_time:.3f}s",
            )

            # 응답 헤더에 request-id 추가
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # 에러 로깅
            process_time = time.time() - start_time
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time=f"{process_time:.3f}s",
            )
            raise
        finally:
            # 로깅 컨텍스트 정리
            structlog.contextvars.unbind_contextvars("request_id")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """전역 에러 핸들링 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Unhandled exception: {e}", exc_info=True)
            return Response(
                content={"detail": "Internal server error"},
                status_code=500,
                media_type="application/json",
            )
