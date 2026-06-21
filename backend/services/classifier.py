import os
import anthropic
import json
import logging

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def classify_bias(text: str) -> dict:
    """
    Classify political bias using Claude.
    
    We ask Claude to reason about the language, framing, and
    word choices in the article and return a structured JSON result.
    Prompt engineering replaces the zero-shot model entirely.
    """
    prompt = f"""Analyse the political bias of the following news article text.

Return ONLY a JSON object with exactly these fields:
{{
  "label": one of ["left-wing", "centre-left", "centre", "centre-right", "right-wing"],
  "confidence": a float between 0.0 and 1.0,
  "reasoning": a single sentence explaining your assessment
}}

Article text:
{text}

Return only the JSON object, no other text."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    try:
        result = json.loads(raw)
        return {
            "label": result["label"],
            "confidence": round(float(result["confidence"]), 3)
        }
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse bias response: {raw}")
        return {"label": "centre", "confidence": 0.5}


def classify_tone(text: str) -> dict:
    """
    Classify emotional tone using Claude.
    
    We ask Claude to assess how emotionally charged the language
    is — from calm and factual to highly inflammatory.
    """
    prompt = f"""Analyse the emotional tone of the following news article text.

Return ONLY a JSON object with exactly these fields:
{{
  "label": one of ["neutral", "moderately charged", "highly charged", "positive"],
  "score": a float between 0.0 and 1.0 where 0.0 is completely neutral and 1.0 is extremely emotional,
  "reasoning": a single sentence explaining your assessment
}}

Article text:
{text}

Return only the JSON object, no other text."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    try:
        result = json.loads(raw)
        return {
            "label": result["label"],
            "score": round(float(result["score"]), 3)
        }
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse tone response: {raw}")
        return {"label": "neutral", "score": 0.5}


def calculate_entity_density(text: str) -> float:
    """
    Estimate factual density by counting capitalised proper nouns.
    Lightweight heuristic — no API call needed.
    """
    words = text.split()
    if not words:
        return 0.0

    entities = [
        w for i, w in enumerate(words)
        if i > 0 and w[0].isupper() and w.isalpha()
    ]

    density = len(entities) / len(words)
    return round(density, 3)