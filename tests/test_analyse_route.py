import os
import sys
import time
import types
from unittest.mock import MagicMock

import pytest

# Keep the heavy / networked dependencies out of the unit tests.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
for _name, _attrs in {
    "supabase": {"create_client": lambda *a, **k: MagicMock(), "Client": object},
    "newspaper": {"Article": object},
}.items():
    sys.modules[_name] = types.SimpleNamespace(**_attrs)  # type: ignore[assignment]
try:
    import anthropic  # noqa: F401
except ImportError:
    sys.modules["anthropic"] = types.SimpleNamespace(Anthropic=lambda **k: MagicMock())  # type: ignore[assignment]

from fastapi.testclient import TestClient  # noqa: E402

from backend.db import supabase as db  # noqa: E402
from backend.main import app  # noqa: E402
from backend.routers import analyse as route  # noqa: E402

DELAY = 0.3


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(route, "get_cached_analysis", lambda url: None)
    monkeypatch.setattr(
        route, "scrape_article",
        lambda url: {"headline": "H", "text": "word " * 100, "source": "example.com", "authors": []},
    )

    def slow(result):
        def fn(text):
            time.sleep(DELAY)
            return result
        return fn

    monkeypatch.setattr(route, "classify_bias", slow({"label": "centre", "confidence": 0.7, "reasoning": "bias why"}))
    monkeypatch.setattr(route, "classify_tone", slow({"label": "neutral", "score": 0.2, "reasoning": "tone why"}))
    monkeypatch.setattr(route, "summarise", slow("A summary."))
    return TestClient(app)


def test_three_claude_calls_run_concurrently(client, monkeypatch):
    monkeypatch.setattr(route, "save_analysis", lambda data: None)
    start = time.perf_counter()
    r = client.post("/api/analyse", json={"url": "https://example.com/a"})
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    # Sequential would take >= 3 * DELAY. Concurrent is ~1 * DELAY.
    assert elapsed < 2 * DELAY, f"took {elapsed:.2f}s; calls look sequential"


def test_reasoning_is_saved_to_cache(client, monkeypatch):
    saved = {}
    monkeypatch.setattr(route, "save_analysis", saved.update)
    client.post("/api/analyse", json={"url": "https://example.com/a"})
    assert saved["bias_reasoning"] == "bias why"
    assert saved["tone_reasoning"] == "tone why"


def test_cache_hit_returns_saved_reasoning(client, monkeypatch):
    row = {
        "url": "u", "headline": "H", "source": "s", "bias_label": "centre", "bias_score": 0.7,
        "bias_reasoning": "bias why", "tone_label": "neutral", "tone_score": 0.2, "tone_reasoning": "tone why",
        "entity_density": 0.1, "summary": "S", "analysed_at": "2026-11-14T10:00:00+00:00",
    }
    monkeypatch.setattr(route, "get_cached_analysis", lambda url: row)
    body = client.post("/api/analyse", json={"url": "https://example.com/a"}).json()
    assert body["cached"] is True
    assert body["bias"]["reasoning"] == "bias why"
    assert body["tone"]["reasoning"] == "tone why"


def test_cache_hit_on_old_row_with_null_reasoning(client, monkeypatch):
    row = {
        "url": "u", "headline": "H", "source": "s", "bias_label": "centre", "bias_score": 0.7,
        "bias_reasoning": None, "tone_label": "neutral", "tone_score": 0.2, "tone_reasoning": None,
        "entity_density": 0.1, "summary": "S", "analysed_at": "2026-11-14T10:00:00+00:00",
    }
    monkeypatch.setattr(route, "get_cached_analysis", lambda url: row)
    r = client.post("/api/analyse", json={"url": "https://example.com/a"})
    assert r.status_code == 200
    assert r.json()["bias"]["reasoning"] == ""


def test_pipeline_failure_returns_503(client, monkeypatch):
    def boom(text):
        raise RuntimeError("API down")
    monkeypatch.setattr(route, "classify_tone", boom)
    assert client.post("/api/analyse", json={"url": "https://example.com/a"}).status_code == 503


def test_save_retries_without_reasoning_when_columns_missing(monkeypatch):
    calls = []
    table = MagicMock()

    def insert(row):
        calls.append(dict(row))
        if "bias_reasoning" in row:
            raise RuntimeError("column bias_reasoning does not exist")
        return MagicMock()

    table.insert.side_effect = insert
    monkeypatch.setattr(db, "supabase", MagicMock(table=lambda name: table))
    db.save_analysis({"url": "u", "bias_reasoning": "x", "tone_reasoning": "y", "summary": "s"})
    assert len(calls) == 2
    assert calls[1] == {"url": "u", "summary": "s"}  # cache write still succeeded, minus reasoning


def test_save_makes_single_insert_when_columns_exist(monkeypatch):
    table = MagicMock()
    monkeypatch.setattr(db, "supabase", MagicMock(table=lambda name: table))
    db.save_analysis({"url": "u", "bias_reasoning": "x", "tone_reasoning": "y"})
    assert table.insert.call_count == 1
