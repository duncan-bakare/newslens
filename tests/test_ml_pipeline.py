import json

import numpy as np
import pytest

from ml.baseline_keras import scrub_source_names, split_by_source
from ml.evaluate import evaluate, predict_all
from ml.labels import LABELS, label_to_id
from ml.metrics import classification_report, expected_calibration_error, per_source_accuracy


def test_perfect_predictions():
    y = [0, 1, 2, 3, 4]
    r = classification_report(y, y)
    assert r["accuracy"] == 1.0
    assert r["within_one_accuracy"] == 1.0
    assert r["mean_absolute_error"] == 0.0
    assert r["macro_f1"] == 1.0
    assert np.trace(np.array(r["confusion_matrix"])) == 5


def test_within_one_is_more_forgiving_than_exact():
    # left-wing predicted as centre-left (1 step off) and as right-wing (4 steps off)
    r = classification_report([0, 0], [1, 4])
    assert r["accuracy"] == 0.0
    assert r["within_one_accuracy"] == 0.5
    assert r["mean_absolute_error"] == 2.5


def test_centre_rate_detects_fence_sitting():
    r = classification_report([0, 4, 0, 4], [2, 2, 2, 2])
    assert r["predicted_centre_rate"] == 1.0
    assert r["true_centre_rate"] == 0.0


def test_report_handles_missing_classes():
    # Only two of five classes appear anywhere; must not crash or reshape the matrix.
    r = classification_report([0, 0, 4], [0, 4, 4])
    assert np.array(r["confusion_matrix"]).shape == (5, 5)
    assert r["per_class"]["centre"]["support"] == 0


def test_report_rejects_bad_input():
    with pytest.raises(ValueError):
        classification_report([], [])
    with pytest.raises(ValueError):
        classification_report([0, 1], [0])


def test_ece_zero_when_confidence_matches_accuracy():
    correct = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0], dtype=bool)  # 40% accurate
    conf = np.full(10, 0.4)
    ece, bins = expected_calibration_error(correct, conf)
    assert ece == pytest.approx(0.0, abs=1e-9)
    assert bins[0]["n"] == 10


def test_ece_large_for_overconfident_wrong_model():
    correct = np.zeros(10, dtype=bool)
    conf = np.full(10, 0.9)
    ece, _ = expected_calibration_error(correct, conf)
    assert ece == pytest.approx(0.9)


def test_confidence_of_exactly_one_is_binned():
    ece, bins = expected_calibration_error(np.array([True]), np.array([1.0]))
    assert sum(b["n"] for b in bins) == 1


def test_per_source_accuracy():
    out = per_source_accuracy(["a", "a", "b"], [0, 0, 4], [0, 1, 4])
    assert out["a"]["accuracy"] == 0.5
    assert out["a"]["true_label"] == "left-wing"
    assert out["b"]["accuracy"] == 1.0


def _records():
    recs = []
    for label, sources in {
        "left-wing": ["huffpost.com", "vox.com"],
        "centre": ["bbc.co.uk"],
        "right-wing": ["breitbart.com", "washingtonexaminer.com"],
    }.items():
        for s in sources:
            for i in range(3):
                recs.append({"url": f"https://{s}/{i}", "source": s, "text": f"text {s} {i}", "true_label": label})
    return recs


def test_split_holds_out_whole_outlets_and_never_leaks():
    train, test = split_by_source(_records())
    train_sources = {r["source"] for r in train}
    test_sources = {r["source"] for r in test}
    assert train_sources.isdisjoint(test_sources)
    # a label with one outlet (centre) can't be held out, or it would vanish from training
    assert "bbc.co.uk" in train_sources
    # every label with 2+ outlets contributes exactly one test outlet
    assert len(test_sources) == 2


def test_split_is_deterministic():
    a = split_by_source(_records())[1]
    b = split_by_source(_records())[1]
    assert [r["url"] for r in a] == [r["url"] for r in b]


def test_scrub_removes_outlet_name_case_insensitively():
    out = scrub_source_names("The Guardian reports; GUARDIAN view", "theguardian.com", ["the guardian", "guardian"])
    assert "guardian" not in out.lower()


def test_scrub_handles_spaced_outlet_names_via_aliases():
    # "foxnews" (the domain stem) alone would miss "Fox News" with a space in it
    assert "fox" not in scrub_source_names("Fox News said", "foxnews.com", ["fox news"]).lower()
    assert "fox" in scrub_source_names("Fox News said", "foxnews.com").lower()  # documents why aliases exist


def test_predict_all_uses_cache_and_survives_failures(tmp_path):
    recs = [{"url": f"u{i}", "source": "s", "text": f"t{i}", "true_label": "centre"} for i in range(4)]
    calls = []

    def fake(text):
        calls.append(text)
        if text == "t2":
            raise RuntimeError("API down")
        return {"label": "centre", "confidence": 0.8, "reasoning": "x"}

    cache = tmp_path / "preds.jsonl"
    first = predict_all(recs, fake, cache, workers=2)
    assert len(first) == 3  # t2 failed but the rest were kept
    assert len(calls) == 4

    calls.clear()
    second = predict_all(recs, fake, cache, workers=2)
    assert calls == ["t2"]  # only the failed one is retried
    assert len(second) == 3

    cached_lines = [json.loads(line) for line in cache.read_text().splitlines()]
    assert len(cached_lines) == 3


def test_evaluate_end_to_end():
    recs = [
        {"url": "a", "source": "x", "text": "", "true_label": "left-wing"},
        {"url": "b", "source": "y", "text": "", "true_label": "right-wing"},
    ]
    preds = [
        {"url": "a", "label": "left-wing", "confidence": 0.9},
        {"url": "b", "label": "centre", "confidence": 0.7},
    ]
    r = evaluate(recs, preds)
    assert r["accuracy"] == 0.5
    assert r["per_source"]["y"]["accuracy"] == 0.0
    assert set(LABELS) == set(r["per_class"])


def test_label_to_id_is_case_and_whitespace_tolerant():
    assert label_to_id("  Centre-Left ") == 1
    with pytest.raises(KeyError):
        label_to_id("far-left")
