"""Keras baseline: can a small neural net trained on labelled articles match Claude?

TF-IDF features -> dense ANN (Keras) -> 5-way softmax over the bias labels.

Split: leave-one-source-out per class. For each label with two or more outlets,
one whole outlet is held out for testing. Splitting by article instead would let
the network memorise each publisher's house style and score far too well, which
says nothing about bias. Outlet names are also scrubbed from the text.

Run from the repo root after collect_dataset and evaluate:
    python -m ml.baseline_keras --claude-preds ml/results/claude_predictions.jsonl

With --claude-preds, Claude is scored on exactly the same held-out articles so
the comparison is fair.
"""

import argparse
import json
import random
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

from ml.evaluate import DEFAULT_DATA, load_jsonl, plot_confusion_matrix
from ml.labels import LABELS, label_to_id
from ml.metrics import classification_report

DEFAULT_OUT = Path(__file__).parent / "results"
SEED = 42


def scrub_source_names(text: str, source: str, aliases=()) -> str:
    """Remove the outlet's own name so the model can't just spot 'Fox News'."""
    stem = source.split(".")[0]
    names = {stem, *aliases}
    if stem.startswith("the"):
        names.add(stem[3:])
    pattern = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return re.sub(pattern, " ", text, flags=re.IGNORECASE)


def split_by_source(records: list[dict], seed: int = SEED) -> tuple[list[dict], list[dict]]:
    """Hold out one outlet per label (where a label has 2+ outlets)."""
    rng = random.Random(seed)
    sources_by_label: dict[str, list[str]] = {}
    for r in records:
        sources_by_label.setdefault(r["true_label"], [])
        if r["source"] not in sources_by_label[r["true_label"]]:
            sources_by_label[r["true_label"]].append(r["source"])

    held_out = set()
    for label, sources in sources_by_label.items():
        if len(sources) >= 2:
            held_out.add(rng.choice(sorted(sources)))

    train = [r for r in records if r["source"] not in held_out]
    test = [r for r in records if r["source"] in held_out]
    return train, test


def build_model(input_dim: int, n_classes: int):
    import keras
    from keras import layers

    model = keras.Sequential(
        [
            layers.Input(shape=(input_dim,)),
            layers.Dense(128, activation="relu"),
            layers.Dropout(0.5),
            layers.Dense(64, activation="relu"),
            layers.Dropout(0.3),
            layers.Dense(n_classes, activation="softmax"),
        ]
    )
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def plot_history(history, path: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.plot(history.history["loss"], label="train")
    ax1.plot(history.history["val_loss"], label="validation")
    ax1.set_title("Loss")
    ax1.set_xlabel("Epoch")
    ax1.legend()
    ax2.plot(history.history["accuracy"], label="train")
    ax2.plot(history.history["val_accuracy"], label="validation")
    ax2.set_title("Accuracy")
    ax2.set_xlabel("Epoch")
    ax2.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--claude-preds", type=Path, default=None, help="claude_predictions.jsonl from ml.evaluate")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--max-features", type=int, default=5000)
    args = parser.parse_args()

    import keras

    keras.utils.set_random_seed(SEED)

    records = load_jsonl(args.data)
    train, test = split_by_source(records)
    if not train or not test:
        raise SystemExit("Need at least two outlets for some label to hold one out. Collect more sources.")
    print(f"Train: {len(train)} articles from {len({r['source'] for r in train})} outlets")
    print(f"Test:  {len(test)} articles from {len({r['source'] for r in test})} held-out outlets: {sorted({r['source'] for r in test})}")

    def prep(rs):
        return [scrub_source_names(r["text"], r["source"], r.get("aliases", ())) for r in rs]

    # Fit the vectoriser on training text only, so no test vocabulary leaks in.
    vec = TfidfVectorizer(max_features=args.max_features, ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
    X_train = vec.fit_transform(prep(train)).toarray().astype("float32")
    X_test = vec.transform(prep(test)).toarray().astype("float32")
    y_train = np.array([label_to_id(r["true_label"]) for r in train])
    y_test = np.array([label_to_id(r["true_label"]) for r in test])

    classes = np.unique(y_train)
    weights = dict(zip(classes, compute_class_weight("balanced", classes=classes, y=y_train)))

    # Explicit stratified validation split for early stopping. Keras's validation_split
    # takes the LAST 20% of rows without shuffling, and the data is ordered by outlet,
    # so it would validate on a single publisher.
    X_fit, X_val, y_fit, y_val = train_test_split(X_train, y_train, test_size=0.2, stratify=y_train, random_state=SEED)

    model = build_model(X_train.shape[1], len(LABELS))
    history = model.fit(
        X_fit,
        y_fit,
        validation_data=(X_val, y_val),
        epochs=args.epochs,
        batch_size=16,
        class_weight=weights,
        callbacks=[keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)],
        verbose=2,
    )

    probs = model.predict(X_test, verbose=0)
    keras_report = classification_report(y_test, probs.argmax(axis=1), probs.max(axis=1))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    plot_history(history, args.out_dir / "keras_training_curves.png")
    plot_confusion_matrix(keras_report["confusion_matrix"], args.out_dir / "keras_confusion_matrix.png", "Keras TF-IDF ANN (held-out outlets)")
    model.save(args.out_dir / "keras_baseline.keras")

    comparison = {
        "test_outlets": sorted({r["source"] for r in test}),
        "n_test": len(test),
        "keras": keras_report,
    }

    if args.claude_preds:
        preds = {p["url"]: p for p in load_jsonl(args.claude_preds)}
        scored = [r for r in test if r["url"] in preds]
        if scored:
            claude_report = classification_report(
                [label_to_id(r["true_label"]) for r in scored],
                [label_to_id(preds[r["url"]]["label"]) for r in scored],
                [preds[r["url"]]["confidence"] for r in scored],
            )
            comparison["claude_same_articles"] = claude_report
        else:
            print("No overlap between Claude predictions and the held-out set; run ml.evaluate on the full dataset.")

    (args.out_dir / "comparison.json").write_text(json.dumps(comparison, indent=2))

    print("\n=== Held-out outlets ===")
    rows = [("Keras ANN", keras_report)]
    if "claude_same_articles" in comparison:
        rows.append(("Claude Haiku", comparison["claude_same_articles"]))
    print(f"{'model':14s} {'n':>4s} {'acc':>7s} {'within-1':>9s} {'macro-F1':>9s} {'MAE':>6s}")
    for name, r in rows:
        print(f"{name:14s} {r['n']:4d} {r['accuracy']:7.1%} {r['within_one_accuracy']:9.1%} {r['macro_f1']:9.3f} {r['mean_absolute_error']:6.2f}")
    print(f"\nFull results in {args.out_dir}/")


if __name__ == "__main__":
    main()
