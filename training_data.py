"""
Labeled training data for the expense category classifier.

Each entry is a (description, category_name) tuple. Category names
must match the seeded names in the database exactly — see init_db.py.

Design principles:
  - Indian context (Swiggy, Zomato, Ola, BSNL, IRCTC, etc.)
  - ~20–25 examples per category for rough class balance
  - Variation in phrasing: "Swiggy" alone, "Lunch at Swiggy",
    "Swiggy delivery", "Swiggy Instamart" — teaches the model
    that the merchant token matters across phrasings.
  - Mix of explicit merchant names and generic descriptions.

To extend: just add more tuples to TRAINING_DATA. The training
script re-fits from scratch, so adding examples costs nothing.
"""

from collections import Counter


TRAINING_DATA: list[tuple[str, str]] = [
    # =================================================================
    # 🍔 Food & Dining  (~25)
    # =================================================================
    ("Lunch at Swiggy", "Food & Dining"),
    ("Zomato dinner order", "Food & Dining"),
    ("Swiggy Instamart groceries", "Food & Dining"),
    ("Swiggy Genie food pickup", "Food & Dining"),
    ("Domino's pizza", "Food & Dining"),
    ("McDonald's burger meal", "Food & Dining"),
    ("KFC chicken bucket", "Food & Dining"),
    ("Subway sandwich", "Food & Dining"),
    ("Starbucks coffee", "Food & Dining"),
    ("Cafe Coffee Day latte", "Food & Dining"),
    ("Chai at canteen", "Food & Dining"),
    ("Hostel mess fee", "Food & Dining"),
    ("Biryani delivery from Behrouz", "Food & Dining"),
    ("Pav bhaji at street stall", "Food & Dining"),
    ("Paneer tikka takeaway", "Food & Dining"),
    ("Chinese food order", "Food & Dining"),
    ("Pizza Hut weekend dinner", "Food & Dining"),
    ("Faasos wrap order", "Food & Dining"),
    ("Lunch with friends restaurant", "Food & Dining"),
    ("Snacks from kirana store", "Food & Dining"),
    ("Restaurant bill split", "Food & Dining"),
    ("Dabba tiffin service", "Food & Dining"),
    ("Ice cream at Naturals", "Food & Dining"),
    ("Late night Maggi order", "Food & Dining"),
    ("Haldiram sweets purchase", "Food & Dining"),
    ("Tea and snacks", "Food & Dining"),
    ("Coffee with friends", "Food & Dining"),
    ("Mess fees monthly", "Food & Dining"),
    ("Cold drinks and chips", "Food & Dining"),
    ("Dinner at restaurant", "Food & Dining"),

    # =================================================================
    # 🚗 Transport  (~25)
    # =================================================================
    ("Uber to college", "Transport"),
    ("Ola cab home", "Transport"),
    ("Auto rickshaw fare", "Transport"),
    ("Petrol fill up at HP", "Transport"),
    ("Diesel for bike", "Transport"),
    ("Metro card recharge", "Transport"),
    ("Bus ticket city transport", "Transport"),
    ("Train ticket booking IRCTC", "Transport"),
    ("IRCTC tatkal booking", "Transport"),
    ("Flight booking IndiGo", "Transport"),
    ("Air India ticket", "Transport"),
    ("SpiceJet flight to Delhi", "Transport"),
    ("Rapido bike ride", "Transport"),
    ("Toll plaza FASTag payment", "Transport"),
    ("Parking fee mall", "Transport"),
    ("Bike service Hero showroom", "Transport"),
    ("Car wash", "Transport"),
    ("Tire puncture repair", "Transport"),
    ("Uber to Chennai airport", "Transport"),
    ("Ola Outstation Bangalore", "Transport"),
    ("Train to Delhi sleeper", "Transport"),
    ("Bus to home Tamil Nadu", "Transport"),
    ("Indian Oil petrol pump", "Transport"),
    ("Bharat Petroleum diesel", "Transport"),
    ("Shell premium fuel", "Transport"),
    ("Train ticket Mumbai Rajdhani", "Transport"),
    ("Bus ticket overnight Volvo", "Transport"),
    ("Flight ticket Chennai Bangalore", "Transport"),
    ("IRCTC ticket booking AC", "Transport"),
    ("Cab booking Uber to airport", "Transport"),
    ("Petrol pump local fill", "Transport"),
    ("Diesel refuel highway", "Transport"),
    ("Auto fare college to station", "Transport"),
    ("Metro ticket recharge", "Transport"),
    ("Ola booking outstation trip", "Transport"),
    ("Petrol for car", "Transport"),
    ("Taxi to station", "Transport"),
    ("Bike fuel", "Transport"),
    ("Cab ride home", "Transport"),

    # =================================================================
    # 💡 Bills & Utilities  (~25)
    # =================================================================
    ("Electricity bill payment", "Bills & Utilities"),
    ("Water bill municipality", "Bills & Utilities"),
    ("Gas connection bill", "Bills & Utilities"),
    ("BSNL broadband monthly bill", "Bills & Utilities"),
    ("Jio Fiber recharge", "Bills & Utilities"),
    ("Airtel mobile recharge", "Bills & Utilities"),
    ("Vi prepaid recharge", "Bills & Utilities"),
    ("Wifi monthly bill ACT", "Bills & Utilities"),
    ("DTH recharge", "Bills & Utilities"),
    ("Tata Sky subscription", "Bills & Utilities"),
    ("Netflix subscription monthly", "Bills & Utilities"),
    ("Spotify Premium plan", "Bills & Utilities"),
    ("Amazon Prime renewal", "Bills & Utilities"),
    ("Disney Hotstar subscription", "Bills & Utilities"),
    ("Mobile recharge Jio", "Bills & Utilities"),
    ("Postpaid Airtel bill", "Bills & Utilities"),
    ("Internet bill ACT broadband", "Bills & Utilities"),
    ("TNEB power bill", "Bills & Utilities"),
    ("LPG cylinder booking", "Bills & Utilities"),
    ("Indane gas refill", "Bills & Utilities"),
    ("Society maintenance charges", "Bills & Utilities"),
    ("Apartment maintenance fee", "Bills & Utilities"),
    ("Property tax annual", "Bills & Utilities"),
    ("YouTube Premium subscription", "Bills & Utilities"),
    ("ZEE5 annual plan", "Bills & Utilities"),

    # =================================================================
    # 🛒 Shopping  (~25)
    # =================================================================
    ("Amazon order delivery", "Shopping"),
    ("Flipkart purchase", "Shopping"),
    ("Myntra clothes order", "Shopping"),
    ("Ajio fashion sale", "Shopping"),
    ("Meesho deal", "Shopping"),
    ("Nykaa cosmetics", "Shopping"),
    ("Croma electronics", "Shopping"),
    ("Reliance Digital TV purchase", "Shopping"),
    ("Shoppers Stop shopping", "Shopping"),
    ("Lifestyle store visit", "Shopping"),
    ("Decathlon sports gear", "Shopping"),
    ("IKEA furniture order", "Shopping"),
    ("Snapdeal order", "Shopping"),
    ("Tata CLiQ purchase", "Shopping"),
    ("New shoes from Nike", "Shopping"),
    ("Adidas tracksuit", "Shopping"),
    ("H&M tshirt", "Shopping"),
    ("Zara jeans purchase", "Shopping"),
    ("Phone cover from Amazon", "Shopping"),
    ("Headphones Flipkart", "Shopping"),
    ("Stationery shopping", "Shopping"),
    ("Backpack Wildcraft", "Shopping"),
    ("Watch from Titan", "Shopping"),
    ("Sunglasses Lenskart", "Shopping"),
    ("Bedsheet from Pepperfry", "Shopping"),
    ("New shoes purchase", "Shopping"),
    ("Headphones electronics", "Shopping"),
    ("Online shopping order", "Shopping"),

    # =================================================================
    # 🎬 Entertainment  (~22)
    # =================================================================
    ("BookMyShow movie ticket", "Entertainment"),
    ("PVR cinema booking", "Entertainment"),
    ("INOX movie tickets", "Entertainment"),
    ("Concert ticket purchase", "Entertainment"),
    ("Comedy show ticket", "Entertainment"),
    ("Music festival pass", "Entertainment"),
    ("Theme park entry Wonderla", "Entertainment"),
    ("Bowling alley night", "Entertainment"),
    ("Gaming arcade tokens", "Entertainment"),
    ("Steam game purchase", "Entertainment"),
    ("PlayStation game", "Entertainment"),
    ("Xbox Game Pass subscription", "Entertainment"),
    ("Apple Music subscription", "Entertainment"),
    ("BookMyShow concert tickets", "Entertainment"),
    ("IPL match ticket", "Entertainment"),
    ("Stand up comedy show", "Entertainment"),
    ("Escape room booking", "Entertainment"),
    ("Karaoke night with friends", "Entertainment"),
    ("Pool table charges", "Entertainment"),
    ("Trampoline park ticket", "Entertainment"),
    ("VR gaming session", "Entertainment"),
    ("Movie at PVR Phoenix", "Entertainment"),

    # =================================================================
    # 🏥 Health & Medical  (~20)
    # =================================================================
    ("Doctor consultation fee", "Health & Medical"),
    ("Apollo Pharmacy medicines", "Health & Medical"),
    ("1mg online medicine order", "Health & Medical"),
    ("PharmEasy prescription delivery", "Health & Medical"),
    ("Netmeds medicine delivery", "Health & Medical"),
    ("Medical checkup full body", "Health & Medical"),
    ("Blood test at lab", "Health & Medical"),
    ("Dentist appointment cleaning", "Health & Medical"),
    ("Eye doctor visit", "Health & Medical"),
    ("Pathology lab Thyrocare", "Health & Medical"),
    ("Hospital bill admission", "Health & Medical"),
    ("ECG test cardiology", "Health & Medical"),
    ("X-ray scan diagnostic", "Health & Medical"),
    ("MRI scan cost", "Health & Medical"),
    ("Dental cleaning Apollo", "Health & Medical"),
    ("Specs from Lenskart prescription", "Health & Medical"),
    ("Contact lenses order", "Health & Medical"),
    ("Vitamins supplements HealthKart", "Health & Medical"),
    ("Cold medicine pharmacy", "Health & Medical"),
    ("Painkillers from chemist", "Health & Medical"),

    # =================================================================
    # 📚 Education  (~20)
    # =================================================================
    ("Coursera course subscription", "Education"),
    ("Udemy course Python", "Education"),
    ("Byju's premium subscription", "Education"),
    ("Unacademy plus subscription", "Education"),
    ("Vedantu live classes", "Education"),
    ("Engineering textbooks purchase", "Education"),
    ("Reference books for exam", "Education"),
    ("Lab manual college", "Education"),
    ("College semester fees", "Education"),
    ("Hostel fees VIT", "Education"),
    ("Exam fee university", "Education"),
    ("Stationery for class notes", "Education"),
    ("Online certification AWS", "Education"),
    ("Programming course bootcamp", "Education"),
    ("LinkedIn Learning subscription", "Education"),
    ("Pluralsight annual plan", "Education"),
    ("Khan Academy donation", "Education"),
    ("IELTS preparation course", "Education"),
    ("GRE coaching classes", "Education"),
    ("Workshop registration fee", "Education"),
    ("Books for school", "Education"),
    ("School supplies stationery", "Education"),
    ("Notebook and pens", "Education"),
    ("College project materials", "Education"),
    ("Library membership fee", "Education"),
    ("Engineering drawing kit", "Education"),
    ("Calculator for exam", "Education"),
    ("Photocopy of notes", "Education"),
    ("Lab coat for college", "Education"),
    ("Geometry box for class", "Education"),
    ("Coaching class fees", "Education"),
    ("Tuition fee monthly", "Education"),

    # =================================================================
    # 📦 Miscellaneous  (~20)
    # =================================================================
    ("Cash withdrawal ATM", "Miscellaneous"),
    ("Bank charges quarterly", "Miscellaneous"),
    ("ATM fee non-home bank", "Miscellaneous"),
    ("Loan EMI payment", "Miscellaneous"),
    ("Credit card bill payment", "Miscellaneous"),
    ("Insurance premium LIC", "Miscellaneous"),
    ("Mutual fund SIP investment", "Miscellaneous"),
    ("Personal loan EMI HDFC", "Miscellaneous"),
    ("Income tax payment", "Miscellaneous"),
    ("Donation to charity", "Miscellaneous"),
    ("Gift for friend birthday", "Miscellaneous"),
    ("Diwali sweets gift box", "Miscellaneous"),
    ("Holi colors and sweets", "Miscellaneous"),
    ("Salon haircut", "Miscellaneous"),
    ("Massage at spa", "Miscellaneous"),
    ("Laundry service monthly", "Miscellaneous"),
    ("Dry cleaning charges", "Miscellaneous"),
    ("Photo printing studio", "Miscellaneous"),
    ("Wedding gift envelope", "Miscellaneous"),
    ("Tip to delivery person", "Miscellaneous"),
    ("Birthday gift for friend", "Miscellaneous"),
    ("Loan EMI auto debit", "Miscellaneous"),
    ("LIC insurance renewal", "Miscellaneous"),
    ("Salon haircut and beard", "Miscellaneous"),
    ("Donation to charity NGO", "Miscellaneous"),
    ("Gift for parent", "Miscellaneous"),
    ("Wedding shagun envelope", "Miscellaneous"),
    ("Festival celebration expense", "Miscellaneous"),
    ("Personal expense random", "Miscellaneous"),
]


# =====================================================================
# Helpers used by train_classifier.py and inspection scripts
# =====================================================================

def get_training_data() -> tuple[list[str], list[str]]:
    """
    Split TRAINING_DATA into parallel lists of texts and labels.

    sklearn expects two lists: one of input texts, one of label
    strings. The list-of-tuples format is for human readability;
    this function converts to the format sklearn wants.

    Returns:
        (texts, labels) where len(texts) == len(labels).
    """
    texts = [text for text, _ in TRAINING_DATA]
    labels = [label for _, label in TRAINING_DATA]
    return texts, labels


def get_category_distribution() -> dict[str, int]:
    """
    Count examples per category. Useful for sanity-checking
    class balance before training.

    Returns:
        dict mapping category name -> count.
    """
    return dict(Counter(label for _, label in TRAINING_DATA))


def print_distribution() -> None:
    """Pretty-print the category distribution. Run this file to use."""
    distribution = get_category_distribution()
    total = sum(distribution.values())

    print("=" * 50)
    print(f"Training data distribution ({total} total examples)")
    print("=" * 50)
    for category, count in sorted(distribution.items(), key=lambda x: -x[1]):
        bar = "█" * count
        print(f"  {category:<20} {count:>3}  {bar}")
    print("=" * 50)


if __name__ == "__main__":
    print_distribution()