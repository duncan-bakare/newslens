import os
import anthropic
import logging

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def summarise(text: str) -> str:
    """
    Generate a neutral, bias-free summary using Claude.
    
    The prompt explicitly instructs Claude to strip out emotionally
    charged language and present only the core facts.
    """
    prompt = f"""Summarise the following news article in 2-3 sentences.

Rules:
- Use neutral, factual language only
- Remove emotional framing, loaded words, and opinion
- Focus on who, what, when, where
- Do not start with "The article" or "This article"
- Write as if you are a neutral wire service journalist

Article text:
{text}

Neutral summary:"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()