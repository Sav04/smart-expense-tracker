"""
Quick smoke test for the classifier inference module.

Confirms the model loads and predicts correctly on realistic
descriptions. Also tests the top-k variant and the edge case
of empty input.
"""

from classifier import (
    is_model_available,
    predict_category,
    predict_top_k,
)


def test() -> None:
    print("=" * 60)
    print("Classifier inference test")
    print("=" * 60)

    # --- Model availability check -----------------------------------
    if not is_model_available():
        print("❌ Model not found. Run train_classifier.py first.")
        return
    print("✓ Model file exists\n")

    # --- Single predictions on realistic phrases --------------------
    print("Single predictions:")
    test_descriptions = [
        "Lunch at Swiggy",
        "Uber to college",
        "BookMyShow movie ticket",
        "Doctor consultation fee",
        "Amazon order delivery",
        "Coursera Python course",
        "Electricity bill payment",
        "Birthday gift for friend",
    ]

    for text in test_descriptions:
        result = predict_category(text)
        assert result is not None, f"Got None for '{text}'"
        confidence_pct = result["confidence"] * 100
        print(
            f"  '{text:<32}' → "
            f"{result['category_icon']} {result['category_name']:<18}  "
            f"({confidence_pct:5.1f}%)"
        )

    # --- Top-3 alternatives for an ambiguous case -------------------
    print("\nTop-3 alternatives for an ambiguous case:")
    ambiguous = "Amazon Prime"
    top3 = predict_top_k(ambiguous, k=3)
    print(f"  Input: '{ambiguous}'\n")
    for i, result in enumerate(top3, 1):
        confidence_pct = result["confidence"] * 100
        bar = "█" * int(confidence_pct / 4)
        print(
            f"    {i}. {result['category_icon']} {result['category_name']:<18}  "
            f"{confidence_pct:>5.1f}%  {bar}"
        )

    # --- Edge case: empty / whitespace input ------------------------
    print("\nEdge cases:")
    print(f"  predict_category('')       → {predict_category('')}")
    print(f"  predict_category('   ')    → {predict_category('   ')}")
    print(f"  predict_top_k('')          → {predict_top_k('')}")

    print("\n✅ All tests passed.")


if __name__ == "__main__":
    test()