"""Shared label scheme for the evaluation pipeline.

The five classes are the same ones the production classifier
(backend/services/classifier.py) is prompted to return, ordered left to right,
so the position of a label doubles as an ordinal score.
"""

LABELS = ["left-wing", "centre-left", "centre", "centre-right", "right-wing"]
LABEL_TO_ID = {label: i for i, label in enumerate(LABELS)}
CENTRE_ID = LABEL_TO_ID["centre"]


def label_to_id(label: str) -> int:
    """Map a label string to its ordinal id. Raises KeyError on unknown labels."""
    return LABEL_TO_ID[label.strip().lower()]
