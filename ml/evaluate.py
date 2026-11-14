"""Evaluate the production bias classifier against the collected dataset.

Run from the repo root (needs ANTHROPIC_API_KEY, e.g. in .env):
    python -m ml.evaluate --limit 50

Predictions are cached in <out-dir>/claude_predictions.jsonl, so re-running only
pays for articles not yet classified. This uses the same truncation and prompt
as the live site (backend.services.classifier.classify_bias), so the numbers
describe what users actually get.

Outputs in <out-dir>: metrics.json, confusion_matrix.png, reliability.png
"""

import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ml.labels import LABELS, label_to_id
from ml.metrics import classification_report, per_source_accuracy

logger = logging.getLogger("evaluate")

DEFAULT_DATA = Path(__file__).parent / "data" / "articles.jsonl"
DEFAULT_OUT = Path(__file__).parent / "results"


def load_jsonl(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def predict_all(records: list[dict], predict_fn: Callable[[str], dict], cache_path: Path, workers: int = 4) -> list[dict]:
    """Run predict_fn over every record, reusing cached predictions by URL.

    predict_fn takes article text and returns {"label", "confidence", ...}, the
    same shape as classify_bias. It is injected so tests can use a fake.
    """
    cache = {r["url"]: r for r in load_jsonl(cache_path)} if cache_path.exists() else {}
    todo = [r for r in records if r["url"] not in cache]
    logger.info("%d cached, %d to classify", len(records) - len(todo), len(todo))

    def work(rec):
        try:
            pred = predict_fn(rec["text"])
            return {"url": rec["url"], "label": pred["label"], "confidence": pred["confidence"], "reasoning": pred.get("reasoning", "")}
        except Exception as e:  # one bad API call shouldn't lose the whole run
            logger.warning("failed on %s: %s", rec["url"], e)
            return None

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("a") as f, ThreadPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(work, todo):
            if result:
                cache[result["url"]] = result
                f.write(json.dumps(result) + "\n")
                f.flush()

    return [cache[r["url"]] for r in records if r["url"] in cache]


def plot_confusion_matrix(cm: list[list[int]], path: Path, title: str) -> None:
    cm = np.asarray(cm)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(LABELS)), LABELS, rotation=30, ha="right")
    ax.set_yticks(range(len(LABELS)), LABELS)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Source-level label")
    ax.set_title(title)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, cm[i, j], ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_reliability(bins: list[dict], path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], "k--", label="perfectly calibrated")
    ax.plot([b["mean_confidence"] for b in bins], [b["accuracy"] for b in bins], "o-", label="classifier")
    ax.set_xlabel("Mean stated confidence")
    ax.set_ylabel("Actual accuracy")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def evaluate(records: list[dict], predictions: list[dict]) -> dict:
    by_url = {p["url"]: p for p in predictions}
    rows = [(r, by_url[r["url"]]) for r in records if r["url"] in by_url]
    y_true = [label_to_id(r["true_label"]) for r, _ in rows]
    y_pred = [label_to_id(p["label"]) for _, p in rows]
    conf = [p["confidence"] for _, p in rows]
    report = classification_report(y_true, y_pred, conf)
    report["per_source"] = per_source_accuracy([r["source"] for r, _ in rows], y_true, y_pred)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--limit", type=int, default=None, help="only classify the first N articles (cheap test run)")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    from dotenv import load_dotenv

    load_dotenv()
    from backend.services.classifier import classify_bias
    from backend.services.scraper import truncate_for_api

    records = load_jsonl(args.data)
    if args.limit:
        records = records[: args.limit]

    def predict(text: str) -> dict:
        return classify_bias(truncate_for_api(text))

    preds = predict_all(records, predict, args.out_dir / "claude_predictions.jsonl", args.workers)
    report = evaluate(records, preds)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "metrics.json").write_text(json.dumps(report, indent=2))
    plot_confusion_matrix(report["confusion_matrix"], args.out_dir / "confusion_matrix.png", "Claude Haiku: bias classification")
    if report.get("reliability"):
        plot_reliability(report["reliability"], args.out_dir / "reliability.png", "Confidence calibration")

    print(f"\nArticles evaluated: {report['n']}")
    print(f"Accuracy:            {report['accuracy']:.1%}")
    print(f"Within one class:    {report['within_one_accuracy']:.1%}")
    print(f"Macro F1:            {report['macro_f1']:.3f}")
    print(f"Calibration error:   {report['expected_calibration_error']:.3f}")
    print(f"Predicts 'centre':   {report['predicted_centre_rate']:.1%} (true share {report['true_centre_rate']:.1%})")
    print("\nPer source:")
    for s, v in report["per_source"].items():
        print(f"  {s:28s} n={v['n']:<3d} acc={v['accuracy']:.2f}  label={v['true_label']:<13s} mean position={v['mean_predicted_position']}")
    print(f"\nFull results in {args.out_dir}/")


if __name__ == "__main__":
    main()
