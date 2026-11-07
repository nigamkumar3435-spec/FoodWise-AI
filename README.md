# 🍽️ FoodWise AI

<div align="center">

**Predict demand before cooking. Redirect surplus before it becomes waste.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-black?logo=flask)](https://flask.palletsprojects.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4.2-orange?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![SDG 2](https://img.shields.io/badge/SDG-2%20Zero%20Hunger-brightgreen)](https://sdgs.un.org/goals/goal2)
[![SDG 12](https://img.shields.io/badge/SDG-12%20Responsible%20Consumption-yellow)](https://sdgs.un.org/goals/goal12)

*IBM SkillsBuild ML-AI Internship Project · v1.1.0*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [SDG Alignment](#-sdg-alignment)
- [Live Demo](#-live-demo)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Machine Learning](#-machine-learning)
- [NGO Matching Algorithm](#-ngo-matching-algorithm)
- [AI Assistant](#-ai-assistant)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Database Setup](#-database-setup)
- [Model Training](#-model-training)
- [Running Tests](#-running-tests)
- [Demo Accounts](#-demo-accounts)
- [Revenue Model](#-revenue-model)
- [Food Safety Disclaimer](#️-food-safety-disclaimer)
- [Future Roadmap](#-future-roadmap)
- [Changelog](#-changelog)

---

## 🌟 Overview

**FoodWise AI** is a full-stack, AI-powered web platform that helps food-serving organisations — restaurants, college canteens, hotels, hostels, and catering services — eliminate preventable food waste through intelligent demand forecasting, and redistribute any unavoidable surplus to nearby NGOs in real time.

The platform combines a **scikit-learn ML regression pipeline**, a **geo-weighted NGO matching engine**, a **data-grounded AI chatbot**, and a full **three-role web portal** (Provider · NGO · Admin) built on Flask.

> For a full deep-dive into every component, see [SYNOPSIS.md](SYNOPSIS.md).

---

## 🔴 Problem Statement

Food-serving organisations consistently overprepare meals because they depend on intuition and manual estimates rather than data:

| Impact | Reality |
|--------|---------|
| 🗑️ Overproduction | 15–30% of cooked food is wasted daily |
| 💸 Cost bleed | Unnecessary ingredient purchases every cycle |
| 📉 No feedback loop | No system learns from past over/under-preparation |
| 😔 Missed opportunity | Surplus is discarded while nearby NGOs face food shortages |

FoodWise AI closes this loop with **ML-driven preparation guidance** and a **marketplace for surplus redistribution**.

---

## 🌍 SDG Alignment

| Goal | How FoodWise Contributes |
|------|--------------------------|
| **SDG 2 — Zero Hunger** | Surplus food redistribution directly feeds NGOs and communities in need |
| **SDG 12 — Responsible Consumption & Production** | AI demand forecasting prevents avoidable overproduction at the source |

> FoodWise *contributes to* and *supports* these goals. It is a decision-support tool — it does not claim to solve hunger alone.

---

## 🎬 Live Demo

Run locally in under 5 minutes — see [Getting Started](#-getting-started).

| Role | Email | Password |
|------|-------|---------|
| 🍳 Food Provider | `demo.canteen@foodwise.ai` | `Demo@1234` |
| 🤝 NGO | `demo.ngo@foodwise.ai` | `Demo@1234` |
| 🔐 Admin | `admin@foodwise.ai` | `Admin@123` |

---

## ✨ Features

### Core Modules

| Module | Description |
|--------|-------------|
| 🤖 **AI Demand Prediction** | GradientBoosting ML model forecasts exactly how many meals to prepare per session |
| 📊 **Surplus Detection** | Auto-calculates surplus and waste % from every recorded meal session |
| 🗺️ **NGO Matching** | Geo-weighted algorithm scores and ranks nearby NGOs for each surplus listing |
| 💬 **AI Food Assistant** | Data-grounded chatbot answers questions using your real dashboard data |
| 📈 **Impact Tracking** | Tracks kg saved, meals redistributed, money saved, and successful donations |
| 📉 **Analytics Dashboard** | Chart.js visualisations — waste trends, meal-type breakdown, weekly comparisons |

### User Roles

#### 🍳 Food Provider
Full portal with 9 screens: Dashboard · Predict · Food History · Surplus Listings · Create Surplus · NGO Matches · Donations · Analytics · AI Assistant

#### 🤝 NGO / Food Receiver
Browse available surplus · Request food · Track donations · Manage profile

#### 🔐 Admin
Platform-wide KPIs · User management · Listings moderation · Donation oversight

---

## 🛠️ Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend** | Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate | Flask 3.0.3 |
| **ML** | scikit-learn, pandas, numpy, joblib | scikit-learn 1.4.2 |
| **Frontend** | HTML5, CSS3, Bootstrap 5, Chart.js, Font Awesome, Jinja2 | Bootstrap 5 |
| **Database** | SQLite (dev) · PostgreSQL/MySQL (prod via `DATABASE_URL`) | — |
| **Auth** | Werkzeug PBKDF2-SHA256 hashing · Flask-Login sessions · CSRF tokens | Werkzeug 3.0.3 |
| **Production** | Gunicorn (multi-worker WSGI server) | latest |
| **Optional LLM** | OpenAI GPT-3.5 · Google Gemini 1.5 Flash · IBM watsonx Granite-13B | — |

---

## 🤖 Machine Learning

### Problem
**Supervised Regression** — predict `food_consumed` (meals) from 13 contextual and historical features.

### Features (13 total)

| Feature | Type | Description |
|---------|------|-------------|
| `day_of_week` | Ordinal | 0=Mon … 6=Sun |
| `meal_type_enc` | Ordinal | 0=breakfast, 1=lunch, 2=dinner |
| `number_of_people` | Continuous | Expected headcount |
| `is_holiday` / `is_weekend` | Binary | Calendar flags |
| `event_type_enc` | Ordinal | normal / holiday / festival / college_event / weekend / conference |
| `weather_enc` | Ordinal | clear / cloudy / rainy / hot / cold |
| `temperature` | Continuous | Degrees Celsius |
| `prev_day_consumption` | Lag-1 | Previous day's consumption (same meal type) |
| `last_3_day_avg` | Rolling | 3-day moving average |
| `last_7_day_avg` | Rolling | 7-day moving average |
| `same_day_last_week_consumption` | Lag | Same weekday, previous week |
| `consumption_trend` | Ratio | `last_3_avg / last_7_avg` |

> **Data leakage prevention:** All lag/rolling features use `.shift(1)` — no future data enters training.

### Split Strategy
**Chronological 80/20 split** — first 80% of dates = training, last 20% = testing. No random shuffle to prevent temporal leakage.

### Model Comparison

| Model | MAE | RMSE | R² |
|-------|-----|------|----|
| LinearRegression | ~16 meals | ~22 meals | 0.94 |
| RandomForest | ~14 meals | ~21 meals | 0.95 |
| **GradientBoosting** | **~12 meals** | **~17 meals** | **0.97** |

The model with the highest R² is automatically selected and saved to `ml/models/best_model.pkl`.

### Prediction Reliability Score
A **platform score** (not a statistical probability) based on:
- Data availability (0–60 historical records → 0–100%)
- Consistency of recent vs. historical consumption

Clearly labelled in the UI as *"Platform Reliability Score"*.

### Fallback
If no trained model exists, `PredictionService` falls back to a rule-based estimate using rolling 7-day averages + event-type multipliers — no crashes, always a useful answer.

---

## 🗺️ NGO Matching Algorithm

Each surplus listing is scored against every registered NGO using a weighted formula:

```
Match Score = Distance Score     × 0.30
            + Capacity Score     × 0.25
            + Food Compatibility × 0.25
            + Pickup Feasibility × 0.20
```

| Component | Scoring Logic |
|-----------|--------------|
| **Distance** | Haversine great-circle distance — 1.0 at ≤1 km, 0.0 at ≥30 km |
| **Capacity** | NGO daily capacity ÷ listing quantity (capped at 1.0) |
| **Compatibility** | 1.0 if category matches; 0.7 if no restriction; 0.2 otherwise |
| **Pickup** | 1.0 at 4+ hours before deadline, 0.0 at deadline |

Top-N matched NGOs are displayed with per-dimension score breakdowns for full transparency.

---

## 💬 AI Assistant

The AI assistant uses **only real database values** — it never invents data:

- Queries last 7, 14, and 30 days of food history
- Calculates waste % trends, per-meal surplus, and worst-performing days
- Answers: waste trends · daily summary · reduction tips · savings impact
- Integrates with **IBM watsonx / OpenAI / Google Gemini** if an API key is set
- Falls back to a deterministic rule-based engine if no key is configured

Supported questions include:
> *"How much should I prepare tomorrow?"*  
> *"Why did food waste increase this week?"*  
> *"Which day has the highest waste?"*  
> *"How much food did we save this month?"*

---

## 📁 Project Structure

```
foodwise-ai/
├── app.py                      # Entry point + CLI commands (seed-admin, seed-demo)
├── run.py                      # Dev server launcher
├── config.py                   # Flask config (Dev / Prod)
├── requirements.txt
├── .env.example
├── SYNOPSIS.md                 # Detailed technical synopsis
│
├── app/
│   ├── __init__.py             # App factory (create_app)
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py             # User (auth, role)
│   │   ├── organization.py     # Organization (providers & NGOs)
│   │   ├── food_history.py     # FoodHistory · DemandPrediction · ImpactMetric
│   │   └── surplus.py          # SurplusListing · DonationRequest
│   ├── routes/                 # Flask blueprints
│   │   ├── auth.py             # /auth/*
│   │   ├── provider.py         # /provider/* (full portal)
│   │   ├── ngo.py              # /ngo/*
│   │   ├── admin.py            # /admin/*
│   │   ├── api.py              # /api/* (AJAX JSON)
│   │   └── errors.py           # 400 / 403 / 404 / 500
│   ├── services/               # Business logic layer
│   │   ├── prediction_service.py
│   │   ├── matching_service.py
│   │   ├── ai_assistant.py
│   │   ├── llm_service.py      # OpenAI · Gemini · watsonx adapter
│   │   └── impact_service.py
│   ├── templates/              # Jinja2 HTML templates
│   └── static/                 # CSS, JS, images
│
├── ml/
│   ├── generate_data.py        # Synthetic dataset generator
│   ├── feature_engineering.py  # Lag features, encoding, leakage prevention
│   ├── train_model.py          # Train + compare 3 models, save best
│   ├── predict.py              # Standalone CLI inference
│   ├── evaluate.py             # Metrics + efficiency score
│   └── models/
│       ├── best_model.pkl      # Serialised scikit-learn model
│       ├── model_meta.json     # R², MAE, RMSE, feature list, training date
│       └── feature_importance.csv
│
├── data/raw/
│   └── sample_food_data.csv
├── migrations/                 # Alembic migration scripts
└── tests/
    └── test_app.py             # 22 pytest tests
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/nigamkumar3435-spec/FoodWise-AI.git
cd FoodWise-AI

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
copy .env.example .env       # Windows
# cp .env.example .env       # Linux/macOS
# Edit .env and set at least SECRET_KEY

# 5. Initialise the database
flask db init
flask db migrate -m "initial"
flask db upgrade

# 6. Seed admin account
flask seed-admin

# 7. (Optional) Seed demo data — provider + NGO + 60 days of history
flask seed-demo

# 8. Train the ML model
python ml/train_model.py

# 9. Start the development server
python run.py
```

Open **http://127.0.0.1:5000** in your browser.

#### Production (Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# ── Required ────────────────────────────────────
SECRET_KEY=your-long-random-secret-key
DATABASE_URL=sqlite:///foodwise.db      # or postgresql://user:pass@host/db
FLASK_ENV=development                   # or production

# ── Optional LLM Integration ────────────────────
# Falls back to rule-based assistant if not set
AI_PROVIDER=openai                      # openai | gemini | watsonx
AI_API_KEY=sk-...

# IBM watsonx (only when AI_PROVIDER=watsonx)
WATSONX_URL=https://...
WATSONX_PROJECT_ID=...

# ── Seed Credentials ────────────────────────────
ADMIN_EMAIL=admin@foodwise.ai
ADMIN_PASSWORD=Admin@123
```

> ⚠️ **Never commit `.env` to version control.**

---

## 🗄️ Database Setup

Flask-Migrate handles schema versioning via Alembic:

```bash
flask db init       # First-time setup only
flask db migrate    # Generate migration script after model changes
flask db upgrade    # Apply migrations to the database
```

For production, switch to PostgreSQL by updating `DATABASE_URL`:
```env
DATABASE_URL=postgresql://user:password@host/dbname
```

---

## 🧠 Model Training

```bash
python ml/train_model.py
```

Expected output:
```
============================================================
FoodWise AI — Model Training
============================================================
Train: 1440 rows | Test: 360 rows

Training LinearRegression...
Training RandomForest...
Training GradientBoosting...

============================================================
>> Best Model: GradientBoosting
   MAE:  12.20 meals
   RMSE: 16.98 meals
   R²:   0.9667
============================================================
Model saved -> ml/models/best_model.pkl
Metadata saved -> ml/models/model_meta.json
```

The trained model is automatically loaded by `PredictionService`. If no model is found, the service falls back to a rule-based statistical estimate.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

**22 tests** covering:

| Area | Tests |
|------|-------|
| User registration / login / logout | Auth flows |
| Password hashing | Correct & incorrect checks |
| Role-based access | Cross-role route protection |
| Food history | Record creation, waste % computation |
| Feature engineering | No-leakage validation on lag features |
| Impact service | Metric recalculation accuracy |
| NGO matching | Haversine distance, scoring functions |
| Prediction service | ML loading, statistical fallback |

---

## 👥 Demo Accounts

After running `flask seed-demo`:

| Role | Email | Password |
|------|-------|---------|
| 🍳 Food Provider | `demo.canteen@foodwise.ai` | `Demo@1234` |
| 🤝 NGO | `demo.ngo@foodwise.ai` | `Demo@1234` |
| 🔐 Admin | `admin@foodwise.ai` | `Admin@123` |

---

## 💰 Revenue Model

| Tier | Target | Features |
|------|--------|---------|
| **Starter (Free)** | NGOs, small canteens | Basic ML prediction, manual food history |
| **Professional** | Restaurants, hotels | Advanced analytics, AI assistant, priority NGO matching |
| **Enterprise** | Universities, chains | Custom ML training, REST API access, IoT integration |

---

## ⚠️ Food Safety Disclaimer

FoodWise AI does not guarantee the safety of any surplus food listed on the platform. Providers must confirm that all listed food is stored appropriately and is suitable for redistribution before creating a listing. **Food safety remains the sole responsibility of the listing provider.**

---

## 🔭 Future Roadmap

| Feature | Description |
|---------|-------------|
| 🔌 **IoT Integration** | Real-time weighing scales feed preparation data automatically |
| 📱 **Mobile App** | React Native app for providers and NGO field workers |
| 🚀 **XGBoost + SHAP** | Higher accuracy + explainable AI for each prediction |
| 🗺️ **Map View** | Leaflet.js / Google Maps for visual NGO discovery |
| 📧 **Weekly Reports** | Automated email digest of waste trends and impact metrics |
| 🌐 **Multi-Language** | i18n support for regional Indian languages |

---

## 📄 Changelog

### v1.1.0
- **Fix:** NGO registration — disabled hidden provider-section inputs on submit to prevent empty `organization_name` collision
- **Fix:** NGO registration — renamed NGO org-name field to `ngo_organization_name` to avoid duplicate field name conflict
- **Added:** `gunicorn` to `requirements.txt` for production WSGI deployment
- **Added:** `SYNOPSIS.md` — full technical deep-dive into all components
- **Updated:** Default admin password in `.env.example` changed to `Admin@123`
- **Updated:** `run.py` added for clean, unbuffered server launch

### v1.0.0
- Initial release: full FoodWise AI platform with ML pipeline, provider/NGO/admin dashboards, AI assistant, NGO matching, and impact metrics

---

<div align="center">

*FoodWise AI — built during the IBM SkillsBuild ML-AI Internship*  
*Supporting SDG 2 (Zero Hunger) and SDG 12 (Responsible Consumption & Production)*

</div>
