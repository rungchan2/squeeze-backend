from supabase import create_client, Client
from typing import Optional
import structlog
from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client singleton"""
    global _supabase_client

    if _supabase_client is None:
        try:
            # Simple client creation as per documentation
            _supabase_client = create_client(
                settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    return _supabase_client


async def check_supabase_connection() -> bool:
    """Check if Supabase connection is healthy"""
    try:
        client = get_supabase_client()
        # Try to fetch from a system table to verify connection
        response = client.table("profiles").select("id").limit(1).execute()
        return True
    except Exception as e:
        logger.error(f"Supabase connection check failed: {e}")
        return False
