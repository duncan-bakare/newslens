import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional
import logging

load_dotenv()

logger = logging.getLogger(__name__)

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
            .limit(1)
            .execute()
        )
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception:
        return None


def save_analysis(data: dict) -> None:
    """
    Save a fresh analysis result to the database.
    """
    try:
        supabase.table("analyses").insert(data).execute()
    except Exception as e:
        logger.warning(f"Failed to cache result: {str(e)}") 
