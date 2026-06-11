import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Initialise the Supabase client once at module load
# This is a singleton pattern — one connection reused across all requests
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


def get_cached_analysis(url: str) -> Optional[dict]:
    """
    Check if we've already analysed this URL.
    Returns the cached result or None.
    """
    try:
        result = (
            supabase.table("analyses")
            .select("*")
            .eq("url", url)
            .single()
            .execute()
        )
        return result.data
    except Exception:
        # If the record doesn't exist, Supabase raises an error
        # We treat that as a cache miss, not a real error
        return None


def save_analysis(data: dict) -> None:
    """
    Save a fresh analysis result to the database.
    """
    try:
        supabase.table("analyses").insert(data).execute()
    except Exception as e:
        # Caching failures shouldn't crash the app
        # Log it but let the request succeed anyway
        logger.warning(f"Failed to cache result: {str(e)}") 
