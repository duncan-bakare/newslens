"""Metrics for the five-class, ordered bias labels.

Pure functions over integer label ids (see ml/labels.py) so they can be unit
tested without any API calls.
"""

import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

from ml.labels import CENTRE_ID, LABELS

N_CLASSES = len(LABELS)
_ALL = list(range(N_CLASSES))


def expected_calibration_error(correct: np.ndarray, confidence: np.ndarray, n_bins: int = 5) -> tuple[float, list[dict]]:
    """Expected calibration error plus the per-bin reliability table.

    A well-calibrated classifier is right ~70% of the time when it says 0.7.
    The production prompt tells Claude to "be bold" with confidence, so this
    checks whether the reported confidence means anything.
    """
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins, ece = [], 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        in_bin = (confidence >= lo) & ((confidence < hi) if hi < 1.0 else (confidence <= hi))
        if not in_bin.any():
            continue
        acc = float(correct[in_bin].mean())
        conf = float(confidence[in_bin].mean())
        ece += in_bin.mean() * abs(acc - conf)
        bins.append({"range": f"{lo:.1f}-{hi:.1f}", "n": int(in_bin.sum()), "mean_confidence": round(conf, 3), "accuracy": round(acc, 3)})
    return float(ece), bins


def classification_report(y_true, y_pred, confidence=None) -> dict:
    """All headline metrics for one set of predictions."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if len(y_true) == 0 or len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must be non-empty and the same length")

    correct = y_true == y_pred
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=_ALL, zero_division=0
    )

    report = {
        "n": int(len(y_true)),
        "accuracy": round(float(correct.mean()), 4),
        # An answer one step along the spectrum (e.g. centre-left vs left-wing)
        # is a much smaller mistake than left vs right, so report both.
        "within_one_accuracy": round(float((np.abs(y_true - y_pred) <= 1).mean()), 4),
        "mean_absolute_error": round(float(np.abs(y_true - y_pred).mean()), 4),
        "macro_f1": round(float(f1.mean()), 4),
        # Does the model retreat to "centre" more often than the data warrants?
        "predicted_centre_rate": round(float((y_pred == CENTRE_ID).mean()), 4),
        "true_centre_rate": round(float((y_true == CENTRE_ID).mean()), 4),
        "per_class": {
            LABELS[i]: {
                "precision": round(float(precision[i]), 4),
                "recall": round(float(recall[i]), 4),
                "f1": round(float(f1[i]), 4),
                "support": int(support[i]),
            }
            for i in _ALL
        },
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=_ALL).tolist(),
    }

    if confidence is not None:
        ece, bins = expected_calibration_error(correct, np.asarray(confidence, dtype=float))
        report["expected_calibration_error"] = round(ece, 4)
        report["reliability"] = bins

    return report


def per_source_accuracy(sources, y_true, y_pred) -> dict:
    """Accuracy and mean predicted position for each outlet."""
    sources = np.asarray(sources)
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    out = {}
    for s in sorted(set(sources)):
        m = sources == s
        out[s] = {
            "n": int(m.sum()),
            "true_label": LABELS[int(y_true[m][0])],
            "accuracy": round(float((y_true[m] == y_pred[m]).mean()), 3),
            "mean_predicted_position": round(float(y_pred[m].mean()), 2),
        }
    return out
