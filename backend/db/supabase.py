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


REASONING_COLUMNS = ("bias_reasoning", "tone_reasoning")


def save_analysis(data: dict) -> None:
    """
    Save a fresh analysis result to the database.

    If the insert fails and the row included the reasoning columns, retry
    without them. That keeps caching working on a database that has not had
    backend/db/migrations/001_add_reasoning_columns.sql applied yet, instead of
    silently dropping every cache write.
    """
    try:
        supabase.table("analyses").insert(data).execute()
        return
    except Exception as e:
        logger.warning(f"Failed to cache result: {str(e)}")

    if any(col in data for col in REASONING_COLUMNS):
        fallback = {k: v for k, v in data.items() if k not in REASONING_COLUMNS}
        try:
            supabase.table("analyses").insert(fallback).execute()
            logger.warning(
                "Cached without reasoning columns. Apply "
                "backend/db/migrations/001_add_reasoning_columns.sql to store them."
            )
        except Exception as e:
            logger.warning(f"Fallback cache write also failed: {str(e)}")
