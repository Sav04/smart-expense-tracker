"""
SMS Bank Parser for Indian banks.

Tries a sequence of regex patterns against the input SMS. Returns
extracted fields (amount, merchant, date) if any pattern matches,
or None if nothing parses cleanly.

Supported (so far):
  - "Rs.X (has been) debited ... on DATE at|to MERCHANT"  (HDFC, ICICI)
  - "Rs.X spent ... at MERCHANT on DATE"                   (credit cards)
  - "Sent/Paid Rs.X to MERCHANT (from BANK_INFO) on DATE"  (UPI apps)
  - SBI-style "debited for Rs.X on DATE by UPI ref/.../MERCHANT"

Unrecognized formats return None — caller falls back to manual entry.
"""

import re
from datetime import datetime, date
from typing import Optional


# =====================================================================
# Date parsing — Indian SMS dates come in many shapes
# =====================================================================

_DATE_FORMATS = [
    "%d-%b-%y",   # 28-Apr-26
    "%d-%b-%Y",   # 28-Apr-2026
    "%d-%m-%y",   # 28-04-26
    "%d-%m-%Y",   # 28-04-2026
    "%d/%m/%y",   # 28/04/26
    "%d/%m/%Y",   # 28/04/2026
    "%d %b %Y",   # 28 Apr 2026
    "%d %b %y",   # 28 Apr 26
    "%d%b%y",     # 28APR26
    "%d%b%Y",     # 28APR2026
]


def _parse_date(date_str: str) -> Optional[date]:
    """Try each known Indian date format; return None if none match."""
    cleaned = date_str.strip().replace("  ", " ")
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


# =====================================================================
# Amount and merchant cleanup helpers
# =====================================================================

def _parse_amount(amount_str: str) -> float:
    """'1,500.00' → 1500.0"""
    return float(amount_str.replace(",", "").strip())


def _clean_merchant(raw: str) -> str:
    """Strip trailing junk, UPI handles, collapse whitespace."""
    cleaned = raw.strip().rstrip(".;,")
    cleaned = re.sub(r"@\w+$", "", cleaned).strip()  # drop @paytm, @upi
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


# =====================================================================
# Regex building blocks
# =====================================================================
#
# Note the merchant character class now includes apostrophe (Domino's)
# and ampersand (Tom & Jerry's).
#
# Note the merchant terminator uses a LOOKAHEAD (?=...) — matches but
# doesn't consume. This way merchant matches lazily up to (but not
# including) the next sentence break.

_AMOUNT_GROUP = r"(?:rs\.?\s*|inr\s+|₹\s*)(?P<amount>[\d,]+(?:\.\d+)?)"
_DATE_GROUP = r"(?P<date>\d{1,2}[-/\s][A-Za-z\d]{2,9}[-/\s]\d{2,4})"
_MERCHANT_CHARS = r"[A-Za-z0-9*.\-_'@& ]"
_MERCHANT_END = r"(?=\.\s|;|,\s|\s+for\b|\s+UPI\b|\s+ref\b|\s*$)"


# =====================================================================
# Patterns — try each in order
# =====================================================================

_PATTERNS = [
    # Pattern 1: "Rs.X (has been|is)? debited ... on DATE (at|to) MERCHANT"
    # Covers HDFC and ICICI debit SMSes. The date comes BEFORE the merchant.
    re.compile(
        rf"{_AMOUNT_GROUP}\s+(?:has\s+been\s+|is\s+)?debited.*?"
        rf"on\s+{_DATE_GROUP}\s+(?:at|to)\s+"
        rf"(?P<merchant>{_MERCHANT_CHARS}+?){_MERCHANT_END}",
        re.IGNORECASE | re.DOTALL,
    ),

    # Pattern 2: "Rs.X spent ... at MERCHANT on DATE"
    # Credit card spend SMSes. Merchant comes BEFORE date.
    re.compile(
        rf"{_AMOUNT_GROUP}\s+spent.*?"
        rf"at\s+(?P<merchant>{_MERCHANT_CHARS}+?)"
        rf"\s+on\s+{_DATE_GROUP}",
        re.IGNORECASE | re.DOTALL,
    ),

    # Pattern 3: "Sent/Paid Rs.X to MERCHANT (from BANK_INFO)? on DATE"
    # UPI app SMSes. The "from BANK_INFO" part is optional but allowed.
    re.compile(
        rf"(?:sent|paid|transferred)\s+{_AMOUNT_GROUP}\s+"
        rf"to\s+(?P<merchant>{_MERCHANT_CHARS}+?)\s+"
        rf"(?:from\s+.*?\s+)?on\s+{_DATE_GROUP}",
        re.IGNORECASE | re.DOTALL,
    ),

    # Pattern 4: "...debited for Rs.X on DATE by UPI ref/.../MERCHANT"
    # SBI-style structured UPI debit.
    re.compile(
        rf"debited\s+for\s+{_AMOUNT_GROUP}.*?"
        rf"on\s+{_DATE_GROUP}.*?"
        rf"upi[^/]*/[^/]+/(?P<merchant>{_MERCHANT_CHARS}+?)"
        rf"(?:[.;]|$)",
        re.IGNORECASE | re.DOTALL,
    ),
]


# =====================================================================
# Public API
# =====================================================================

def parse_sms(text: str) -> Optional[dict]:
    """
    Parse an Indian bank/UPI SMS and extract transaction fields.

    Returns:
        dict with amount, merchant, date, raw_sms — or None.
    """
    if not text or not text.strip():
        return None

    text = text.strip()

    for pattern in _PATTERNS:
        match = pattern.search(text)
        if not match:
            continue

        try:
            amount = _parse_amount(match.group("amount"))
            merchant = _clean_merchant(match.group("merchant"))
            date_obj = _parse_date(match.group("date"))

            if date_obj is None:
                continue
            if amount <= 0:
                continue
            if not merchant:
                continue

            return {
                "amount": amount,
                "merchant": merchant,
                "date": date_obj,
                "raw_sms": text,
            }
        except (ValueError, KeyError):
            continue

    return None