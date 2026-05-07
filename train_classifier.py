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


# ---------------------------------------------------------------------
# Training and evaluation
# ---------------------------------------------------------------------

def train() -> None:
    print("=" * 60)
    print("Training expense category classifier")
    print("=" * 60)

    # --- Step 1: Load data ----------------------------------------
    texts, labels = get_training_data()
    print(f"\nLoaded {len(texts)} labeled examples "
          f"across {len(set(labels))} categories")

    distribution = get_category_distribution()
    for cat, count in sorted(distribution.items(), key=lambda x: -x[1]):
        print(f"  {cat:<20} {count}")

    # --- Step 2: Train/test split (stratified) ---------------------
    # stratify=labels guarantees both splits have the same class
    # proportions. Without it, you could get a test set missing
    # entire categories — meaningless evaluation.
    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=TEST_FRACTION,
        stratify=labels,
        random_state=RANDOM_STATE,
    )
    print(f"\nTrain: {len(X_train)} examples")
    print(f"Test:  {len(X_test)} examples")

    # --- Step 3: Build pipeline and fit ----------------------------
    pipeline = build_pipeline()
    print("\nTraining...")
    pipeline.fit(X_train, y_train)
    print("Done.")

    # --- Step 4: Evaluate ------------------------------------------
    train_predictions = pipeline.predict(X_train)
    test_predictions = pipeline.predict(X_test)

    train_accuracy = accuracy_score(y_train, train_predictions)
    test_accuracy = accuracy_score(y_test, test_predictions)

    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Train accuracy: {train_accuracy:.1%}")
    print(f"Test accuracy:  {test_accuracy:.1%}")

    gap = train_accuracy - test_accuracy
    if gap > 0.20:
        print(f"⚠  Train/test gap ({gap:.1%}) — overfitting suspected.")
    else:
        print(f"✓ Train/test gap ({gap:.1%}) is healthy.")

    # Per-category metrics
    print("\nPer-category breakdown on test set:")
    print(classification_report(y_test, test_predictions, zero_division=0))

    # Confusion matrix
    print("Confusion matrix (rows = true label, cols = predicted):")
    labels_sorted = sorted(set(labels))
    short_names = [name[:11] for name in labels_sorted]
    cm = confusion_matrix(y_test, test_predictions, labels=labels_sorted)

    print(f"\n{'':<13}", end="")
    for name in short_names:
        print(f"{name:>13}", end="")
    print()
    for i, name in enumerate(short_names):
        print(f"{name:<13}", end="")
        for val in cm[i]:
            print(f"{val:>13}", end="")
        print()

    # --- Step 5: Save the trained pipeline -------------------------
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    file_size_kb = MODEL_PATH.stat().st_size / 1024
    print(f"\n✅ Model saved to {MODEL_PATH} ({file_size_kb:.1f} KB)")

    # --- Step 6: Smoke test on novel descriptions ------------------
    print("\nSmoke test on novel descriptions:")
    novel_texts = [
        "BookMyShow movie tickets",
        "Swiggy lunch order",
        "Petrol fill at HP",
        "Doctor visit checkup",
        "Amazon shopping order",
        "Coursera AI course",
    ]
    predictions = pipeline.predict(novel_texts)
    probabilities = pipeline.predict_proba(novel_texts)

    for text, pred, probs in zip(novel_texts, predictions, probabilities):
        confidence = probs.max()
        print(f"  '{text:<32}' → {pred:<20} ({confidence:.0%} sure)")


if __name__ == "__main__":
    train()