from fastapi import APIRouter, HTTPException
from backend.models.schemas import AnalyseRequest, AnalyseResponse
from backend.services.scraper import scrape_article, truncate_for_api, ScraperError
from backend.services.classifier import classify_bias, classify_tone, calculate_entity_density
from backend.services.summariser import summarise
from backend.db.supabase import get_cached_analysis, save_analysis
from datetime import datetime, timezone
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyse", response_model=AnalyseResponse)
async def analyse_article(request: AnalyseRequest):
    """
    Main endpoint. Takes a URL, returns a full scorecard.
    
    Flow:
    1. Check cache
    2. Scrape article
    3. Run ML pipeline
    4. Save to cache
    5. Return result
    """
    url_str = str(request.url)

    # ── Step 1: Check cache ──────────────────────────────────────
    cached = get_cached_analysis(url_str)
    if cached:
        logger.info(f"Cache hit for {url_str}")
        return AnalyseResponse(
            url=cached["url"],
            headline=cached["headline"],
            source=cached["source"],
            bias={"label": cached["bias_label"], "confidence": cached["bias_score"]},
            tone={"label": cached["tone_label"], "score": cached["tone_score"]},
            entity_density=cached["entity_density"],
            summary=cached["summary"],
            analysed_at=cached["analysed_at"],
            cached=True
        )

    # ── Step 2: Scrape article ───────────────────────────────────
    try:
        article = scrape_article(url_str)
    except ScraperError as e:
        raise HTTPException(status_code=422, detail=str(e))

    truncated_text = truncate_for_api(article["text"])

    # ── Step 3: Run ML pipeline ──────────────────────────────────
    try:
        bias = classify_bias(truncated_text)
        tone = classify_tone(truncated_text)
        entity_density = calculate_entity_density(article["text"])
        summary = summarise(truncated_text)
    except Exception as e:
        logger.error(f"ML pipeline failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )

    # ── Step 4: Save to cache ────────────────────────────────────
    now = datetime.now(timezone.utc)
    save_analysis({
        "url": url_str,
        "headline": article["headline"],
        "source": article["source"],
        "bias_label": bias["label"],
        "bias_score": bias["confidence"],
        "tone_label": tone["label"],
        "tone_score": tone["score"],
        "entity_density": entity_density,
        "summary": summary,
        "full_text": article["text"][:5000],  # Store first 5000 chars
        "analysed_at": now.isoformat()
    })

    # ── Step 5: Return result ────────────────────────────────────
    return AnalyseResponse(
        url=url_str,
        headline=article["headline"],
        source=article["source"],
        bias=bias,
        tone=tone,
        entity_density=entity_density,
        summary=summary,
        analysed_at=now,
        cached=False
    ) 
