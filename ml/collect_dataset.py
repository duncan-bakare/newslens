"""Collect an evaluation dataset of news articles from RSS feeds.

Each record gets the SOURCE-LEVEL bias label from ml/sources.yaml. That is a
noisy proxy for the true article-level label (an outlet's individual articles
vary), so treat accuracy numbers as indicative, not exact.

Run from the repo root:
    python -m ml.collect_dataset --per-source 20

The output is a JSONL file (one article per line). Re-running resumes: URLs
already in the file are skipped, so you can top it up over several days.
"""

import argparse
import json
import logging
import time
from pathlib import Path

import feedparser
import yaml

from backend.services.scraper import ScraperError, scrape_article
from ml.labels import LABELS

logger = logging.getLogger("collect")

DEFAULT_SOURCES = Path(__file__).parent / "sources.yaml"
DEFAULT_OUT = Path(__file__).parent / "data" / "articles.jsonl"


def load_sources(path: Path) -> list[dict]:
    sources = yaml.safe_load(path.read_text())["sources"]
    for s in sources:
        if s["label"] not in LABELS:
            raise ValueError(f"{s['name']}: unknown label {s['label']!r}; expected one of {LABELS}")
    return sources


def load_seen_urls(out_path: Path) -> set[str]:
    if not out_path.exists():
        return set()
    with out_path.open() as f:
        return {json.loads(line)["url"] for line in f if line.strip()}


def collect_source(source: dict, per_source: int, seen: set[str], delay: float):
    """Yield up to `per_source` new scraped articles from one outlet's feed."""
    feed = feedparser.parse(source["feed"])
    if not feed.entries:
        logger.warning("%s: feed returned no entries (dead URL or blocked), skipping", source["name"])
        return

    got = 0
    for entry in feed.entries:
        if got >= per_source:
            break
        url = entry.get("link")
        if not url or url in seen:
            continue
        try:
            article = scrape_article(url)
        except ScraperError as e:
            logger.info("%s: skipped %s (%s)", source["name"], url, e)
            continue
        finally:
            time.sleep(delay)  # be polite to the publisher

        got += 1
        seen.add(url)
        yield {
            "url": url,
            "source": source["name"],
            "headline": article["headline"],
            "text": article["text"],
            "true_label": source["label"],
            "aliases": source.get("aliases", []),
        }
    logger.info("%s: collected %d new articles", source["name"], got)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--per-source", type=int, default=20, help="new articles to collect per outlet")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds to wait between article downloads")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args.out.parent.mkdir(parents=True, exist_ok=True)

    seen = load_seen_urls(args.out)
    total = 0
    with args.out.open("a") as f:
        for source in load_sources(args.sources):
            for record in collect_source(source, args.per_source, seen, args.delay):
                f.write(json.dumps(record) + "\n")
                f.flush()
                total += 1
    logger.info("Done: %d new articles written to %s", total, args.out)


if __name__ == "__main__":
    main()
