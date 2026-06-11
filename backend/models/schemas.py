from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class AnalyseRequest(BaseModel):
    """What the frontend sends to us."""
    url: HttpUrl


class BiasResult(BaseModel):
    """Political bias analysis result."""
    label: str        # e.g. "centre-left", "right", "centre"
    confidence: float # 0.0 to 1.0


class ToneResult(BaseModel):
    """Emotional tone analysis result."""
    label: str        # e.g. "neutral", "moderately charged"
    score: float      # 0.0 to 1.0


class AnalyseResponse(BaseModel):
    """What we send back to the frontend."""
    url: str
    headline: str
    source: str
    bias: BiasResult
    tone: ToneResult
    entity_density: float
    summary: str
    analysed_at: datetime
    cached: bool      # Was this pulled from cache or freshly analysed?


class ErrorResponse(BaseModel):
    """Structured error we return if something goes wrong."""
    error: str
    detail: Optional[str] = None
