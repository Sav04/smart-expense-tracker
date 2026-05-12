"""
Train the expense category classifier.

Run this script once. It:
  1. Loads labeled training data from training_data.py
  2. Splits into train/test (80/20, stratified)
  3. Builds a TF-IDF + Logistic Regression pipeline
  4. Fits on the training set
  5. Evaluates on the test set (accuracy + classification report)
  6. Saves the trained pipeline to models/classifier.joblib

Re-run any time you update training_data.py — the script re-fits
from scratch in a few seconds.

Usage:
    python train_classifier.py
"""
from db_corrections import get_all_corrections, get_correction_count
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from training_data import get_training_data, get_category_distribution


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "classifier.joblib"

RANDOM_STATE = 42      # Fixed seed → re-runs produce identical results
TEST_FRACTION = 0.2    # 20% held out for honest evaluation


# ---------------------------------------------------------------------
# Pipeline definition
# ---------------------------------------------------------------------

def build_pipeline() -> Pipeline:
    """
    Build the TF-IDF + Logistic Regression pipeline.

    Pipeline = vectorizer + classifier wrapped in a single object.
    Benefits:
      - Inference is one call: pipeline.predict([text])
      - We save/load one file, not two
      - No risk of using a vectorizer on text that doesn't match
        what the classifier was trained on (a classic bug)

    Tuning notes for this small dataset (~200 examples):
      - ngram_range=(1, 1): bigrams overfit at this scale
      - min_df=1: keep all words including rare merchant names
        (proper nouns are high-signal here)
      - no stop_words: descriptions are too short to drop words safely
      - default C=1.0: sklearn defaults work well; aggressive tuning
        produced no measurable improvement on this dataset
    """
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 1),
            min_df=1,
            sublinear_tf=True,
            lowercase=True,
        )),
        ("classifier", LogisticRegression(
            max_iter=1000,
            C=1.0,
            random_state=RANDOM_STATE,
        )),
    ])

def load_all_training_data() -> tuple[list[str], list[str]]:
    """
    Combine seed training data (training_data.py) with user corrections
    from the database. This is what the retraining loop is built on:
    every override the user makes becomes a new training example next
    time the model is fit.
    """
    texts, labels = get_training_data()
    n_seed = len(texts)

    # Pull user corrections from DB and append
    try:
        corrections = get_all_corrections()
        for c in corrections:
            texts.append(c["description"])
            labels.append(c["category_name"])
    except Exception:
        # If corrections table doesn't exist yet, skip silently
        corrections = []

    return texts, labels

# ---------------------------------------------------------------------
# Training and evaluation
# ---------------------------------------------------------------------

def train(verbose: bool = True) -> dict:
    """
    Fit the classifier on combined seed data + user corrections.

    Args:
        verbose: If True, print progress and metrics.

    Returns:
        dict with keys: train_accuracy, test_accuracy, total_examples,
        n_corrections.
    """
    if verbose:
        print("=" * 60)
        print("Training expense category classifier")
        print("=" * 60)

    # --- Step 1: Load combined data --------------------------------
    texts, labels = load_all_training_data()
    n_corrections = get_correction_count() if _safe_count() else 0
    n_seed = len(texts) - n_corrections

    if verbose:
        print(f"\nLoaded {len(texts)} labeled examples "
              f"({n_seed} seed + {n_corrections} corrections) "
              f"across {len(set(labels))} categories")

    # --- Step 2: Train/test split ----------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=TEST_FRACTION,
        stratify=labels,
        random_state=RANDOM_STATE,
    )
    if verbose:
        print(f"Train: {len(X_train)}  ·  Test: {len(X_test)}")

    # --- Step 3: Fit ----------------------------------------------
    pipeline = build_pipeline()
    if verbose:
        print("\nTraining...")
    pipeline.fit(X_train, y_train)

    # --- Step 4: Evaluate -----------------------------------------
    train_predictions = pipeline.predict(X_train)
    test_predictions = pipeline.predict(X_test)
    train_accuracy = accuracy_score(y_train, train_predictions)
    test_accuracy = accuracy_score(y_test, test_predictions)

    if verbose:
        print(f"\nTrain accuracy: {train_accuracy:.1%}")
        print(f"Test accuracy:  {test_accuracy:.1%}")
        print(classification_report(y_test, test_predictions, zero_division=0))

    # --- Step 5: Save ---------------------------------------------
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    if verbose:
        print(f"\n✅ Model saved to {MODEL_PATH}")

    return {
        "train_accuracy": train_accuracy,
        "test_accuracy": test_accuracy,
        "total_examples": len(texts),
        "n_seed": n_seed,
        "n_corrections": n_corrections,
    }


def _safe_count() -> bool:
    """Helper: check if corrections table is queryable."""
    try:
        get_correction_count()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    train()