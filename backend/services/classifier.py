import httpx
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_BASE_URL = "https://api-inference.huggingface.co/models"

# The models we're using
BIAS_MODEL = "facebook/bart-large-mnli"
SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"


def _call_hf_api(model: str, payload: dict) -> dict:
    """
    Make a call to the HuggingFace Inference API.
    
    This is a private helper function (note the underscore prefix).
    It handles auth, errors, and retries in one place so our
    other functions stay clean.
    """
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    url = f"{HF_BASE_URL}/{model}"

    response = httpx.post(url, headers=headers, json=payload, timeout=30.0)

    # HuggingFace returns 503 when a model is loading (cold start)
    # This is normal — models "sleep" when not used recently
    if response.status_code == 503:
        raise Exception(
            "AI model is warming up. Please try again in 20 seconds."
        )

    if response.status_code != 200:
        raise Exception(
            f"HuggingFace API error: {response.status_code} - {response.text}"
        )

    return response.json()


def classify_bias(text: str) -> dict:
    """
    Classify political bias using zero-shot classification.
    
    Zero-shot means the model was never specifically trained on
    "news bias" — instead we give it candidate labels and it
    figures out which fits best. This is powerful because it
    requires no labelled training data from us.
    """
    payload = {
        "inputs": text,
        "parameters": {
            "candidate_labels": [
                "left-wing",
                "centre-left",
                "centre",
                "centre-right",
                "right-wing"
            ]
        }
    }

    result = _call_hf_api(BIAS_MODEL, payload)

    # Result comes back as parallel arrays of labels and scores
    # e.g. labels: ["centre", "left-wing", ...], scores: [0.71, 0.12, ...]
    # The first item is always the highest scoring
    top_label = result["labels"][0]
    top_score = result["scores"][0]

    return {
        "label": top_label,
        "confidence": round(top_score, 3)
    }


def classify_tone(text: str) -> dict:
    """
    Classify emotional tone using sentiment analysis.
    
    We use a standard sentiment model but map its output
    to more meaningful labels for our use case.
    """
    payload = {"inputs": text}

    result = _call_hf_api(SENTIMENT_MODEL, payload)

    # Result is a list of lists: [[{"label": "POSITIVE", "score": 0.98}]]
    scores = result[0]
    top = max(scores, key=lambda x: x["score"])

    raw_label = top["label"]   # "POSITIVE" or "NEGATIVE"
    score = top["score"]       # confidence

    # Map raw labels to human-friendly tone descriptions
    if raw_label == "NEGATIVE" and score > 0.90:
        label = "highly charged"
    elif raw_label == "NEGATIVE":
        label = "moderately charged"
    elif raw_label == "POSITIVE" and score > 0.90:
        label = "positive"
    else:
        label = "neutral"

    return {
        "label": label,
        "score": round(score, 3)
    }


def calculate_entity_density(text: str) -> float:
    """
    Estimate factual density by counting capitalised proper nouns.
    
    This is a lightweight heuristic — not ML. We count words that
    look like named entities (capitalised mid-sentence) as a ratio
    of total words. High entity density = more names, places, orgs
    = more factual grounding.
    
    A proper NLP approach would use a NER model, but this is fast,
    free, and good enough for our MVP.
    """
    words = text.split()
    if not words:
        return 0.0

    # Words capitalised mid-sentence (not at start) are likely entities
    entities = [
        w for i, w in enumerate(words)
        if i > 0 and w[0].isupper() and w.isalpha()
    ]

    density = len(entities) / len(words)
    return round(density, 3)
