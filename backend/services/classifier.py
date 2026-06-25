import os
import anthropic
import json
import logging

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def classify_bias(text: str) -> dict:
    """
    Classify political bias using Claude with improved prompting.
    Forces a committed assessment rather than defaulting to centre.
    """
    prompt = f"""You are a media bias analyst with expertise in political language and framing.

Analyse the political bias in this news article text. Look for:
- Word choices that favour one political perspective
- Which groups or policies are framed positively vs negatively  
- Whose voices and quotes are included or excluded
- What context is provided or omitted
- Emotional language that signals political alignment

You MUST commit to a specific assessment. Do not default to "centre" unless the article is genuinely balanced from multiple angles.

Return ONLY a valid JSON object, no other text:
{{
  "label": "one of: left-wing, centre-left, centre, centre-right, right-wing",
  "confidence": "float 0.0-1.0 — be bold, most articles score above 0.6",
  "reasoning": "one sentence citing specific language or framing choices"
}}

Article text to analyse:
{text}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if Claude adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        result = json.loads(raw)
        return {
            "label": result.get("label", "centre"),
            "confidence": round(float(result.get("confidence", 0.5)), 3),
            "reasoning": result.get("reasoning", "")
        }
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Failed to parse bias response: {raw}")
        return {"label": "centre", "confidence": 0.5, "reasoning": ""}


def classify_tone(text: str) -> dict:
    """
    Classify emotional tone with improved prompting.
    """
    prompt = f"""You are a linguistic analyst specialising in media tone and emotional language.

Analyse the emotional tone of this news article. Look for:
- Emotionally charged adjectives and adverbs
- Inflammatory or sensationalist language
- Calm, measured, factual reporting style
- Fear, anger, or outrage-inducing framing
- Positive or celebratory framing

Score the emotional intensity honestly. Most news articles are NOT neutral — 
they score between 0.3 and 0.8. Only pure wire-service reporting scores below 0.3.

Return ONLY a valid JSON object, no other text:
{{
  "label": "one of: neutral, moderately charged, highly charged, positive",
  "score": "float 0.0-1.0 where 0.0 is completely factual and 1.0 is extremely emotional",
  "reasoning": "one sentence citing specific language examples"
}}

Article text to analyse:
{text}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        result = json.loads(raw)
        return {
            "label": result.get("label", "neutral"),
            "score": round(float(result.get("score", 0.5)), 3),
            "reasoning": result.get("reasoning", "")
        }
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Failed to parse tone response: {raw}")
        return {"label": "neutral", "score": 0.5, "reasoning": ""}


def calculate_entity_density(text: str) -> float:
    """
    Estimate factual density by counting capitalised proper nouns.
    """
    words = text.split()
    if not words:
        return 0.0

    entities = [
        w for i, w in enumerate(words)
        if i > 0 and w[0].isupper() and w.isalpha()
    ]

    density = len(entities) / len(words)
    return round(min(density, 1.0), 3)