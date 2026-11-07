# 🍽️ FoodWise AI — Detailed Project Synopsis

> **Predict demand before cooking. Redirect surplus before it becomes waste.**

---

## 📌 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [SDG Alignment](#3-sdg-alignment)
4. [System Architecture](#4-system-architecture)
5. [Technology Stack — Detailed Breakdown](#5-technology-stack--detailed-breakdown)
6. [Database Design (ORM Models)](#6-database-design-orm-models)
7. [Machine Learning Pipeline](#7-machine-learning-pipeline)
8. [Core Services & Business Logic](#8-core-services--business-logic)
9. [Application Routes & Blueprints](#9-application-routes--blueprints)
10. [User Roles & Dashboards](#10-user-roles--dashboards)
11. [AI Assistant](#11-ai-assistant)
12. [NGO Matching Algorithm](#12-ngo-matching-algorithm)
13. [Impact Tracking System](#13-impact-tracking-system)
14. [Security & Auth Design](#14-security--auth-design)
15. [Testing](#15-testing)
16. [Configuration & Deployment](#16-configuration--deployment)
17. [Project Directory Structure](#17-project-directory-structure)
18. [Future Roadmap](#18-future-roadmap)

---

## 1. Project Overview

**FoodWise AI** is a full-stack, AI-powered web platform built to help food-serving organisations — restaurants, college canteens, hotels, hostels, and catering services — dramatically reduce food waste by predicting how much food to prepare and intelligently redistributing any unavoidable surplus to nearby NGOs and food banks.

The platform sits at the intersection of **machine learning**, **operations management**, and **social impact**, making it both technically sophisticated and practically useful for real-world deployment.

| Attribute | Detail |
|-----------|--------|
| **Type** | Full-Stack Web Application |
| **Language** | Python 3.9+ |
| **Framework** | Flask (micro-web framework) |
| **ML Library** | scikit-learn |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Version** | 1.1.0 |
| **Context** | IBM SkillsBuild ML-AI Internship Project |

---

## 2. Problem Statement

Food-serving organisations consistently overprepare meals because they rely on **manual estimates and intuition** rather than data. This results in:

- 🗑️ **15–30% overproduction** is the industry norm
- 💸 **Higher operational costs** from unnecessary food purchases
- 📉 **Poor inventory planning** with no feedback loop
- 😔 **Wasted surplus** while nearby NGOs and food banks face shortages
- 🌍 **Avoidable environmental impact** from food going to landfill

FoodWise AI solves this by providing an **ML-powered prediction engine** that learns from historical consumption patterns, combined with a **geo-weighted redistribution marketplace** that connects surplus food with verified NGOs in real time.

---

## 3. SDG Alignment

FoodWise AI is explicitly aligned with two United Nations Sustainable Development Goals:

| SDG | Goal | How FoodWise Contributes |
|-----|------|--------------------------|
| **SDG 2** | Zero Hunger | Surplus food redistribution to NGOs and food banks feeds communities in need |
| **SDG 12** | Responsible Consumption & Production | AI demand forecasting directly reduces preventable overproduction and food waste |

> FoodWise *contributes to* and *supports* these goals. It is a tool that assists human decision-making — it does not claim to solve hunger alone.

---

## 4. System Architecture

The application follows a **layered MVC architecture** using Flask's Application Factory pattern:

```
┌──────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                       │
│            HTML5 · Bootstrap 5 · Chart.js · JS               │
└──────────────────────┬───────────────────────────────────────┘
                       │  HTTP / AJAX
┌──────────────────────▼───────────────────────────────────────┐
│                    FLASK APPLICATION                          │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Blueprints│  │  Jinja2      │  │  Flask Extensions    │  │
│  │  (Routes)  │  │  Templates   │  │  Login · CSRF · ORM  │  │
│  └─────┬──────┘  └──────────────┘  └──────────────────────┘  │
│        │                                                      │
│  ┌─────▼──────────────────────────────────────────────────┐  │
│  │                  SERVICE LAYER                          │  │
│  │  PredictionService · MatchingService · AIAssistant     │  │
│  │  ImpactService · LLMService                            │  │
│  └─────┬──────────────────────────────────────────────────┘  │
│        │                                                      │
│  ┌─────▼──────────────────────────────────────────────────┐  │
│  │               SQLALCHEMY ORM (Models)                   │  │
│  │  User · Organization · FoodHistory · SurplusListing    │  │
│  │  DonationRequest · DemandPrediction · ImpactMetric     │  │
│  └─────┬──────────────────────────────────────────────────┘  │
└────────┼──────────────────────────────────────────────────────┘
         │
┌────────▼───────────────────────────────┐
│          DATABASE (SQLite / PostgreSQL) │
└────────────────────────────────────────┘
         │
┌────────▼───────────────────────────────┐
│          ML PIPELINE (scikit-learn)     │
│  generate_data → feature_engineering   │
│  → train_model → best_model.pkl        │
└────────────────────────────────────────┘
```

---

## 5. Technology Stack — Detailed Breakdown

### 5.1 Backend

| Library | Version | Purpose |
|---------|---------|---------|
| **Flask** | 3.0.3 | Core web micro-framework — routing, request handling, Jinja2 templating |
| **Flask-SQLAlchemy** | 3.1.1 | ORM for defining and querying database models in Python |
| **Flask-Login** | 0.6.3 | Session-based user authentication, `current_user`, `login_required` |
| **Flask-WTF** | 1.2.1 | WTForms integration + automatic CSRF token generation and validation |
| **Flask-Migrate** | 4.0.7 | Alembic-powered database schema migrations via CLI commands |
| **Werkzeug** | 3.0.3 | WSGI utility — password hashing (`generate_password_hash`, `check_password_hash`), security helpers |
| **python-dotenv** | 1.0.1 | Loads environment variables from `.env` files into `os.environ` |
| **WTForms** | 3.1.2 | Form validation and rendering engine |
| **email-validator** | 2.1.1 | RFC-compliant email address validation for registration forms |
| **Gunicorn** | latest | Production-grade WSGI HTTP server (multi-worker process model) |

### 5.2 Machine Learning

| Library | Version | Purpose |
|---------|---------|---------|
| **scikit-learn** | 1.4.2 | ML model training: `LinearRegression`, `RandomForestRegressor`, `GradientBoostingRegressor`, `Pipeline`, `StandardScaler`, metrics |
| **pandas** | 2.2.2 | Data loading, feature engineering, lag/rolling computations, chronological splitting |
| **numpy** | 1.26.4 | Numerical operations, array manipulation, feature vector construction |
| **joblib** | 1.4.2 | Serialising/deserialising trained models to `.pkl` files for persistence |

### 5.3 Frontend

| Technology | Purpose |
|------------|---------|
| **HTML5** | Semantic page structure |
| **CSS3** | Custom styling on top of Bootstrap |
| **Bootstrap 5** | Responsive grid, components (cards, modals, navbars, badges), utility classes |
| **Chart.js** | Interactive canvas charts — line charts (consumption trends), bar charts (waste analysis), doughnut charts (meal-type split) |
| **Font Awesome** | Icon library used throughout the UI |
| **Jinja2** | Server-side templating — template inheritance (`base.html`), conditionals, loops, filters |
| **Vanilla JavaScript / AJAX** | Dynamic prediction requests and AI assistant chat without full page reloads |

### 5.4 Optional LLM Integrations

| Provider | Model Used | Library |
|----------|------------|---------|
| **OpenAI** | `gpt-3.5-turbo` | `openai` Python SDK |
| **Google Gemini** | `gemini-1.5-flash` | `google-generativeai` |
| **IBM watsonx** | `ibm/granite-13b-chat-v2` | `ibm-watsonx-ai` |

> All three are **optional**. If no API key is configured, the app falls back gracefully to its own deterministic rule-based AI assistant engine.

### 5.5 Database

| Env | Engine | Config |
|-----|--------|--------|
| Development | SQLite (`foodwise.db`) | File-based, zero setup |
| Production | PostgreSQL / MySQL | Set `DATABASE_URL` in environment |

---

## 6. Database Design (ORM Models)

FoodWise uses **7 SQLAlchemy ORM models** across 4 files:

### 6.1 `User`
Stores authentication and role data.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `full_name` | String(120) | Display name |
| `email` | String(120) | Unique, indexed |
| `password_hash` | String(256) | Werkzeug PBKDF2-SHA256 hash |
| `role` | String(20) | `provider` / `ngo` / `admin` |
| `phone` | String(20) | Optional contact |
| `is_active` | Boolean | Soft-disable accounts |
| `created_at` | DateTime | Auto-set UTC |

### 6.2 `Organization`
Links a User to their organisation profile (1-to-1).

| Column | Type | Notes |
|--------|------|-------|
| `organization_name` | String(150) | Restaurant/canteen/NGO name |
| `organization_type` | String(50) | `restaurant`, `canteen`, `hotel`, `hostel`, `catering`, `ngo`, `food_bank` |
| `city` / `address` | String | Location info |
| `latitude` / `longitude` | Float | GPS coordinates for geo-matching |
| `capacity` | Float | NGOs only — max daily meals/kg |
| `accepted_food_categories` | String(300) | NGOs only — comma-separated list |

### 6.3 `FoodHistory`
The core training data record — one row per meal session per day.

| Column | Type | Notes |
|--------|------|-------|
| `date` / `day_of_week` | Date / Int | When the meal occurred |
| `meal_type` | String | `breakfast`, `lunch`, `dinner` |
| `number_of_people` | Integer | Expected headcount |
| `food_prepared` | Float | Meals cooked |
| `food_consumed` | Float | Meals actually eaten |
| `surplus_food` | Float | prepared − consumed |
| `event_type` | String | `normal`, `holiday`, `festival`, `college_event`, `weekend`, `conference` |
| `weather_condition` | String | `clear`, `cloudy`, `rainy`, `hot`, `cold` |
| `temperature` | Float | Degrees Celsius |

Computed property: `waste_percentage = surplus_food / food_prepared × 100`

### 6.4 `DemandPrediction`
Stores every prediction made by the ML service (audit trail).

| Column | Type | Notes |
|--------|------|-------|
| `prediction_date` | Date | The date being predicted |
| `meal_type` | String | Which meal |
| `predicted_demand` | Float | Raw ML output (meals) |
| `recommended_preparation` | Float | Demand + safety buffer |
| `confidence_score` | Float | 0.0–1.0 platform reliability score |
| `model_version` | String | `v1` or `statistical_fallback` |

### 6.5 `ImpactMetric`
Aggregated impact statistics per organisation (1-to-1 with Organisation).

| Column | Notes |
|--------|-------|
| `total_food_saved_kg` | Donated meals × 0.35 kg/meal |
| `meals_saved` | Total meals redistributed |
| `money_saved` | Saved kg × Rs. 80/kg |
| `successful_donations` | Count of completed donation requests |
| `waste_reduction_percentage` | Lifetime waste rate |

### 6.6 `SurplusListing`
A food surplus advertisement posted by a provider.

| Column | Notes |
|--------|-------|
| `food_name` / `food_category` | What is being offered |
| `quantity` / `unit` | How much (`meals`, `kg`, `litres`) |
| `preparation_time` / `expiry_time` / `pickup_deadline` | Time constraints |
| `status` | `available` → `requested` → `assigned` → `collected` / `expired` |
| `latitude` / `longitude` | For distance-based NGO matching |
| `food_safety_confirmed` | Provider must confirm before listing |

### 6.7 `DonationRequest`
An NGO's request to collect a specific surplus listing.

| Column | Notes |
|--------|-------|
| `request_status` | `pending` → `approved` / `rejected` → `completed` |
| `request_time` / `approved_time` / `collected_time` | Full lifecycle timestamps |

---

## 7. Machine Learning Pipeline

### 7.1 Problem Formulation

**Supervised Regression** — predict `food_consumed` (continuous, in meals) from 13 contextual and historical features.

### 7.2 Data Generation (`ml/generate_data.py`)

A synthetic dataset generator creates realistic training data simulating a college canteen across ~2 years, incorporating:
- Meal-type patterns (breakfast/lunch/dinner base ratios)
- Weekend and holiday dips
- Festival spikes
- Weather impacts
- Random natural variance

### 7.3 Feature Engineering (`ml/feature_engineering.py`)

All transformations use **strict data-leakage prevention** — `.shift(1)` ensures no future data leaks into any lag feature.

| Feature | Type | Description |
|---------|------|-------------|
| `day_of_week` | Ordinal | 0=Monday … 6=Sunday |
| `meal_type_enc` | Ordinal | 0=breakfast, 1=lunch, 2=dinner |
| `number_of_people` | Continuous | Expected headcount for session |
| `is_holiday` | Binary | 1 if public holiday |
| `is_weekend` | Binary | Derived from `day_of_week >= 5` |
| `event_type_enc` | Ordinal | normal/holiday/festival/college_event/weekend/conference |
| `weather_enc` | Ordinal | clear/cloudy/rainy/hot/cold |
| `temperature` | Continuous | Degrees Celsius |
| `prev_day_consumption` | Lag-1 | Consumption from previous day (same meal type) |
| `last_3_day_avg` | Rolling | 3-day moving average (same meal type) |
| `last_7_day_avg` | Rolling | 7-day moving average (same meal type) |
| `same_day_last_week_consumption` | Lag | Same weekday, previous week |
| `consumption_trend` | Ratio | `last_3_day_avg / last_7_day_avg` |

### 7.4 Train / Test Split

**Chronological 80/20 split** — the first 80% of records (by date) go to training; the last 20% to testing. No random shuffle to prevent temporal leakage.

### 7.5 Models Compared

| Model | Hyperparameters | Notes |
|-------|----------------|-------|
| **LinearRegression** | With `StandardScaler` in a Pipeline | Baseline; interpretable |
| **RandomForestRegressor** | 200 trees, max_depth=12, min_samples_leaf=5 | Ensemble; handles non-linearity |
| **GradientBoostingRegressor** | 200 estimators, depth=5, lr=0.05, subsample=0.8 | Sequential boosting; best performer |

### 7.6 Model Selection & Persistence

```
Best Model: GradientBoosting
MAE:  ~12 meals
RMSE: ~17 meals
R2:   ~0.97
```

The model with the **highest R²** is automatically selected and saved to `ml/models/best_model.pkl` using `joblib`. Metadata is saved to `ml/models/model_meta.json`. Feature importances go to `ml/models/feature_importance.csv`.

### 7.7 Prediction Reliability Score

A **platform-defined score** (not a statistical probability) ranging 0.50–0.97:

```
score = 0.5 × (data_count / 60)        ← data availability
      + 0.5 × (1 − variability_ratio)  ← consistency
```

Labelled in the UI as *"Platform Reliability Score"* to avoid misleading users.

### 7.8 Statistical Fallback

If no trained model exists, `PredictionService` uses a rule-based estimate:
- Rolling 7-day average as base demand
- Event-type multipliers (festival → ×1.20, holiday → ×0.75, etc.)
- Returns `model_version = "statistical_fallback"`

---

## 8. Core Services & Business Logic

### 8.1 `PredictionService`
- Loads `best_model.pkl` via `joblib` at instantiation
- Queries `FoodHistory` for the requesting organisation to build historical statistics
- Constructs a 13-feature vector matching the training schema exactly
- Calls `model.predict()` → adds configurable safety buffer (default 5%)
- Persists results as `DemandPrediction` records for audit trail

### 8.2 `MatchingService`

```
Match Score = Distance Score     × 0.30
            + Capacity Score     × 0.25
            + Food Compatibility × 0.25
            + Pickup Feasibility × 0.20
```

| Component | Scoring Logic |
|-----------|--------------|
| **Distance** | Haversine great-circle distance. 1.0 at ≤1 km, 0.0 at ≥30 km, linear between |
| **Capacity** | NGO's daily capacity ÷ listing quantity (capped at 1.0) |
| **Compatibility** | 1.0 if category matches; 0.7 if no restriction; 0.2 if incompatible |
| **Pickup Feasibility** | 1.0 at 4+ hours remaining, 0.0 at deadline |

### 8.3 `AIAssistant`
- Queries last 7, 14, 30 days of `FoodHistory` and `ImpactMetric`
- Routes to keyword handlers or escalates to external LLM
- **Never invents numbers** — all responses cite real database values

### 8.4 `LLMService`

| Provider | Model |
|----------|-------|
| OpenAI | `gpt-3.5-turbo` |
| Google Gemini | `gemini-1.5-flash` |
| IBM watsonx | `ibm/granite-13b-chat-v2` |

Builds a structured real-data context string, then sends `system_prompt + context + user_question` to the LLM.

### 8.5 `ImpactService`

| Metric | Calculation |
|--------|-------------|
| `total_food_saved_kg` | `donated_meals × 0.35 kg/meal` |
| `money_saved` | `total_kg × Rs. 80/kg` |
| `meals_saved` | Total meals in completed donations |
| `successful_donations` | Count of completed `DonationRequest` |
| `waste_reduction_percentage` | Lifetime `surplus / prepared × 100` |

---

## 9. Application Routes & Blueprints

| Blueprint | URL Prefix | File | Purpose |
|-----------|-----------|------|---------|
| `main_bp` | `/` | `routes/main.py` | Landing page, About |
| `auth_bp` | `/auth` | `routes/auth.py` | Login, Register, Logout |
| `provider_bp` | `/provider` | `routes/provider.py` | Full provider portal |
| `ngo_bp` | `/ngo` | `routes/ngo.py` | NGO portal |
| `admin_bp` | `/admin` | `routes/admin.py` | Admin panel |
| `api_bp` | `/api` | `routes/api.py` | JSON REST endpoints for AJAX |

### Key Provider Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/provider/dashboard` | GET | KPIs, charts, recent history |
| `/provider/predict` | GET / POST | ML prediction form + result |
| `/provider/history` | GET / POST | Add and view food history |
| `/provider/surplus` | GET | View all surplus listings |
| `/provider/surplus/create` | GET / POST | Post new surplus listing |
| `/provider/matches/<id>` | GET | Ranked NGO matches for a listing |
| `/provider/analytics` | GET | In-depth waste analytics |
| `/provider/assistant` | GET / POST | AI chatbot |
| `/provider/donations` | GET | Manage incoming NGO requests |

---

## 10. User Roles & Dashboards

### Food Provider (9 screens)
Dashboard · Predict · Food History · Surplus Listings · Create Surplus · NGO Matches · Donations · Analytics · AI Assistant

### NGO / Food Receiver (6 screens)
Dashboard · Available Food · Request Food · My Requests · Donation History · Profile

### Admin (5 screens)
Dashboard · User Management · Listings Moderation · Donations Overview · Analytics

---

## 11. AI Assistant

```
User Question
      │
      ▼
LLMService.is_available()?
   ├── YES → Build context string from DB → Send to LLM → Return response
   └── NO  → Rule-based keyword engine → Query DB → Return deterministic answer
```

Supported intents:
- "How much to prepare tomorrow?"
- "Why did food waste increase?"
- "How can I reduce food waste?"
- "Which day has the highest waste?"
- "How much food did we save this month?"
- "Give me this week's summary."

---

## 12. NGO Matching Algorithm

```
Match Score (%) =
    Distance Score     × 30%
  + Capacity Score     × 25%
  + Food Compatibility × 25%
  + Pickup Feasibility × 20%

Distance:  <= 1 km → 1.0 | >= 30 km → 0.0 | linear between
Capacity:  ngo.capacity / listing.quantity (capped 1.0)
Compat:    category match → 1.0 | any accepted → 0.7 | mismatch → 0.2
Pickup:    >= 240 min → 1.0 | 0 min → 0.0 | linear
```

Distance computed with the **Haversine formula** from GPS lat/lon coordinates.

---

## 13. Impact Tracking System

| Metric | Calculation |
|--------|------------|
| 🥗 Food Saved (kg) | Completed donation meals × 0.35 kg |
| 🍽️ Meals Redistributed | Sum of quantities of all completed donations |
| 💰 Money Saved (Rs.) | Food saved kg × Rs. 80/kg |
| ✅ Successful Donations | Count of completed `DonationRequest` records |
| 📉 Waste Reduction % | Lifetime `(surplus / prepared) × 100` |

---

## 14. Security & Auth Design

| Feature | Implementation |
|---------|---------------|
| **Password Hashing** | `werkzeug.security` — PBKDF2-SHA256 with salt |
| **Session Management** | Flask-Login — `login_required`, `current_user` proxy |
| **CSRF Protection** | Flask-WTF `CSRFProtect` — hidden `csrf_token` on all forms |
| **Role-Based Access** | Custom decorators: `provider_required`, `ngo_required`, `admin_required` |
| **Secure Cookies** | `HTTPONLY=True`, `SAMESITE=Lax`; `SECURE=True` in production |
| **Secret Key** | From `SECRET_KEY` env var — never hardcoded |
| **Input Validation** | WTForms validators on all form fields |
| **Custom Error Pages** | 400 / 403 / 404 / 500 handlers |

---

## 15. Testing

22 automated pytest tests in [`tests/test_app.py`](tests/test_app.py):

```bash
pytest tests/ -v
```

| Test Area | Coverage |
|-----------|---------|
| Authentication | Registration, login, logout flows |
| Password Security | Hash generation, correct/incorrect checks |
| Role Permissions | Cross-role access prevention |
| Food History | Record creation, waste % calculation |
| Feature Engineering | No-leakage check on lag features |
| Impact Service | Metric recalculation accuracy |
| NGO Matching | Haversine accuracy, scoring functions |
| Prediction Service | ML loading, statistical fallback |

---

## 16. Configuration & Deployment

### Environment Variables

```env
SECRET_KEY=your-long-secret-key
DATABASE_URL=sqlite:///foodwise.db   # or postgresql://...
FLASK_ENV=development                # or production

# Optional LLM
AI_PROVIDER=openai                   # openai | gemini | watsonx
AI_API_KEY=sk-...
WATSONX_URL=https://...
WATSONX_PROJECT_ID=...

ADMIN_EMAIL=admin@foodwise.ai
ADMIN_PASSWORD=Admin@123
```

### CLI Commands

| Command | Purpose |
|---------|---------|
| `flask seed-admin` | Create admin account from env vars |
| `flask seed-demo` | Seed 60 days of history + demo provider + NGO |
| `flask db init` | Initialise Alembic migrations folder |
| `flask db migrate` | Generate migration script |
| `flask db upgrade` | Apply migrations |

### Starting the Server

```bash
python run.py                                      # Development
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"  # Production
```

### Demo Accounts

| Role | Email | Password |
|------|-------|---------|
| Food Provider | `demo.canteen@foodwise.ai` | `Demo@1234` |
| NGO | `demo.ngo@foodwise.ai` | `Demo@1234` |
| Admin | `admin@foodwise.ai` | `Admin@123` |

---

## 17. Project Directory Structure

```
foodwise-ai/
├── app.py                      # Entry point, CLI commands
├── run.py                      # Dev server launcher
├── config.py                   # Flask config classes (Dev/Prod)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── pytest.ini                  # Pytest config
├── foodwise.db                 # SQLite database (dev)
│
├── app/
│   ├── __init__.py             # App factory, extension init
│   ├── models/
│   │   ├── user.py             # User model
│   │   ├── organization.py     # Organization model
│   │   ├── food_history.py     # FoodHistory, DemandPrediction, ImpactMetric
│   │   └── surplus.py          # SurplusListing, DonationRequest
│   ├── routes/
│   │   ├── main.py             # / and /about
│   │   ├── auth.py             # /auth/*
│   │   ├── provider.py         # /provider/* (507 lines)
│   │   ├── ngo.py              # /ngo/*
│   │   ├── admin.py            # /admin/*
│   │   ├── api.py              # /api/* (AJAX JSON)
│   │   └── errors.py           # 400/403/404/500
│   ├── services/
│   │   ├── prediction_service.py
│   │   ├── matching_service.py
│   │   ├── ai_assistant.py
│   │   ├── llm_service.py
│   │   └── impact_service.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/               # login, register
│   │   ├── provider/           # dashboard, predict, history, surplus,
│   │   │                       # matches, analytics, assistant, donations
│   │   ├── ngo/                # dashboard, available_food, requests, history
│   │   ├── admin/              # dashboard, users, listings, donations
│   │   └── errors/             # 400, 403, 404, 500
│   └── static/                 # CSS, JS, images
│
├── ml/
│   ├── generate_data.py        # Synthetic dataset generator
│   ├── feature_engineering.py  # Lag features, encoding, leakage prevention
│   ├── train_model.py          # Train + compare 3 models, save best
│   ├── predict.py              # Standalone CLI inference
│   ├── evaluate.py             # Metrics and efficiency score
│   └── models/
│       ├── best_model.pkl
│       ├── model_meta.json
│       └── feature_importance.csv
│
├── data/raw/
│   └── sample_food_data.csv
├── migrations/                 # Alembic migration scripts
└── tests/
    └── test_app.py             # 22 pytest tests
```

---

## 18. Future Roadmap

| Feature | Description |
|---------|-------------|
| 🔌 **IoT Integration** | Real-time weighing scales feed preparation data automatically |
| 📱 **Mobile App** | React Native app for providers and NGO field workers |
| 🚀 **XGBoost + SHAP** | Better accuracy + explainable feature attribution |
| 🗺️ **Map View** | Leaflet.js / Google Maps for visual NGO discovery |
| 📧 **Weekly Reports** | Automated email digest of waste trends and impact |
| 🌐 **Multi-Language** | i18n support for regional languages |

### Revenue Model

| Tier | Target | Features |
|------|--------|---------|
| **Starter (Free)** | NGOs, small canteens | Basic prediction, manual history |
| **Professional** | Restaurants, hotels | Advanced analytics, AI assistant, priority matching |
| **Enterprise** | Universities, chains | Custom ML, REST API, IoT integration |

---

## Changelog

### v1.1.0
- Fix: NGO registration form field collision
- Fix: Renamed NGO org-name field to avoid duplicate conflict
- Added: `gunicorn` to requirements for production deployment
- Updated: Default admin password and `run.py` server launcher

### v1.0.0
- Initial release: ML pipeline, provider/NGO/admin dashboards, AI assistant, NGO matching, impact metrics

---

*FoodWise AI — built during the IBM SkillsBuild ML-AI Internship · Supporting SDG 2 (Zero Hunger) and SDG 12 (Responsible Consumption)*

