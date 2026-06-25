from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class AnalyseRequest(BaseModel):
    url: HttpUrl


class BiasResult(BaseModel):
    label: str
    confidence: float
    reasoning: Optional[str] = ""


class ToneResult(BaseModel):
    label: str
    score: float
    reasoning: Optional[str] = ""


class AnalyseResponse(BaseModel):
    url: str
    headline: str
    source: str
    bias: BiasResult
    tone: ToneResult
    entity_density: float
    summary: str
    analysed_at: datetime
    cached: bool


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
