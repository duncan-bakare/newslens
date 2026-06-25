from newspaper import Article
from urllib.parse import urlparse
from typing import Optional
import logging
import httpx

logger = logging.getLogger(__name__)

# Sites known to block scrapers or require JavaScript
KNOWN_PAYWALLS = [
    "wsj.com", "ft.com", "thetimes.co.uk", "telegraph.co.uk",
    "nytimes.com", "washingtonpost.com", "economist.com",
    "bloomberg.com", "theathletic.com"
]

# Minimum article length to be considered valid
MIN_ARTICLE_LENGTH = 150


class ScraperError(Exception):
    pass


class PaywallError(ScraperError):
    pass


def _is_likely_paywalled(url: str) -> bool:
    domain = urlparse(url).netloc.replace("www.", "")
    return any(pw in domain for pw in KNOWN_PAYWALLS)


def scrape_article(url: str) -> dict:
    """
    Scrape and extract article content from a URL.
    Raises ScraperError or PaywallError with clear user-facing messages.
    """

    # Warn early about known paywalls
    if _is_likely_paywalled(url):
        raise PaywallError(
            "This site is behind a paywall and cannot be scraped. "
            "Try a free news source like BBC, Reuters, or The Guardian."
        )

    try:
        article = Article(url)
        article.download()
        article.parse()
    except Exception as e:
        logger.error(f"Download/parse failed for {url}: {str(e)}")
        raise ScraperError(
            "Could not access this article. The site may be blocking "
            "automated access or the URL may be invalid."
        )

    # Validate content quality
    if not article.text:
        raise ScraperError(
            "No article text could be extracted. The page may require "
            "JavaScript to load or may be behind a login."
        )

    if len(article.text.strip()) < MIN_ARTICLE_LENGTH:
        raise ScraperError(
            f"Article text is too short to analyse "
            f"({len(article.text.strip())} characters). "
            "This may not be a standard news article."
        )

    source = urlparse(url).netloc.replace("www.", "")

    return {
        "headline": article.title or "Untitled article",
        "text": article.text.strip(),
        "source": source,
        "authors": article.authors or [],
    }


def truncate_for_api(text: str, max_chars: int = 1500) -> str:
    """
    Truncate text for API calls.
    Takes the first max_chars characters — the lede and opening
    paragraphs carry the most framing and bias signal.
    """
    if len(text) <= max_chars:
        return text
    # Try to cut at a sentence boundary
    truncated = text[:max_chars]
    last_period = truncated.rfind(". ")
    if last_period > max_chars * 0.8:
        return truncated[:last_period + 1]
    return truncated