import httpx
import os
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
SUMMARY_MODEL = "facebook/bart-large-cnn"
HF_BASE_URL = "https://api-inference.huggingface.co/models"


def summarise(text: str) -> str:
    """
    Generate a neutral summary of the article text.
    
    BART-CNN was trained on news article summarisation —
    it's one of the best models for this specific task.
    It produces concise, neutral summaries that capture
    the core facts without the original article's framing.
    """
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    url = f"{HF_BASE_URL}/{SUMMARY_MODEL}"

    payload = {
        "inputs": text[:1024],  # BART-CNN has a 1024 token limit
        "parameters": {
            "max_length": 130,
            "min_length": 50,
            "do_sample": False  # Deterministic output — same input = same summary
        }
    }

    response = httpx.post(url, headers=headers, json=payload, timeout=60.0)

    if response.status_code == 503:
        return "Summary temporarily unavailable — model is warming up."

    if response.status_code != 200:
        return "Summary could not be generated."

    result = response.json()

    # Result format: [{"summary_text": "..."}]
    return result[0].get("summary_text", "Summary unavailable.")
