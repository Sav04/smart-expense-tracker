# 💰 Smart Expense Tracker

An AI-powered personal expense tracker that auto-categorizes spending using ML, parses Indian bank SMS messages for automatic entry, and tracks per-category budgets with smart alerts.

> **Status:** 🚧 Under construction. Phase 1 (setup) complete.

## Features (planned)

- 📲 **SMS bank parser** — paste an HDFC/SBI/ICICI/Axis transaction SMS, app auto-fills the expense
- 🤖 **ML category classifier** — text → category (Food, Transport, Bills, Shopping, etc.)
- 📊 **Visual dashboard** — monthly trends, category breakdown, spending heatmap
- 🎯 **Per-category budgets with alerts** — warns at 80%, alerts at 100% of category limit
- 💾 **SQLite persistence** — your data stays local, between sessions

## Tech Stack

- **Frontend:** Streamlit
- **Database:** SQLite
- **ML:** scikit-learn (text classification)
- **Visualization:** Plotly
- **Currency:** INR (₹) only

## Setup (after Phase 1)

```bash
git clone https://github.com/Sav04/smart-expense-tracker.git
cd expense-tracker
py -3.12 -m venv venv
venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Author

Built by Utsav Johri — final-year EEE @ VIT Chennai, exploring AI/ML engineering.
- 📂 [Resume Analyzer (Project #1)](https://github.com/Sav04/resume-analyzer) — [Live](https://sav04-resume-analyzer.streamlit.app)
- 🔗 [LinkedIn](https://linkedin.com/in/your-handle) | 📫 johriutsav@gmail.com