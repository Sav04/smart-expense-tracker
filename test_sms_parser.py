"""
Test the SMS parser against realistic Indian bank SMS samples.

Each test case = one real-world SMS format. When a new bank format
fails, add it as a failing test, then update sms_parser.py until it
passes. This is test-driven parser development.
"""

from sms_parser import parse_sms


# =====================================================================
# Test cases: (description, sms_text, expected_partial_dict)
# expected_partial_dict only specifies fields we want to verify;
# the test passes if the parser returns those values (other fields ok).
# =====================================================================

TEST_CASES = [
    # --- Should parse successfully ---
    (
        "HDFC standard debit",
        "Rs.450.00 has been debited from your a/c XX1234 on 28-Apr-26 "
        "at SWIGGY*BANGALORE. Avbl bal: Rs.12,340.00",
        {"amount": 450.0, "merchant_contains": "swiggy"},
    ),
    (
        "Credit card spend (HDFC card)",
        "INR 1500.00 spent on HDFC Bank Card xx5678 at AMAZON IN on 28-04-26. "
        "Avl Limit: INR 50,000",
        {"amount": 1500.0, "merchant_contains": "amazon"},
    ),
    (
        "ICICI debit",
        "Rs.350.00 debited from A/c XX1234 on 28-Apr-2026 to UBER INDIA "
        "for ride. Bal: Rs.5,420",
        {"amount": 350.0, "merchant_contains": "uber"},
    ),
    (
        "UPI payment - Paid",
        "Paid Rs.250 to Apollo Pharmacy from a/c xx1234 on 28-04-26. "
        "UPI Ref 412345678901",
        {"amount": 250.0, "merchant_contains": "apollo"},
    ),
    (
        "UPI payment - Sent",
        "Sent Rs.1,200.00 to merchant@paytm from HDFC A/C *1234 on 28/04/2026",
        {"amount": 1200.0, "merchant_contains": "merchant"},
    ),
    (
        "SBI UPI format",
        "Your a/c no. XXXXXXXX1234 is debited for Rs.500.00 on 28-04-2026 "
        "by UPI ref 412345/PAYTM/Domino's Pizza",
        {"amount": 500.0, "merchant_contains": "domino"},
    ),
    (
        "Comma in amount",
        "Rs.10,000.00 has been debited from a/c XX1234 on 28-Apr-26 "
        "at IRCTC.CO.IN. Avbl bal: Rs.50,000",
        {"amount": 10000.0, "merchant_contains": "irctc"},
    ),

    # --- Should return None (not transactions) ---
    (
        "Credit transaction (income, not expense)",
        "Rs.5000 credited to your a/c XX1234 on 28-Apr-26 by UPI from boss@upi",
        None,  # not a debit, should not parse
    ),
    (
        "OTP message",
        "OTP for transaction is 123456. Do not share with anyone.",
        None,
    ),
    (
        "Balance check",
        "Your a/c XX1234 has a balance of Rs.12,340 as on 28-Apr-26",
        None,
    ),
    (
        "Empty input",
        "",
        None,
    ),
]


def main() -> None:
    print("=" * 60)
    print("SMS Parser Test")
    print("=" * 60)

    passed = 0
    failed = 0

    for description, sms, expected in TEST_CASES:
        result = parse_sms(sms)

        # Case 1: expected None (not a parseable expense)
        if expected is None:
            if result is None:
                print(f"✓ {description}")
                passed += 1
            else:
                print(f"✗ {description}")
                print(f"   Expected: None")
                print(f"   Got:      {result}")
                failed += 1
            continue

        # Case 2: expected a parsed result
        if result is None:
            print(f"✗ {description}: parser returned None")
            failed += 1
            continue

        amount_ok = abs(result["amount"] - expected["amount"]) < 0.01
        merchant_ok = (
            expected["merchant_contains"].lower() in result["merchant"].lower()
        )

        if amount_ok and merchant_ok:
            print(f"✓ {description}")
            print(
                f"    → amount=₹{result['amount']:.2f}, "
                f"merchant='{result['merchant']}', "
                f"date={result['date']}"
            )
            passed += 1
        else:
            print(f"✗ {description}")
            print(
                f"   Expected: amount=₹{expected['amount']}, "
                f"merchant~'{expected['merchant_contains']}'"
            )
            print(
                f"   Got:      amount=₹{result.get('amount')}, "
                f"merchant='{result.get('merchant')}'"
            )
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed (out of {len(TEST_CASES)})")

    if failed == 0:
        print("✅ All parser tests passed.")
    else:
        print("⚠️  Some tests failed — parser needs work.")


if __name__ == "__main__":
    main()