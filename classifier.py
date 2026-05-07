"""
Inference module for the expense category classifier.

Loads the trained model lazily on first call and caches it for
the rest of the Python process. Exposes prediction functions
used by the Streamlit app and any other consumer.

Usage:
    from classifier import predict_category

    result = predict_category("Lunch at Swiggy")
    # → {"category_id": 1, "category_name": "Food & Dining",
    #    "category_icon": "🍔", "category_color": "#FF6B6B",
    #    "confidence": 0.94}
"""

from pathlib import Path
from typing import Optional

import joblib
from sklearn.pipeline import Pipeline

from db_categories import get_category_by_name


MODEL_PATH = Path(__file__).parent / "models" / "classifier.joblib"


# Module-level cache. Lives for the lifetime of the Python process.
# First call to a predict function loads it; subsequent calls reuse it.
_pipeline: Optional[Pipeline] = None


# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------

def _load_model() -> Pipeline:
    """
    Load the trained pipeline from disk. Cached at module level.

    Raises:
        FileNotFoundError: If the model file doesn't exist. The
        message tells the caller exactly how to fix it.
    """
    global _pipeline
    if _pipeline is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file not found at {MODEL_PATH}.\n"
                f"Run `python train_classifier.py` to train the model first."
            )
        _pipeline = joblib.load(MODEL_PATH)
    return _pipeline


def _build_result(class_name: str, confidence: float) -> Optional[dict]:
    """Convert a (class_name, confidence) into the rich result dict."""
    category = get_category_by_name(class_name)
    if category is None:
        # The model predicted a class name not in the database.
        # Shouldn't happen — model trained on seeded category names.
        return None

    return {
        "category_id": category["id"],
        "category_name": category["name"],
        "category_icon": category["icon"],
        "category_color": category["color"],
        "confidence": confidence,
    }


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def is_model_available() -> bool:
    """Check if the trained model file exists. Useful for UI gating."""
    return MODEL_PATH.exists()


def predict_category(text: str) -> Optional[dict]:
    """
    Predict the most likely category for an expense description.

    Args:
        text: Description of the expense (e.g., "Lunch at Swiggy").

    Returns:
        dict with keys:
          - category_id    (int)
          - category_name  (str)
          - category_icon  (str)
          - category_color (str, hex)
          - confidence     (float, 0.0–1.0)
        Or None if text is empty/whitespace-only.
    """
    if not text or not text.strip():
        return None

    pipeline = _load_model()

    # predict_proba returns shape (n_samples, n_classes).
    # We pass one text, so [0] gives us the per-class probabilities.
    probabilities = pipeline.predict_proba([text])[0]

    # argmax → index of the highest-probability class
    best_idx = probabilities.argmax()
    best_class_name = pipeline.classes_[best_idx]
    confidence = float(probabilities[best_idx])

    return _build_result(best_class_name, confidence)


def predict_top_k(text: str, k: int = 3) -> list[dict]:
    """
    Return the top K predicted categories sorted by confidence DESC.

    Useful UX pattern: when top-1 confidence is low, show the user
    the top 2–3 options as "did you mean..." chips.

    Args:
        text: Expense description.
        k: How many top predictions to return.

    Returns:
        List of result dicts, longest first. Empty list if text empty.
    """
    if not text or not text.strip():
        return []

    pipeline = _load_model()
    probabilities = pipeline.predict_proba([text])[0]

    # argsort returns indices that would sort the array (ascending).
    # [::-1] reverses → descending. [:k] takes the top k.
    top_indices = probabilities.argsort()[::-1][:k]

    results = []
    for idx in top_indices:
        class_name = pipeline.classes_[idx]
        confidence = float(probabilities[idx])
        result = _build_result(class_name, confidence)
        if result is not None:
            results.append(result)

    return results