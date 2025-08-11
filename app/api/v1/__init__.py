"""
API v1 router configuration
"""
from fastapi import APIRouter
from app.core.config import get_settings
from app.api.v1 import analyze, health

settings = get_settings()

# Create v1 API router
api_router = APIRouter()

# Include domain routers
api_router.include_router(analyze.router, prefix="/analyze", tags=["analysis"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
