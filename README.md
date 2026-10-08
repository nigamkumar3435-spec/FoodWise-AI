# FoodWise AI

> **Predict demand before cooking. Redirect surplus before it becomes waste.**

AI-powered food demand forecasting and surplus redistribution platform for restaurants, college canteens, hotels, hostels, and catering services.

---

## Problem Statement

Food-serving organizations overprepare because they rely on manual estimates, causing:
- Unnecessary food waste (15–30% overproduction is common)
- Higher operational costs
- Poor inventory planning
- Inefficient surplus handling while nearby NGOs need food

---

## SDG Alignment

| Goal | Description |
|------|-------------|
| **SDG 2 — Zero Hunger** | Supports redistribution of edible surplus to NGOs and food banks |
| **SDG 12 — Responsible Consumption** | Helps reduce preventable food waste through AI-powered planning |

FoodWise *contributes to* and *supports* these goals. It does not claim to solve hunger alone.

---

## Features

### Core Modules
1. **AI Demand Prediction** — ML model (GradientBoosting/RandomForest) forecasts how much food to prepare
2. **Surplus Detection** — Auto-calculates surplus and waste percentage from recorded consumption
3. **Food Redistribution Matching** — Geo-weighted algorithm matches surplus with suitable nearby NGOs
4. **AI Food Management Assistant** — Rule-based chatbot that answers questions using real dashboard data

### User Roles
- **Food Provider** (restaurant/canteen/hotel/hostel/caterer): dashboard, predictions, history, surplus listings, donations, analytics, AI assistant
- **NGO / Food Receiver**: browse available food, request food, track donations
- **Admin**: user management, listing moderation, platform analytics

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Bootstrap 5, Chart.js, Font Awesome |
| Backend | Python 3, Flask, Flask-SQLAlchemy, Flask-Login, Gunicorn (prod) |
| Database | SQLite (dev) — swap to PostgreSQL/MySQL via `DATABASE_URL` |
| ML | scikit-learn (GradientBoosting, RandomForest, LinearRegression), joblib, pandas, numpy |
| Auth | Werkzeug password hashing, Flask-Login sessions, CSRF protection |

---

## System Architecture

```
foodwise-ai/
├── app.py                  # Entry point
├── config.py               # Flask config (dev/prod)
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py         # App factory
│   ├── models/             # SQLAlchemy ORM models
│   ├── routes/             # Flask blueprints
│   ├── services/           # Business logic
│   │   ├── prediction_service.py
│   │   ├── matching_service.py
│   │   ├── ai_assistant.py
│   │   ├── llm_service.py   # Optional LLM abstraction
│   │   └── impact_service.py
│   ├── templates/          # Jinja2 HTML templates
│   └── static/             # CSS, JS, images
├── ml/
│   ├── generate_data.py    # Synthetic dataset generator
│   ├── feature_engineering.py
│   ├── train_model.py      # Train + compare models, save best
│   ├── predict.py          # Standalone inference
│   ├── evaluate.py         # Metrics + efficiency score
│   └── models/             # Saved .pkl and metadata
├── data/
│   └── raw/sample_food_data.csv
└── tests/
    └── test_app.py         # 22 pytest tests
```

---

## Machine Learning

### Problem
Regression: predict `food_consumed` (meals) from historical and contextual features.

### Features (13 total)
| Feature | Description |
|---------|-------------|
| `day_of_week` | 0=Mon … 6=Sun |
| `meal_type_enc` | 0=breakfast, 1=lunch, 2=dinner |
| `number_of_people` | Expected headcount |
| `is_holiday` / `is_weekend` | Binary flags |
| `event_type_enc` | normal/holiday/festival/college_event/weekend/conference |
| `weather_enc` | clear/cloudy/rainy/hot/cold |
| `temperature` | °C |
| `prev_day_consumption` | Lag-1 (same meal type) |
| `last_3_day_avg` | Rolling 3-day average |
| `last_7_day_avg` | Rolling 7-day average |
| `same_day_last_week_consumption` | Same day-of-week, previous week |
| `consumption_trend` | Ratio of last_3 / last_7 |

**Data leakage prevention:** All lag features use `.shift(1)` — no future data enters training.

### Split Strategy
**Chronological 80/20 split** — first 80% of dates = training, last 20% = testing. No random shuffle to prevent temporal leakage.

### Model Comparison (sample dataset)
| Model | MAE | RMSE | R² |
|-------|-----|------|----|
| LinearRegression | ~16 meals | ~22 meals | 0.94 |
| RandomForest | ~14 meals | ~21 meals | 0.95 |
| **GradientBoosting** | **~12 meals** | **~17 meals** | **0.97** |

Best model is automatically selected by R² and saved to `ml/models/best_model.pkl`.

### Prediction Reliability Score
A **platform score** (not a statistical probability) based on:
- Data availability (0–60 historical records → 0–100%)  
- Consistency of recent vs. historical consumption

Clearly labeled in the UI as "Platform Reliability Score."

---

## Installation

### Prerequisites
- Python 3.9+
- pip

### Steps

```bash
# 1. Clone / navigate to project
cd foodwise-ai

# 2. Create virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
copy .env.example .env
# Edit .env and set SECRET_KEY

# 5. Initialize database
flask db init
flask db migrate -m "initial"
flask db upgrade

# 6. Seed admin account
flask seed-admin

# 7. (Optional) Seed demo data
flask seed-demo

# 8. Train ML model
python ml/train_model.py

# 9. Run the application (development)
python run.py

# 9b. Run with Gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

Then open: **http://127.0.0.1:5000**

---

## Environment Variables

See `.env.example` for all options:

```env
SECRET_KEY=your-long-secret-key
DATABASE_URL=sqlite:///foodwise.db      # or postgresql://...
FLASK_ENV=development

# Optional LLM (falls back to rule-based assistant if not set)
AI_PROVIDER=openai                      # openai | gemini | watsonx
AI_API_KEY=sk-...

# IBM watsonx (if AI_PROVIDER=watsonx)
WATSONX_URL=https://...
WATSONX_PROJECT_ID=...

# Admin seed credentials
ADMIN_EMAIL=admin@foodwise.ai
ADMIN_PASSWORD=Admin@123
```

**Never commit `.env` to version control.**

---

## Database Setup

The project uses Flask-Migrate for database migrations:

```bash
flask db init       # Initialize migration folder (first time only)
flask db migrate    # Generate migration script
flask db upgrade    # Apply migrations
```

For production with PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@host/dbname
```

---

## Model Training

```bash
# Generates synthetic data + trains all models
python ml/train_model.py

# Output:
# Best Model: GradientBoosting
# MAE: 12.20 meals
# RMSE: 16.98 meals
# R2 Score: 0.9667
# Model saved -> ml/models/best_model.pkl
```

The trained model is automatically used by the prediction service. If no model exists, the service falls back to a rule-based statistical estimate.

---

## Running Tests

```bash
pytest tests/ -v
```

22 tests covering:
- User registration/login/permissions
- Password hashing
- Food history calculations
- Impact service
- Feature engineering (no-leakage check)
- NGO matching (Haversine, scoring functions)
- Prediction service fallback

---

## Demo Accounts

After running `flask seed-demo`:

| Role | Email | Password |
|------|-------|----------|
| Food Provider | demo.canteen@foodwise.ai | Demo@1234 |
| NGO | demo.ngo@foodwise.ai | Demo@1234 |
| Admin | admin@foodwise.ai | Admin@FoodWise123 |

---

## NGO Matching Algorithm

Match Score formula:

```
Match Score = Distance Score × 0.30
            + Capacity Score × 0.25
            + Food Compatibility × 0.25
            + Pickup Feasibility × 0.20
```

- **Distance**: Haversine great-circle distance. Score 1.0 at ≤1 km, 0.0 at ≥30 km.
- **Capacity**: NGO daily capacity ÷ listing quantity (capped at 1.0).
- **Compatibility**: 1.0 if listing category is in NGO's accepted list; 0.7 if no restriction; 0.2 otherwise.
- **Pickup**: Score based on minutes remaining before deadline.

---

## AI Assistant

The AI assistant uses **only real database values** — it never invents data:

- Queries last 7 and 14 days of food history
- Calculates waste % trends, per-meal surplus, and worst day
- Answers questions: waste trends, daily summary, reduction tips, savings
- Integrates with IBM watsonx / OpenAI / Google Gemini if API key is set
- Falls back to rule-based engine if no key is configured

---

## Food Safety Disclaimer

FoodWise AI does not guarantee the safety of any surplus food listed on the platform. Providers must confirm that all listed food is stored appropriately and suitable for redistribution. Food safety remains the responsibility of the listing provider.

---

## Future Improvements

- IoT weighing integration for real-time preparation tracking
- Mobile app (React Native)
- Advanced ML with XGBoost + SHAP explainability
- Map-based NGO discovery
- Automated weekly report email
- Multi-language support

---

## Revenue Model

| Tier | Target | Features |
|------|--------|----------|
| Starter (Free) | NGOs, small canteens | Basic prediction, manual history |
| Professional | Restaurants, hotels | Advanced analytics, AI assistant |
| Enterprise | Universities, chains | Custom ML, API access, IoT integration |

---

*FoodWise AI — supporting SDG 2 and SDG 12 through intelligent food management.*

## Changelog

### v1.1.0
- **Fix:** NGO registration — disabled hidden provider section inputs on form submit to prevent empty `organization_name` collision
- **Fix:** NGO registration — renamed NGO org-name field to `ngo_organization_name` to avoid duplicate field name conflict with provider section
- **Added:** `gunicorn` to `requirements.txt` for production WSGI deployment
- **Updated:** Default admin password in `.env.example` changed to `Admin@123`
- **Updated:** Startup script `run.py` added for clean server launch

### v1.0.0
- Initial release: full FoodWise AI platform with ML pipeline, provider/NGO/admin dashboards, AI assistant, NGO matching, and impact metrics
