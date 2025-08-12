from fastapi import FastAPI
from contextlib import asynccontextmanager
import structlog
from app.core.config import get_settings
from app.core.middleware import setup_cors, LoggingMiddleware, ErrorHandlingMiddleware
from app.db.redis import close_redis_client, check_redis_connection
from app.db.supabase import check_supabase_connection
from app.api.v1 import api_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown with serverless optimization"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Check if running in serverless environment
    import os
    is_serverless = os.getenv("VERCEL") is not None
    
    if is_serverless:
        logger.info("Running in serverless environment (Vercel)")
        # In serverless, skip connection testing on startup to reduce cold start time
        logger.info("Skipping connection tests in serverless environment")
    else:
        # Test database connections in traditional deployment
        logger.info("Testing database connections...")
        redis_ok = await check_redis_connection()
        supabase_ok = await check_supabase_connection()

        if redis_ok:
            logger.info("Redis connection established")
        else:
            logger.warning("Redis connection failed - caching will be disabled")

        if supabase_ok:
            logger.info("Supabase connection established")
        else:
            logger.error("Supabase connection failed")

    yield

    # Shutdown - always clean up Redis connections
    logger.info("Shutting down application")
    await close_redis_client()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Setup middlewares
setup_cors(app)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
    }


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)
