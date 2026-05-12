# 💰 Smart Expense Tracker

An ML-powered personal expense tracker for Indian users, featuring auto-categorization, SMS parsing, interactive analytics, and an active-learning correction loop.

**🔗 Live Demo:** [your-app-url-here.streamlit.app](https://your-app-url-here.streamlit.app) *(update after deployment)*

---

## ✨ Features

- **🤖 ML-based auto-categorization** — TF-IDF + Logistic Regression classifies expenses across 8 categories with live confidence scores
- **📱 SMS auto-import** — Multi-pattern regex parser extracts amount, merchant, and date from Indian bank/UPI SMSes (HDFC, ICICI, SBI, etc.)
- **📊 Interactive analytics** — Plotly dashboard with category breakdown, top merchants, daily trend, and KPI cards
- **💰 Budget tracking** — Per-category monthly limits with color-coded progress bars and sidebar alerts when exceeded
- **🔄 Active learning** — User category overrides are captured and merged into training data; one-click retrain hot-swaps the model
- **🗑️ Full CRUD** — Add, delete, and filter expenses across multiple time periods
- **🇮🇳 India-first** — INR throughout, Indian bank SMS formats, merchant names matching Indian spending patterns

---

## 🧠 ML Methodology

The classifier is a `TF-IDF Vectorizer + Logistic Regression` pipeline trained on ~225 hand-labeled examples covering Indian merchant vocabulary (Swiggy, Zomato, IRCTC, BookMyShow, Apollo Pharmacy, etc.).

**Key design choices:**

- `sublinear_tf=True` and `min_df=1` — diminishing returns on repeated terms; allow rare but distinctive vocabulary
- `C=1.0` regularization — balances overfitting against confident discrimination
- 8 categories with calibrated probability output — model expresses honest uncertainty rather than overconfident guesses
- **Active learning feedback loop** — every category override the user makes becomes a new labeled training example, merged on retraining

**Test accuracy:** ~57-65% (8-way classification, random baseline = 12.5%)

Confidence scores are intentionally moderate (30-60% on novel inputs) — the model expresses honest uncertainty rather than feigning confidence. UI uses three-tier confidence display: green (>60%), yellow (30-60%), red with top-3 alternatives (<30%).

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│                    Streamlit UI                        │
│  📋 Track   ·   📊 Dashboard   ·   💰 Budgets         │
└──────────────────────┬─────────────────────────────────┘
                       │
        ┌──────────────┼──────────────────┐
        ▼              ▼                  ▼
   sms_parser     classifier         visualization
   (regex)      (TF-IDF + LR)       (Plotly + pandas)
        │              │                  │
        └──────────────┼──────────────────┘
                       ▼
        ┌──────────────────────────────────┐
        │   Data Access Layer (db_*.py)    │
        │  expenses · budgets · categories │
        │           · corrections          │
        └──────────────────┬───────────────┘
                           ▼
                  ┌──────────────────┐
                  │  SQLite Database │
                  └──────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Streamlit 1.39 |
| ML | scikit-learn 1.6 (TF-IDF + Logistic Regression) |
| Data | pandas 2.2 |
| Charts | Plotly 5.24 |
| Database | SQLite (built-in) |
| Language | Python 3.12 |

---

## 🚀 Run Locally

```bash
# Clone and enter
git clone https://github.com/Sav04/smart-expense-tracker.git
cd smart-expense-tracker

# Set up environment
python -m venv venv
source venv/bin/activate          # macOS/Linux
venv\Scripts\Activate.ps1         # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Initialize database + train model
python init_db.py
python train_classifier.py

# Optional: load demo data
python seed_demo_data.py

# Run
streamlit run app.py
```

Open http://localhost:8501

---

## 📁 Project Structure

```
smart-expense-tracker/
├── app.py                          # Main Streamlit app, 3 top-level tabs
├── classifier.py                   # Lazy-loaded ML predict interface
├── train_classifier.py             # Training pipeline + retrain API
├── training_data.py                # 225 labeled seed examples
├── sms_parser.py                   # Indian bank SMS regex parser
├── visualization.py                # Plotly chart builders
├── seed_demo_data.py               # Demo data for fresh deployments
├── init_db.py                      # SQLite schema creation
├── database.py                     # Connection helper
├── db_categories.py                # Category DAL
├── db_expenses.py                  # Expenses CRUD
├── db_budgets.py                   # Budget CRUD with alert levels
├── db_corrections.py               # User correction storage
├── models/
│   └── expense_classifier.joblib   # Persisted trained model
├── requirements.txt
└── README.md
```

---

## 🎯 Future Improvements

- **Sentence-embedding classifier** — replace TF-IDF with `sentence-transformers` for better semantic understanding ("books for school" ≈ "school supplies" without explicit training overlap)
- **Multi-user authentication** — currently single-user by design; auth + per-user databases would scale this for shared deployment
- **CSV/PDF import** — bank statement upload as a third data source alongside SMS and manual
- **Recurring expense detection** — identify subscriptions automatically
- **Mobile app** — React Native / Flutter wrapper for native SMS-receive integration

---

## 👤 Author

**Utsav Johri**
Final-year EEE student, VIT Chennai
📧 johriutsav@gmail.com · 💻 [github.com/Sav04](https://github.com/Sav04)

---

## 📄 License

MIT