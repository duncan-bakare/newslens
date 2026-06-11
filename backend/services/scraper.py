import httpx
from newspaper import Article
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Raised when we can't extract an article."""
    pass


def scrape_article(url: str) -> dict:
    """
    Scrape a news article from a URL.
    
    Returns a dict with:
    - headline: article title
    - text: cleaned body text
    - source: domain name
    - authors: list of authors
    
    Raises ScraperError if extraction fails.
    """
    try:
        article = Article(url)
        article.download()
        article.parse()

        # Validate we actually got content
        if not article.text or len(article.text.strip()) < 100:
            raise ScraperError(
                "Could not extract article text. "
                "The page may be paywalled or JavaScript-rendered."
            )

        # Extract domain as source name
        # e.g. "https://www.bbc.com/news/..." → "bbc.com"
        from urllib.parse import urlparse
        source = urlparse(url).netloc.replace("www.", "")

        return {
            "headline": article.title or "Unknown headline",
            "text": article.text.strip(),
            "source": source,
            "authors": article.authors,
        }

    except ScraperError:
        raise  # Re-raise our own errors as-is

    except Exception as e:
        logger.error(f"Scraping failed for {url}: {str(e)}")
        raise ScraperError(
            f"Failed to scrape article. "
            f"The site may be blocking automated access."
        )


def truncate_for_api(text: str, max_chars: int = 1500) -> str:
    """
    Truncate text for API calls.
    
    HuggingFace models have token limits. Most news articles
    are longer than what these models can process in one call.
    We take the first 1500 characters which captures the
    most important/biased part — the lede and opening paragraphs.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars]
