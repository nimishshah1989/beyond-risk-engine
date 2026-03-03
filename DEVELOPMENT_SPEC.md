# BEYOND RISK ENGINE v3 — Complete Development Specification

> **For autonomous implementation via Claude Code terminal.**
> Save this file as `DEVELOPMENT_SPEC.md` in your project root.
> Then tell Claude Code: `Read DEVELOPMENT_SPEC.md and follow it phase by phase.`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Existing System (What Exists Today)](#2-existing-system)
3. [New Architecture (What We Are Building)](#3-new-architecture)
4. [Database Schema — Complete Models](#4-database-schema)
5. [Backend Module 1: Financial Life Context (The First Conversation)](#5-financial-life-context)
6. [Backend Module 2: Gamified Assessment Engine](#6-gamified-assessment-engine)
7. [Backend Module 3: Document Parser](#7-document-parser)
8. [Backend Module 4: Transaction Scoring](#8-transaction-scoring)
9. [Backend Module 5: Bayesian Fusion](#9-bayesian-fusion)
10. [Backend Module 6: Market Cycle Overlay & Return Aspiration Check](#10-market-cycle-overlay)
11. [Backend Module 7: Product Matching v2 (Cycle-Aware)](#11-product-matching-v2)
12. [Backend Module 8: Advisor Intelligence](#12-advisor-intelligence)
13. [Frontend Specification](#13-frontend-specification)
14. [API Contract — Every Endpoint](#14-api-contract)
15. [Deployment & Infrastructure](#15-deployment)
16. [Libraries Reference](#16-libraries-reference)
17. [Implementation Order](#17-implementation-order)

---

## 1. Executive Summary

The Beyond Risk Engine v3 is a **complete rebuild** of the behavioral risk profiling system from a questionnaire-only approach to a **dual-path behavioral intelligence platform**. It combines:

- **Foundation — Financial Life Context ("The First Conversation")**: Before any behavioral measurement, capture the investor's complete financial picture — income stability, obligations, liquidity needs at 1/3/5/10 year horizons, existing assets across all classes, real loss experience history, and return aspirations. This structural context determines what "appropriate risk" means regardless of behavioral profile. *Risk isn't volatility — it's the probability of permanent capital loss.*
- **Path A — Gamified Psychometric Assessment**: 19 adaptive trials across 4 behavioral games (~2.5 minutes). Measures risk tolerance, loss aversion, time preference, and herding susceptibility through actual decisions.
- **Path B — Transaction Data Analytics**: Upload CAMS/KFintech CAS PDFs, NSDL/CDSL demat statements, or broker CSV files. System computes 7 behavioral scores from actual trading history.
- **Market Cycle Overlay**: Risk recommendations are *conditional on where we are in the cycle*. Same investor, same profile, but different advice depending on whether valuations are stretched or compressed. The system tracks return-per-unit-of-risk and flags when aspirations are unrealistic given current conditions.
- **Bayesian Fusion**: When both paths available, Normal-Normal conjugate updating produces posterior scores. Transaction data (narrow confidence) naturally dominates questionnaire data (wide confidence). The "say-do gap" becomes a powerful advisor insight.

### Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | Python 3.11+ / FastAPI | Async, Pydantic v2 |
| Database | PostgreSQL (Railway) | SQLAlchemy 2.0 + Alembic |
| Frontend | React 18 + Vite + Tailwind | SPA, react-router-dom v6 |
| PDF Parsing | casparser (MIT) + pdfplumber | CAMS/KFintech/NSDL |
| Market Data | yfinance + mftool | NIFTY drawdowns + scheme NAVs |
| Statistics | numpy + scipy | Bayesian math |
| Deployment | Railway (2 services) | Auto-deploy from GitHub |

### Deployment URLs
- **Backend API**: https://web-production-e8607.up.railway.app
- **Frontend App**: https://beyond-risk-engine-production.up.railway.app
- **Database**: Railway PostgreSQL (connection string in env vars)

---

## 2. Existing System

**CRITICAL: Understand what exists before changing anything. All existing functionality must continue working.**

### 2.1 Current Backend Structure

```
backend/
  app/
    __init__.py
    api/
      __init__.py
      investors.py      # CRUD + list with latest_assessment_id
      products.py       # CRUD + AI document analysis + matching
      questions.py      # CRUD + adaptive assessment flow
    models/
      __init__.py
      database.py       # ALL SQLAlchemy models live here
    services/
      __init__.py
      adaptive.py       # CAT question selection engine
      explain.py        # Advisor insights generator
      instrument_analyzer.py  # AI product doc analysis
      matching.py       # Asymmetric product matching
      scoring.py        # IRT-weighted trait scoring
    core/
      __init__.py
  requirements.txt
  main.py               # FastAPI app entry point
```

### 2.2 Current Database Models (in database.py)

These models exist in production with live data. **Migrations must preserve existing data.**

```python
# ─── ENUMS ───
class QuestionTier(str, enum.Enum):
    ANCHOR = "anchor"
    DIAGNOSTIC = "diagnostic"
    CALIBRATION = "calibration"

class AssessmentStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class FlagType(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

# ─── MODELS ───
class Investor(Base):
    __tablename__ = "investors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    age = Column(String(20))        # Can be "Corp" for corporate
    aum = Column(Float, default=0)
    segment = Column(String(50))    # UHNI, HNI, etc.
    risk_profile = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assessments = relationship("Assessment", back_populates="investor")

class QuestionItem(Base):
    __tablename__ = "question_items"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False)  # A01, D01, C01
    tier = Column(SQLEnum(QuestionTier), nullable=False)
    text = Column(Text, nullable=False)
    rationale = Column(Text)
    difficulty = Column(Float, default=0.5)
    discrimination = Column(Float, default=1.5)
    trait_weights = Column(JSON, nullable=False)    # {"loss_aversion": 0.85, ...}
    options = Column(JSON, nullable=False)           # [{text, scores: {trait: value}}]
    calibrates = Column(String(50))
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey("investors.id"), nullable=False)
    status = Column(SQLEnum(AssessmentStatus), default=AssessmentStatus.IN_PROGRESS)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_questions = Column(Integer, default=0)
    trait_scores = Column(JSON)           # {"loss_aversion": 82, ...}
    confidence_scores = Column(JSON)
    behavioral_flags = Column(JSON)
    drawdown_tolerance = Column(Float)
    liquidity_buffer = Column(String(50))
    stress_prediction = Column(JSON)
    conversation_guide = Column(JSON)
    investor = relationship("Investor", back_populates="assessments")
    responses = relationship("InvestorResponse", back_populates="assessment")

class InvestorResponse(Base):
    __tablename__ = "investor_responses"
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    question_code = Column(String(10), nullable=False)
    option_index = Column(Integer, nullable=False)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    assessment = relationship("Assessment", back_populates="responses")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))
    description = Column(Text)
    risk_vector = Column(JSON, nullable=False)
    min_investment = Column(Float)
    lock_in_years = Column(Float, default=0)
    expected_return_range = Column(String(50))
    risk_label = Column(String(50))
    liquidity = Column(String(100))
    vector_source = Column(String(50), default="manual")
    source_documents = Column(JSON)
    ai_analysis_notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2.3 Current 10-Trait Model

The existing system measures these 10 traits via questionnaire. v3 **KEEPS all 10** but adds transaction-derived scores as parallel measurement.

| Trait ID | v3 Enhancement |
|----------|---------------|
| `loss_aversion` | ADD: Gamified bisection game + PGR/PLR from transactions |
| `horizon_tolerance` | ADD: Time preference game + SIP tenure analysis |
| `liquidity_sensitivity` | ADD: DCE lock-in coefficient + redemption frequency |
| `behavioral_stability` | ADD: SIP discipline index + allocation drift |
| `ambiguity_tolerance` | KEEP questionnaire only |
| `regret_sensitivity` | ADD: Disposition effect from transactions |
| `leverage_comfort` | KEEP questionnaire only |
| `goal_rigidity` | KEEP questionnaire only |
| `emotional_volatility` | ADD: Panic selling score from transactions |
| `decision_confidence` | ADD: Response time analysis from games |

### 2.4 Current Services

**scoring.py** — IRT-weighted trait scoring from questionnaire responses:
```python
TRAIT_IDS = [
    "loss_aversion", "horizon_tolerance", "liquidity_sensitivity",
    "behavioral_stability", "ambiguity_tolerance", "regret_sensitivity",
    "leverage_comfort", "goal_rigidity", "emotional_volatility", "decision_confidence"
]

def compute_trait_scores(responses, questions) -> Dict:
    # Weighted average: score = Σ(option_score × trait_weight × discrimination) / Σ(weight × disc)
    # Returns {"trait_scores": {...}, "confidence_scores": {...}}

def compute_behavioral_flags(traits) -> List[Dict]:
    # Detects: flight risk, inconsistent decisions, leverage-loss contradiction, etc.

def compute_stress_prediction(traits) -> Dict:
    # Predicts behavior during 20%+ correction: FLIGHT RISK, RESILIENT, PARALYSIS, REACTIVE

def compute_liquidity_buffer(traits) -> str:
    # Returns recommended buffer: "1-3 months" to "12+ months"
```

**adaptive.py** — CAT question selection:
```python
def select_next_question(answered_codes, all_questions, current_confidence) -> Optional[dict]:
    # Phase 1: All anchors first
    # Phase 2: Insert calibration every 3 diagnostics
    # Phase 3: Select diagnostic maximizing info gain for most uncertain trait

def should_stop_assessment(num_responses, confidence_scores, max=25, min=12, threshold=72) -> bool:
    # Hard cap 25 questions, soft stop at 12 if avg confidence >= 72%
```

**matching.py** — Asymmetric product matching:
```python
def match_investor_to_products(investor_traits, products) -> List[dict]:
    # Asymmetric: product demands MORE than investor has → 1.5x penalty (dangerous)
    # Investor has MORE than product needs → 0.7x penalty (suboptimal but safe)
    # Returns sorted by fit_score with RECOMMENDED/CONDITIONAL/CAUTION labels
```

### 2.5 Current Frontend

```
frontend/src/
  pages/
    Dashboard.jsx      # Investor list with assessment status
    Questionnaire.jsx  # Adaptive assessment flow
    Results.jsx        # Trait radar, flags, stress prediction, product matching
    Products.jsx       # Product catalog with risk vectors
    QuestionBank.jsx   # Question CRUD
    Upload.jsx         # Product document upload for AI analysis
  components/
    Sidebar.jsx
    UI.jsx
  services/
    api.js             # All API calls
  data/
    traits.js          # Trait definitions
```

### 2.6 Current requirements.txt

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
psycopg2-binary==2.9.9
alembic==1.13.2
python-dotenv==1.0.1
python-multipart==0.0.9
pydantic==2.9.0
pydantic-settings==2.5.2
httpx==0.27.0
anthropic==0.34.0
PyPDF2==3.0.1
openpyxl==3.1.5
```

---

## 3. New Architecture

### 3.1 New Backend Structure

```
backend/
  app/
    api/
      investors.py       # ENHANCED: returns behavioral_profile
      products.py        # ENHANCED: v2 matching uses behavioral_profiles table
      questions.py       # KEEP UNCHANGED
      assessments.py     # KEEP UNCHANGED
      games.py           # NEW: gamified assessment endpoints
      documents.py       # NEW: CAS/demat upload + parsing
      profiles.py        # NEW: unified behavioral profile endpoints
      context.py         # NEW: financial life context CRUD + capacity
      market.py          # NEW: market regime + aspiration check
    models/
      database.py        # ENHANCED: new tables added alongside existing
    services/
      adaptive.py        # KEEP UNCHANGED
      scoring.py         # KEEP + ADD: profile update trigger
      matching.py        # ENHANCE: reads from behavioral_profiles
      explain.py         # ENHANCE: richer insights with say-do gap
      instrument_analyzer.py  # KEEP UNCHANGED
      games_engine.py    # NEW: adaptive staircase logic for 4 games
      cas_parser.py      # NEW: CAMS/KFintech PDF parsing wrapper
      transaction_scorer.py  # NEW: 7 behavioral metrics from transactions
      bayesian_fusion.py # NEW: Normal-Normal conjugate updating
      market_data.py     # NEW: NIFTY drawdown detection via yfinance
      market_cycle.py    # NEW: regime detection, aspiration reality check, cycle-adjusted risk
      financial_context.py # NEW: capacity score, loss experience analysis, constraint logic
  requirements.txt       # UPDATED
  main.py
```

### 3.2 New Frontend Structure

```
frontend/src/
  pages/
    Dashboard.jsx        # ENHANCED: profile source badges, composite score
    FinancialContext.jsx # NEW: the "first conversation" — income, obligations, assets, loss experience, aspirations
    Questionnaire.jsx    # KEEP UNCHANGED
    GameAssessment.jsx   # NEW: gamified 4-game assessment flow
    DocumentUpload.jsx   # NEW: CAS/demat file upload with parsing progress
    BehavioralProfile.jsx# NEW: unified profile + cycle overlay + aspiration reality check
    Results.jsx          # ENHANCED: transaction insights, say-do gap, cycle context
    Products.jsx         # KEEP
    QuestionBank.jsx     # KEEP
    Methodology.jsx      # ENHANCED
  components/
    Sidebar.jsx          # ENHANCED: new nav items
    UI.jsx               # KEEP
    games/               # NEW
      LossAversionGame.jsx
      TimePreferenceGame.jsx
      RiskToleranceGame.jsx
      HerdingGame.jsx
    charts/              # NEW
      BehavioralRadar.jsx
      SayDoGap.jsx
      TransactionTimeline.jsx
  services/
    api.js               # ENHANCED: new API calls added
  data/
    traits.js            # KEEP
```

### 3.3 Updated requirements.txt

Add these to existing:
```
casparser==0.8.1
numpy==1.26.4
scipy==1.12.0
pandas==2.2.1
yfinance==0.2.36
mftool==4.0.0
pdfplumber==0.11.0
python-dateutil==2.9.0
```

### 3.4 System Flow

**Flow 1 — New Investor (No History):**
Create Investor → **Financial Context (The First Conversation)** → Start Gamified Assessment → Play 4 Games (19 trials, ~2.5 min) → Compute Psychometric Scores → Apply Financial Capacity Constraint → Apply Market Cycle Overlay → Generate Profile → Match Products → Advisor Report with Aspiration Reality Check

**Flow 2 — Existing Investor (Has Data):**
Create Investor → **Financial Context** → Upload CAS PDF(s) → Parse Transactions (background) → Compute 7 Transaction Scores → Apply Capacity Constraint → Apply Cycle Overlay → Generate Profile → Match Products → Advisor Report

**Flow 3 — Dual-Path (Best):**
Complete Flow 1 + Flow 2 → Bayesian Fusion → min(fused_risk, financial_capacity) → Cycle-Adjusted Recommendation → Say-Do Gap + Aspiration Reality Check → Comprehensive Advisor Report

---

## 4. Database Schema

**⚠️ CRITICAL: Use Alembic to ADD new tables. NEVER drop existing tables. Preserve all existing data.**

```bash
alembic revision --autogenerate -m "add v3 behavioral tables"
alembic upgrade head
```

### 4.1 New Table: game_sessions

```python
class GameSession(Base):
    __tablename__ = 'game_sessions'

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey('investors.id'), nullable=False)
    status = Column(String(20), default='in_progress')  # in_progress, completed, abandoned
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    device_type = Column(String(20))  # mobile, desktop, tablet
    median_response_time_ms = Column(Integer)

    # Computed scores (populated on completion)
    risk_tolerance_score = Column(Float)    # 0-100
    risk_tolerance_sigma = Column(Float)    # confidence std dev
    loss_aversion_lambda = Column(Float)    # raw λ (typically 1.0-4.0)
    loss_aversion_sigma = Column(Float)
    time_preference_k = Column(Float)       # discount rate k
    time_preference_sigma = Column(Float)
    herding_index = Column(Float)           # 0-1 shift magnitude
    herding_sigma = Column(Float)
    consistency_score = Column(Float)       # 0-100

    investor = relationship('Investor', backref='game_sessions')
    trials = relationship('GameTrial', back_populates='session')
```

### 4.2 New Table: game_trials

```python
class GameTrial(Base):
    __tablename__ = 'game_trials'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('game_sessions.id'), nullable=False)
    game_type = Column(String(30), nullable=False)  # risk_tolerance, loss_aversion, time_preference, herding
    trial_number = Column(Integer, nullable=False)   # 1-based within each game
    stimulus = Column(JSON, nullable=False)
    response = Column(JSON, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship('GameSession', back_populates='trials')
```

**Stimulus examples:**
- risk_tolerance: `{"guaranteed": 50000, "gamble_win": 120000, "gamble_prob": 0.5, "trial": 3}`
- loss_aversion: `{"gain": 20000, "loss": 12500, "probability": 0.5, "trial": 4}`
- time_preference: `{"immediate": 50000, "delayed": 75000, "delay_days": 180, "trial": 2}`
- herding: `{"scenario_id": 1, "phase": "with_signal", "social_signal": "87% chose Fund A"}`

### 4.3 New Table: document_uploads

```python
class DocumentUpload(Base):
    __tablename__ = 'document_uploads'

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey('investors.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # CAMS, KFINTECH, NSDL, CDSL, BROKER_CSV
    file_size_bytes = Column(Integer)
    status = Column(String(20), default='pending')   # pending, parsing, parsed, scoring, scored, failed
    error_message = Column(Text, nullable=True)

    # Parsed metadata
    statement_from = Column(DateTime, nullable=True)
    statement_to = Column(DateTime, nullable=True)
    investor_name_in_doc = Column(String(255))
    investor_pan_in_doc = Column(String(20))
    total_folios = Column(Integer, default=0)
    total_transactions = Column(Integer, default=0)

    uploaded_at = Column(DateTime, default=datetime.utcnow)
    parsed_at = Column(DateTime, nullable=True)
    scored_at = Column(DateTime, nullable=True)

    investor = relationship('Investor', backref='document_uploads')
    transactions = relationship('ParsedTransaction', back_populates='upload')
```

### 4.4 New Table: parsed_transactions

```python
class ParsedTransaction(Base):
    __tablename__ = 'parsed_transactions'

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey('document_uploads.id'), nullable=False)
    investor_id = Column(Integer, ForeignKey('investors.id'), nullable=False)

    # Transaction details
    date = Column(DateTime, nullable=False)
    type = Column(String(30), nullable=False)  # PURCHASE, PURCHASE_SIP, REDEMPTION, SWITCH_IN, SWITCH_OUT, DIVIDEND_PAYOUT, DIVIDEND_REINVEST
    amount = Column(Float, nullable=False)      # INR (positive=buy, negative=sell)
    units = Column(Float)
    nav = Column(Float)
    balance_units = Column(Float)

    # Fund details
    scheme_name = Column(String(500))
    isin = Column(String(20))
    amfi_code = Column(String(20))
    folio_number = Column(String(50))
    amc_name = Column(String(255))
    scheme_category = Column(String(100))  # Large Cap, Mid Cap, Debt, Hybrid

    # Enrichment (populated during scoring)
    nifty_on_date = Column(Float)           # NIFTY 50 close
    nifty_drawdown_pct = Column(Float)      # drawdown from peak (negative = in drawdown)
    scheme_nav_on_date = Column(Float)      # for PGR/PLR

    upload = relationship('DocumentUpload', back_populates='transactions')
```

### 4.5 New Table: transaction_scores

```python
class TransactionScore(Base):
    __tablename__ = 'transaction_scores'

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey('investors.id'), nullable=False)
    upload_ids = Column(JSON)  # list of document_upload ids used

    # 7 Behavioral Scores (0-100, higher = more biased/stronger trait)
    disposition_effect = Column(Float)     # PGR-PLR
    disposition_sigma = Column(Float)
    sip_discipline = Column(Float)         # composite SIP health (INVERTED: 100 = best discipline)
    sip_sigma = Column(Float)
    panic_score = Column(Float)            # redemptions during drawdowns
    panic_sigma = Column(Float)
    diversification = Column(Float)        # HHI-based (INVERTED: 100 = best diversified)
    diversification_sigma = Column(Float)
    herding_score = Column(Float)          # switch-to-trending
    herding_sigma = Column(Float)
    overtrading = Column(Float)            # turnover-based
    overtrading_sigma = Column(Float)
    recency_bias = Column(Float)           # chase recent performers
    recency_sigma = Column(Float)

    n_transactions = Column(Integer)
    date_range_months = Column(Integer)
    computed_at = Column(DateTime, default=datetime.utcnow)

    investor = relationship('Investor', backref='transaction_scores')
```

### 4.6 New Table: behavioral_profiles

**THE unified output — one active row per investor. Product matching and advisor reports read from this.**

```python
class BehavioralProfile(Base):
    __tablename__ = 'behavioral_profiles'

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey('investors.id'), unique=True, nullable=False)

    # Source tracking
    data_sources = Column(String(50))  # PSYCHOMETRIC_ONLY, TRANSACTION_ONLY, QUESTIONNAIRE_ONLY, FUSED
    last_game_session_id = Column(Integer, ForeignKey('game_sessions.id'), nullable=True)
    last_assessment_id = Column(Integer, ForeignKey('assessments.id'), nullable=True)
    last_transaction_score_id = Column(Integer, ForeignKey('transaction_scores.id'), nullable=True)

    # ─── 10 UNIFIED TRAIT SCORES (0-100) — posterior after Bayesian fusion ───
    loss_aversion = Column(Float)
    loss_aversion_ci_lower = Column(Float)
    loss_aversion_ci_upper = Column(Float)
    horizon_tolerance = Column(Float)
    horizon_tolerance_ci_lower = Column(Float)
    horizon_tolerance_ci_upper = Column(Float)
    liquidity_sensitivity = Column(Float)
    behavioral_stability = Column(Float)
    ambiguity_tolerance = Column(Float)
    regret_sensitivity = Column(Float)
    leverage_comfort = Column(Float)
    goal_rigidity = Column(Float)
    emotional_volatility = Column(Float)
    decision_confidence = Column(Float)

    # ─── COMPOSITE ───
    composite_risk_score = Column(Float)
    say_do_gap = Column(Float)            # max divergence stated vs revealed
    say_do_details = Column(JSON)         # per-trait breakdown

    # ─── FLAGS & INSIGHTS ───
    behavioral_flags = Column(JSON)
    stress_prediction = Column(JSON)
    drawdown_tolerance = Column(Float)
    liquidity_buffer = Column(String(50))
    conversation_guide = Column(JSON)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    investor = relationship('Investor', backref=backref('behavioral_profile', uselist=False))
```

### 4.7 New Table: profile_history

```python
class ProfileHistory(Base):
    __tablename__ = 'profile_history'

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey('investors.id'), nullable=False)
    profile_snapshot = Column(JSON, nullable=False)
    trigger = Column(String(50))  # GAME_COMPLETE, DOCUMENT_PARSED, QUESTIONNAIRE_COMPLETE, MANUAL_OVERRIDE
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 5. Financial Life Context (The First Conversation)

**File: `backend/app/services/financial_context.py`**
**File: `backend/app/api/context.py`**

> *"The first conversation isn't about investments at all. It's about understanding the person's financial life completely."* — Yash Jhaveri

This module captures everything a seasoned wealth manager would want to know BEFORE any behavioral measurement. It produces a **Financial Capacity Score** that acts as a hard constraint on risk allocation — no behavioral profile can override structural inability to bear losses.

### 5.1 Why This Comes First

A 28-year-old software engineer earning ₹30L/year with no dependents and ₹5L in obligations has a *structurally different* risk capacity than a 55-year-old business owner with ₹2Cr income but ₹1.5Cr in annual obligations and two children in college — even if both score identically on behavioral games. The financial life context determines the *ceiling* of risk the investor can structurally afford, regardless of their psychological willingness.

### 5.2 New Database Table: investor_financial_context

```python
class InvestorFinancialContext(Base):
    __tablename__ = 'investor_financial_context'

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey('investors.id'), unique=True, nullable=False)

    # ─── INCOME & STABILITY ───
    annual_income = Column(Float)                    # in lakhs
    income_source = Column(String(50))               # SALARIED, BUSINESS, PROFESSIONAL, RETIRED, MIXED
    income_stability = Column(String(20))            # VERY_STABLE (govt/MNC), STABLE (pvt job), MODERATE (business), VOLATILE (freelance/commission)
    income_growth_expectation = Column(String(20))   # GROWING, STABLE, DECLINING
    years_to_retirement = Column(Integer)

    # ─── OBLIGATIONS & LIQUIDITY NEEDS ───
    monthly_fixed_obligations = Column(Float)        # EMIs, rent, insurance premiums, school fees — in lakhs/month
    annual_discretionary_spend = Column(Float)       # lifestyle, travel — in lakhs
    upcoming_obligations_1y = Column(Float)          # known big expenses next 12 months (lakhs)
    upcoming_obligations_3y = Column(Float)          # next 1-3 years
    upcoming_obligations_5y = Column(Float)          # next 3-5 years
    upcoming_obligations_10y = Column(Float)         # next 5-10 years
    obligation_notes = Column(Text)                  # free text: "daughter's wedding 2028, son's education 2030"

    # ─── EXISTING ASSETS (full picture, not just MF) ───
    existing_equity_mf = Column(Float)               # in lakhs
    existing_debt_mf = Column(Float)
    existing_direct_equity = Column(Float)
    existing_fixed_deposits = Column(Float)
    existing_real_estate_value = Column(Float)       # non-primary residence
    existing_gold = Column(Float)
    existing_ppf_epf_nps = Column(Float)
    existing_insurance_corpus = Column(Float)
    existing_other_investments = Column(Float)
    existing_cash_savings = Column(Float)
    primary_residence_value = Column(Float)          # not counted as investable
    total_investable_assets = Column(Float)          # auto-computed
    existing_liabilities = Column(Float)             # total outstanding loans
    net_worth = Column(Float)                        # auto-computed

    # ─── REAL LOSS EXPERIENCE (Yash's key insight) ───
    has_experienced_real_loss = Column(Boolean)       # have they actually lost money?
    worst_loss_amount = Column(Float)                 # in lakhs, actual realized loss
    worst_loss_context = Column(String(100))          # "2008 crash", "bad stock pick", "business failure"
    behavior_during_loss = Column(String(50))         # PANIC_SOLD, HELD_THROUGH, BOUGHT_MORE, FROZE, NOT_APPLICABLE
    loss_recovery_experience = Column(String(50))     # RECOVERED_FULLY, PARTIAL_RECOVERY, PERMANENT_LOSS, NOT_APPLICABLE

    # ─── RETURN ASPIRATIONS ───
    target_return_annual_pct = Column(Float)          # what they WANT (e.g., 15%)
    return_purpose = Column(Text)                     # WHY they want this return
    time_horizon_years = Column(Integer)              # for this aspiration
    is_aspiration_realistic = Column(Boolean)         # computed by market cycle engine
    aspiration_gap_notes = Column(Text)               # "Aspiration of 15% requires 80%+ equity at current valuations..."

    # ─── DECISION MAKING STRUCTURE ───
    decision_maker = Column(String(30))              # SELF, JOINT_SPOUSE, FAMILY_ELDER, ADVISOR_DEPENDENT
    family_influence_level = Column(String(20))       # NONE, LOW, MODERATE, HIGH, DOMINANT
    existing_advisor_relationship = Column(Boolean)
    tax_bracket = Column(String(20))                  # 0%, 5%, 20%, 30%, SURCHARGE

    # ─── COMPUTED ───
    financial_capacity_score = Column(Float)          # 0-100: structural ability to bear risk
    liquidity_runway_months = Column(Float)           # existing_cash / monthly_obligations
    obligation_coverage_ratio = Column(Float)         # annual_income / annual_obligations

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    investor = relationship('Investor', backref=backref('financial_context', uselist=False))
```

### 5.3 Financial Capacity Score Computation

```python
def compute_financial_capacity(ctx) -> float:
    """
    Structural ability to bear investment risk. 0 = cannot afford ANY risk, 100 = maximum capacity.
    This is a HARD CEILING — behavioral willingness cannot exceed structural capacity.
    """
    scores = []

    # 1. Liquidity runway (25% weight)
    runway_months = ctx.existing_cash_savings / max(0.01, ctx.monthly_fixed_obligations) if ctx.monthly_fixed_obligations else 24
    runway_score = min(100, runway_months / 12 * 100)  # 12+ months = 100
    scores.append(('runway', runway_score, 0.25))

    # 2. Obligation coverage (20% weight)
    annual_obligations = ctx.monthly_fixed_obligations * 12 + ctx.annual_discretionary_spend
    coverage = ctx.annual_income / max(0.01, annual_obligations) if annual_obligations else 5
    coverage_score = min(100, max(0, (coverage - 1) * 100))  # ratio 1.0 = 0, 2.0+ = 100
    scores.append(('coverage', coverage_score, 0.20))

    # 3. Time horizon (20% weight)
    horizon = ctx.time_horizon_years or ctx.years_to_retirement or 10
    horizon_score = min(100, horizon * 10)  # 10+ years = 100
    scores.append(('horizon', horizon_score, 0.20))

    # 4. Upcoming obligations pressure (15% weight)
    near_obligations = (ctx.upcoming_obligations_1y or 0) + (ctx.upcoming_obligations_3y or 0)
    obligation_pressure = near_obligations / max(0.01, ctx.total_investable_assets or 1) * 100
    obligation_score = max(0, 100 - obligation_pressure)  # high pressure = low score
    scores.append(('obligations', obligation_score, 0.15))

    # 5. Income stability (10% weight)
    stability_map = {'VERY_STABLE': 90, 'STABLE': 70, 'MODERATE': 50, 'VOLATILE': 25}
    stability_score = stability_map.get(ctx.income_stability, 50)
    scores.append(('stability', stability_score, 0.10))

    # 6. Net worth buffer (10% weight)
    nw = ctx.net_worth or 0
    nw_score = min(100, max(0, nw / 100 * 10))  # ₹100L+ net worth = 100
    scores.append(('networth', nw_score, 0.10))

    capacity = sum(s * w for _, s, w in scores)
    return round(capacity, 1)
```

### 5.4 Real Loss Experience Analysis

```python
def analyze_loss_experience(ctx) -> dict:
    """
    Yash's key insight: actual loss experience tells more than any questionnaire.
    Someone who held through 2008 has DEMONSTRATED resilience.
    Someone who panic-sold has DEMONSTRATED fragility — regardless of what they say now.
    """
    if not ctx.has_experienced_real_loss:
        return {
            'category': 'UNTESTED',
            'insight': 'This investor has never experienced a significant real loss. Their risk tolerance is theoretical and unvalidated. Treat stated preferences with extra caution.',
            'confidence_modifier': 0.6  # reduce confidence in behavioral scores
        }

    experience_map = {
        'PANIC_SOLD': {
            'category': 'DEMONSTRATED_FRAGILITY',
            'insight': f'Investor panic-sold during {ctx.worst_loss_context}. Loss of ₹{ctx.worst_loss_amount}L. This is the strongest predictor of future behavior under stress — overrides questionnaire scores.',
            'confidence_modifier': 1.5,  # this data is MORE reliable than questionnaire
            'override_traits': {'emotional_volatility': 'increase_20', 'loss_aversion': 'increase_15'}
        },
        'HELD_THROUGH': {
            'category': 'DEMONSTRATED_RESILIENCE',
            'insight': f'Investor held through {ctx.worst_loss_context} despite ₹{ctx.worst_loss_amount}L paper loss. Strong evidence of genuine risk tolerance.',
            'confidence_modifier': 1.3,
            'override_traits': {'behavioral_stability': 'increase_15', 'emotional_volatility': 'decrease_15'}
        },
        'BOUGHT_MORE': {
            'category': 'DEMONSTRATED_CONTRARIAN',
            'insight': f'Investor increased allocation during {ctx.worst_loss_context}. Rare contrarian behavior — top 5% of investors.',
            'confidence_modifier': 1.5,
            'override_traits': {'behavioral_stability': 'increase_25', 'loss_aversion': 'decrease_20'}
        },
        'FROZE': {
            'category': 'DEMONSTRATED_PARALYSIS',
            'insight': f'Investor froze during {ctx.worst_loss_context} — neither sold nor bought. May need direct advisor intervention during future stress.',
            'confidence_modifier': 1.2,
            'override_traits': {'decision_confidence': 'decrease_20'}
        }
    }

    return experience_map.get(ctx.behavior_during_loss, {
        'category': 'UNKNOWN',
        'insight': 'Loss experience recorded but behavior pattern unclear.',
        'confidence_modifier': 1.0
    })
```

### 5.5 How Financial Context Constrains Behavioral Profile

The financial capacity score acts as a **ceiling**:

```python
def apply_capacity_constraint(behavioral_profile, financial_context):
    """
    Even if behavioral games say investor is very risk-tolerant (score 85),
    if their financial capacity is 35 (heavy obligations, low runway),
    the EFFECTIVE risk allocation must not exceed capacity.
    """
    capacity = financial_context.financial_capacity_score
    behavioral_risk = behavioral_profile.composite_risk_score

    if behavioral_risk > capacity:
        constrained_risk = capacity
        gap = behavioral_risk - capacity
        flag = {
            'type': 'critical',
            'title': 'Risk Appetite Exceeds Financial Capacity',
            'msg': f'Investor wants risk level {behavioral_risk} but can structurally afford only {capacity}. '
                   f'Near-term obligations of ₹{financial_context.upcoming_obligations_3y}L over 3 years '
                   f'and liquidity runway of only {financial_context.liquidity_runway_months:.0f} months '
                   f'cap the maximum appropriate risk exposure.',
            'action': f'Cap equity allocation at {min(70, capacity)}%. Ensure {max(6, 12 - capacity//10)} months '
                      f'of obligations in liquid instruments before any equity deployment.'
        }
        return constrained_risk, [flag]

    return behavioral_risk, []
```

### 5.6 Frontend: Financial Context Form

**File: `frontend/src/pages/FinancialContext.jsx`**

This is a structured form (NOT a game) — the "first conversation" between advisor and investor. It should feel like a professional consultation, not a quiz.

**Sections in order:**
1. **Income & Stability**: Annual income, source type (dropdown), stability rating, growth expectation, years to retirement
2. **Obligations**: Monthly fixed obligations (with helper examples: EMIs, rent, insurance, school fees), annual discretionary, upcoming big expenses at 1y/3y/5y/10y with free-text notes
3. **Existing Assets**: Full balance sheet — equity MF, debt MF, direct equity, FDs, real estate, gold, PPF/EPF/NPS, insurance, cash. System auto-computes total investable and net worth.
4. **Loss Experience**: "Have you experienced a real investment loss?" If yes: how much, what happened, what did you do (radio: sold/held/bought more/froze), did you recover?
5. **Return Aspirations**: "What annual return are you targeting?" + "Over what time period?" + "What is this return for?" — System will evaluate realism in the Market Cycle module.
6. **Decision Making**: Who makes investment decisions? Family influence level? Existing advisor?

**UX Notes:** Save as you go (no "submit" button anxiety). Show progress. Pre-fill what we know from investor record (age, AUM, segment). Show computed Financial Capacity Score at the end with a clear explanation of what it means.

### 5.7 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/context/{investor_id}` | Get financial context |
| POST | `/api/context/{investor_id}` | Create/update financial context |
| GET | `/api/context/{investor_id}/capacity` | Get computed capacity score + constraints |

---

## 6. Gamified Assessment Engine

**File: `backend/app/services/games_engine.py`**

### 5.1 Game 1: Risk Tolerance (Falk GPS Staircase)

Validated across 76 countries (80,000+ subjects). 5 binary lottery choices bisecting the risk tolerance parameter space.

**Presentation:** "Would you prefer ₹50,000 guaranteed, or a 50% chance of winning ₹X?"

```python
def risk_tolerance_staircase():
    """Falk et al. (2016) GPS staircase. 5 trials."""
    GUARANTEED = 50000
    gamble_range = [60000, 300000]

    def get_first_stimulus():
        mid = (gamble_range[0] + gamble_range[1]) / 2
        return {
            "guaranteed": GUARANTEED,
            "gamble_win": round(mid),
            "gamble_prob": 0.5,
            "trial": 1
        }

    def process_response(trial_num, response, current_range):
        """
        response: {"choice": "guaranteed"} or {"choice": "gamble"}
        Returns: (next_stimulus_or_None, updated_range)
        """
        mid = (current_range[0] + current_range[1]) / 2
        if response["choice"] == "gamble":
            new_range = [mid, current_range[1]]  # more risk tolerant
        else:
            new_range = [current_range[0], mid]  # less risk tolerant

        if trial_num >= 5:
            return None, new_range  # done

        new_mid = (new_range[0] + new_range[1]) / 2
        next_stim = {
            "guaranteed": GUARANTEED,
            "gamble_win": round(new_mid),
            "gamble_prob": 0.5,
            "trial": trial_num + 1
        }
        return next_stim, new_range

    def compute_score(final_range):
        """Convert final gamble range to 0-100 risk tolerance score."""
        mid = (final_range[0] + final_range[1]) / 2
        ce_ratio = GUARANTEED / mid  # certainty equivalent ratio
        # CE ratio near 1.0 = needs barely more than guaranteed = low risk tolerance
        # CE ratio near 0.17 = needs 6x to gamble = extremely risk tolerant wait...
        # Actually: HIGH ce_ratio = LOW risk tolerance (needs small premium)
        # Correction: lower gamble_win needed = MORE risk tolerant
        score = max(0, min(100, round((1 - ce_ratio) * 125 + 15)))
        sigma = 12  # moderate confidence after 5 trials
        return score, sigma
```

### 5.2 Game 2: Loss Aversion (Adaptive Bisection)

Measures λ (loss aversion coefficient) through accept/reject mixed gambles. 6 trials.

**Presentation:** "50/50 gamble: Win ₹20,000 or Lose ₹X. Would you accept?"

```python
def loss_aversion_bisection():
    """Adaptive bisection to find λ. 6 trials."""
    GAIN = 20000
    loss_range = [5000, 40000]

    def get_first_stimulus():
        return {
            "gain": GAIN,
            "loss": round((loss_range[0] + loss_range[1]) / 2),
            "probability": 0.5,
            "trial": 1
        }

    def process_response(trial_num, response, current_range):
        """
        response: {"choice": "accept"} or {"choice": "reject"}
        """
        mid = (current_range[0] + current_range[1]) / 2
        if response["choice"] == "accept":
            new_range = [mid, current_range[1]]  # tolerant, try higher loss
        else:
            new_range = [current_range[0], mid]  # averse, try lower loss

        if trial_num >= 6:
            return None, new_range

        new_mid = (new_range[0] + new_range[1]) / 2
        next_stim = {
            "gain": GAIN,
            "loss": round(new_mid),
            "probability": 0.5,
            "trial": trial_num + 1
        }
        return next_stim, new_range

    def compute_score(final_range):
        """Lambda = gain / switching_point_loss."""
        switching_loss = (final_range[0] + final_range[1]) / 2
        lambda_raw = GAIN / switching_loss if switching_loss > 0 else 2.25

        # Normalize: λ ~1.0 = low loss aversion (score ~20)
        #            λ ~2.25 = average (score ~50)
        #            λ ~4.0+ = extreme (score ~95)
        score = max(0, min(100, round((lambda_raw - 0.5) / 4.0 * 100)))
        sigma = 10  # good confidence after 6 trials
        return lambda_raw, score, sigma
```

### 5.3 Game 3: Time Preference (Koffarnus 5-Trial Adjusting Delay)

Based on Koffarnus & Bickel (2014). Correlates r=0.67 with full 35-trial assessments. 5 trials.

**Presentation:** "Would you take ₹50,000 NOW or ₹1,00,000 in [X time]?"

```python
DELAY_SEQUENCE = [1, 7, 30, 180, 365, 1095, 3650, 9125]  # days
DELAY_LABELS = ["1 day", "1 week", "1 month", "6 months", "1 year", "3 years", "10 years", "25 years"]

def time_preference_adjusting():
    """Koffarnus & Bickel 5-trial adjusting delay. 5 trials."""
    IMMEDIATE = 50000
    DELAYED = 100000
    idx_range = [0, len(DELAY_SEQUENCE) - 1]

    def get_first_stimulus():
        idx = (idx_range[0] + idx_range[1]) // 2
        return {
            "immediate": IMMEDIATE,
            "delayed": DELAYED,
            "delay_days": DELAY_SEQUENCE[idx],
            "delay_label": DELAY_LABELS[idx],
            "trial": 1
        }

    def process_response(trial_num, response, current_range):
        """
        response: {"choice": "immediate"} or {"choice": "delayed"}
        """
        idx = (current_range[0] + current_range[1]) // 2
        if response["choice"] == "immediate":
            new_range = [current_range[0], idx]  # impatient, try shorter
        else:
            new_range = [idx, current_range[1]]  # patient, try longer

        if trial_num >= 5:
            return None, new_range

        new_idx = (new_range[0] + new_range[1]) // 2
        new_idx = max(0, min(len(DELAY_SEQUENCE) - 1, new_idx))
        next_stim = {
            "immediate": IMMEDIATE,
            "delayed": DELAYED,
            "delay_days": DELAY_SEQUENCE[new_idx],
            "delay_label": DELAY_LABELS[new_idx],
            "trial": trial_num + 1
        }
        return next_stim, new_range

    def compute_score(final_range):
        """ED50 = delay at 50% indifference. k = 1/ED50."""
        idx = (final_range[0] + final_range[1]) // 2
        idx = max(0, min(len(DELAY_SEQUENCE) - 1, idx))
        ed50_days = DELAY_SEQUENCE[idx]
        k = 1.0 / ed50_days if ed50_days > 0 else 1.0

        # Normalize: high k = impatient = low patience score
        # k > 0.1 = very impatient (score ~10)
        # k ~ 0.003 = average (score ~50)
        # k < 0.0001 = very patient (score ~90)
        import math
        patience_score = max(0, min(100, round(90 - math.log10(max(k, 1e-6)) * 20)))
        sigma = 14
        return k, patience_score, sigma
```

### 5.4 Game 4: Herding Susceptibility (Social Proof Shift)

Custom design. 3 scenarios presented twice: first without social signal, then with. 3 scenarios × 2 phases = 6 screens.

```python
HERDING_SCENARIOS = [
    {
        "id": 1,
        "description": "Choose between two equity mutual funds for a 5-year investment",
        "option_a": {"name": "Fund Alpha", "return_3y": "14.2%", "risk": "Moderate", "expense": "1.8%"},
        "option_b": {"name": "Fund Beta", "return_3y": "11.8%", "risk": "Low-Moderate", "expense": "0.9%"},
        "social_signal": "87% of investors chose Fund Alpha this month",
        "rational_choice": "B"  # Better risk-adjusted, lower cost
    },
    {
        "id": 2,
        "description": "Markets have fallen 12% this month. What do you do with your equity SIPs?",
        "option_a": {"name": "Continue SIPs as planned"},
        "option_b": {"name": "Pause SIPs and wait for stability"},
        "social_signal": "73% of investors have paused their SIPs",
        "rational_choice": "A"  # Continuing is better long-term
    },
    {
        "id": 3,
        "description": "A new NFO from a trending AMC vs an established fund",
        "option_a": {"name": "New NFO (no track record)", "category": "Thematic - AI & Robotics"},
        "option_b": {"name": "Established fund (8yr track record)", "category": "Flexi Cap"},
        "social_signal": "This NFO collected ₹5,200 Cr in 3 days",
        "rational_choice": "B"  # Track record beats hype
    },
]

def compute_herding_index(phase1_choices, phase2_choices):
    """
    phase1_choices: ["A", "A", "B"] (without social info)
    phase2_choices: ["A", "A", "A"] (with social info)
    """
    shifts_toward_social = 0
    for i in range(len(HERDING_SCENARIOS)):
        if phase1_choices[i] != phase2_choices[i]:
            # Social signal always favors option A in our design
            if phase2_choices[i] == "A":
                shifts_toward_social += 1

    herding_index = shifts_toward_social / len(HERDING_SCENARIOS)  # 0 to 1
    herding_score = round(herding_index * 100)  # 0-100
    sigma = 20  # inherently uncertain with only 3 scenarios
    return herding_index, herding_score, sigma
```

### 5.5 Response Time Capture

**EVERY trial captures `response_time_ms` via `performance.now()` on frontend.**

Rules:
- < 300ms: Flag as random click, exclude from scoring
- < 1500ms: Strong preference (high confidence weight)
- 1500-5000ms: Normal deliberation
- > 5000ms: Genuine uncertainty (widen sigma for this dimension)
- > 12000ms: Distraction (flag session quality)

### 5.6 Session Quality Validation

After all 19 trials, compute quality metrics:
- Median response time (flag if < 800ms = rushing)
- Internal consistency (loss aversion trials should converge monotonically)
- If quality_score < 40: mark session as `low_confidence`, multiply all sigmas by 1.5

---

## 7. Document Parser

**File: `backend/app/services/cas_parser.py`**

### 6.1 Core: casparser Library

```python
import casparser

def parse_cas_pdf(file_path: str, password: str) -> dict:
    """
    Parse CAMS or KFintech CAS PDF.
    Password format: PAN + DOB e.g. 'ABCDE1234F01011990'

    Returns structured data:
    {
        'statement_period': {'from': date, 'to': date},
        'file_type': 'CAMS' or 'KFINTECH',
        'investor_info': {'name': str, 'email': str, 'mobile': str},
        'folios': [
            {
                'folio': str, 'amc': str, 'PAN': str,
                'schemes': [
                    {
                        'scheme': str, 'isin': str, 'amfi': str,
                        'type': str,  # 'EQUITY', 'DEBT', etc
                        'valuation': {'date': date, 'nav': float, 'value': float},
                        'transactions': [
                            {
                                'date': date,
                                'description': str,
                                'amount': float,  # positive = purchase
                                'units': float,
                                'nav': float,
                                'balance': float,
                                'type': str  # PURCHASE, PURCHASE_SIP, REDEMPTION, etc.
                            }
                        ]
                    }
                ]
            }
        ]
    }
    """
    try:
        data = casparser.read_cas_pdf(file_path, password)
        return {'success': True, 'data': data}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

### 6.2 Transaction Type Mapping

| casparser Type | Our Type | Behavioral Use |
|---------------|----------|---------------|
| PURCHASE | LUMPSUM_BUY | Timing reveals chasing vs contrarian |
| PURCHASE_SIP | SIP_BUY | Regularity = discipline. Gaps during drawdowns = panic |
| REDEMPTION | REDEMPTION | **Critical**: timing vs market drawdowns = panic detection |
| SWITCH_IN | SWITCH_IN | With OUT: herding if switching to trending funds |
| SWITCH_OUT | SWITCH_OUT | What they left reveals disposition effect |
| DIVIDEND_PAYOUT | DIVIDEND | Payout vs growth = liquidity preference |
| DIVIDEND_REINVEST | DIVIDEND_REINVEST | Growth mindset indicator |

### 6.3 Fallback Parsers

For NSDL/CDSL demat statements:
```python
import pdfplumber

def parse_demat_pdf(file_path: str) -> dict:
    with pdfplumber.open(file_path) as pdf:
        all_rows = []
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row and any(row):
                        all_rows.append(row)
    return identify_and_parse_demat_rows(all_rows)
```

For broker CSV/Excel:
```python
import pandas as pd

def parse_broker_csv(file_path: str) -> pd.DataFrame:
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
    col_map = identify_columns(df.columns.tolist())
    return df.rename(columns=col_map)
```

### 6.4 Upload API Endpoint

**File: `backend/app/api/documents.py`**

```python
@router.post('/upload')
async def upload_document(
    investor_id: int = Form(...),
    file: UploadFile = File(...),
    password: str = Form(default=''),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    # 1. Save file to temp location
    temp_path = f"/tmp/cas_{upload_id}_{file.filename}"
    with open(temp_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    # 2. Create DocumentUpload record
    upload = DocumentUpload(
        investor_id=investor_id,
        filename=file.filename,
        file_type=detect_file_type(file.filename, content),
        file_size_bytes=len(content),
        status='pending'
    )
    db.add(upload)
    db.commit()

    # 3. Launch background processing
    background_tasks.add_task(
        process_document_pipeline, upload.id, temp_path, password
    )

    return {'upload_id': upload.id, 'status': 'pending'}

@router.get('/status/{upload_id}')
async def get_upload_status(upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(DocumentUpload).filter_by(id=upload_id).first()
    return {
        'upload_id': upload.id,
        'status': upload.status,
        'total_transactions': upload.total_transactions,
        'error': upload.error_message
    }
```

### 6.5 Background Processing Pipeline

```python
def process_document_pipeline(upload_id: int, file_path: str, password: str):
    db = SessionLocal()
    try:
        upload = db.query(DocumentUpload).get(upload_id)

        # Step 1: Parse
        upload.status = 'parsing'
        db.commit()
        result = parse_cas_pdf(file_path, password)
        if not result['success']:
            upload.status = 'failed'
            upload.error_message = result['error']
            db.commit()
            return

        # Step 2: Extract and store transactions
        data = result['data']
        txn_count = 0
        for folio in data.get('folios', []):
            for scheme in folio.get('schemes', []):
                for txn in scheme.get('transactions', []):
                    pt = ParsedTransaction(
                        upload_id=upload_id,
                        investor_id=upload.investor_id,
                        date=txn['date'],
                        type=txn['type'],
                        amount=txn.get('amount', 0),
                        units=txn.get('units'),
                        nav=txn.get('nav'),
                        balance_units=txn.get('balance'),
                        scheme_name=scheme.get('scheme'),
                        isin=scheme.get('isin'),
                        amfi_code=scheme.get('amfi'),
                        folio_number=folio.get('folio'),
                        amc_name=folio.get('amc'),
                        scheme_category=scheme.get('type'),
                    )
                    db.add(pt)
                    txn_count += 1

        upload.status = 'parsed'
        upload.total_transactions = txn_count
        upload.parsed_at = datetime.utcnow()
        db.commit()

        # Step 3: Enrich with NIFTY data
        upload.status = 'scoring'
        db.commit()
        enrich_with_market_data(upload_id, db)

        # Step 4: Compute behavioral scores
        scores = compute_all_transaction_scores(upload.investor_id, db)

        # Step 5: Update behavioral profile
        update_behavioral_profile(upload.investor_id, db)

        upload.status = 'scored'
        upload.scored_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        upload.status = 'failed'
        upload.error_message = str(e)
        db.commit()
    finally:
        db.close()
        # Clean up temp file
        import os
        if os.path.exists(file_path):
            os.remove(file_path)
```

---

## 8. Transaction Scoring

**File: `backend/app/services/transaction_scorer.py`**

All 7 scores are 0-100 with associated sigma (confidence).

### 7.1 Disposition Effect (PGR/PLR)

```python
def compute_disposition_effect(transactions: list) -> tuple:
    """
    Odean (1998) methodology.
    For each REDEMPTION: classify as realized gain or loss.
    For all OTHER held schemes: classify as paper gain or loss.
    PGR = Realized Gains / (Realized Gains + Paper Gains)
    PLR = Realized Losses / (Realized Losses + Paper Losses)
    DE = PGR - PLR  (positive = disposition effect present)
    """
    holdings = {}  # scheme -> [(units, purchase_nav)]
    realized_gains = 0
    realized_losses = 0
    paper_gains = 0
    paper_losses = 0

    for txn in sorted(transactions, key=lambda x: x['date']):
        scheme = txn['scheme_name']

        if txn['type'] in ('PURCHASE', 'PURCHASE_SIP', 'SWITCH_IN'):
            holdings.setdefault(scheme, []).append((abs(txn.get('units', 0)), txn.get('nav', 0)))

        elif txn['type'] in ('REDEMPTION', 'SWITCH_OUT') and txn.get('nav'):
            # FIFO cost basis
            lots = holdings.get(scheme, [])
            if lots:
                avg_cost = sum(u * n for u, n in lots) / sum(u for u, n in lots) if sum(u for u, n in lots) > 0 else 0
                if txn['nav'] > avg_cost:
                    realized_gains += 1
                else:
                    realized_losses += 1

                # Count paper gains/losses on OTHER schemes
                for other, other_lots in holdings.items():
                    if other != scheme and other_lots:
                        other_avg = sum(u * n for u, n in other_lots) / sum(u for u, n in other_lots) if sum(u for u, n in other_lots) > 0 else 0
                        if txn.get('nifty_on_date') and other_avg > 0:
                            # Approximate: use proportional NAV change
                            if txn['nav'] > other_avg:
                                paper_gains += 1
                            else:
                                paper_losses += 1

    pgr = realized_gains / (realized_gains + paper_gains) if (realized_gains + paper_gains) > 0 else 0
    plr = realized_losses / (realized_losses + paper_losses) if (realized_losses + paper_losses) > 0 else 0
    de = pgr - plr

    score = max(0, min(100, round(50 + de * 200)))
    n_events = realized_gains + realized_losses
    sigma = max(5, 30 - n_events * 2)
    return score, sigma
```

### 7.2 SIP Discipline Index

```python
def compute_sip_discipline(transactions: list) -> tuple:
    """
    Composite of 4 factors:
    1. Continuation rate (30%): months_with_SIP / expected_months
    2. Amount consistency (20%): 1 - CV(amounts)
    3. Gap penalty (20%): 1 - (longest_miss / 6)
    4. Downturn discipline (30%): SIP_during_drawdowns / total_drawdown_months
    """
    sips = sorted([t for t in transactions if t['type'] == 'PURCHASE_SIP'], key=lambda x: x['date'])
    if len(sips) < 3:
        return 50, 25  # insufficient data

    import pandas as pd
    import numpy as np

    dates = [pd.Timestamp(s['date']) for s in sips]
    amounts = [abs(s.get('amount', 0)) for s in sips]

    # 1. Continuation rate
    total_months = max(1, (dates[-1] - dates[0]).days / 30)
    continuation = min(1.0, len(sips) / total_months)

    # 2. Amount consistency
    cv = np.std(amounts) / np.mean(amounts) if np.mean(amounts) > 0 else 1
    consistency = max(0, 1 - cv)

    # 3. Gap penalty
    gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
    longest_gap_months = max(gaps) / 30 if gaps else 0
    gap_score = max(0, 1 - longest_gap_months / 6)

    # 4. Downturn discipline
    drawdown_sips = sum(1 for s in sips if s.get('nifty_drawdown_pct', 0) < -5)
    total_drawdown_months = sum(1 for s in sips if s.get('nifty_drawdown_pct') is not None) * 0.3  # rough estimate
    downturn_disc = drawdown_sips / max(1, len(sips) * 0.3)  # normalize

    composite = (continuation * 30 + consistency * 20 + gap_score * 20 + min(1, downturn_disc) * 30)
    sigma = max(5, 20 - len(sips) // 5)
    return round(min(100, composite)), sigma
```

### 7.3 Panic Selling Detection

```python
def compute_panic_score(transactions: list) -> tuple:
    """Correlate redemptions with NIFTY drawdowns (>5% from peak)."""
    redemptions = [t for t in transactions if t['type'] == 'REDEMPTION']
    if not redemptions:
        return 0, 25

    panic_events = sum(1 for r in redemptions if r.get('nifty_drawdown_pct', 0) < -5)
    panic_ratio = panic_events / len(redemptions)

    score = round(panic_ratio * 100)
    sigma = max(5, 25 - len(redemptions) * 3)
    return score, sigma
```

### 7.4 Diversification (HHI)

```python
def compute_diversification(transactions: list) -> tuple:
    """HHI at scheme level. Lower HHI = better diversified = higher score."""
    holdings = {}
    for t in sorted(transactions, key=lambda x: x['date']):
        scheme = t['scheme_name']
        units = t.get('units', 0) or 0
        nav = t.get('nav', 0) or 0
        if t['type'] in ('PURCHASE', 'PURCHASE_SIP', 'SWITCH_IN'):
            holdings[scheme] = holdings.get(scheme, 0) + abs(units) * nav
        elif t['type'] in ('REDEMPTION', 'SWITCH_OUT'):
            holdings[scheme] = max(0, holdings.get(scheme, 0) - abs(units) * nav)

    holdings = {k: v for k, v in holdings.items() if v > 0}
    if not holdings:
        return 50, 25

    total = sum(holdings.values())
    weights = [v / total for v in holdings.values()]
    hhi = sum(w ** 2 for w in weights)

    score = max(0, min(100, round((1 - hhi) * 104)))
    sigma = 10
    return score, sigma
```

### 7.5 Herding (Switch-to-Trending)

```python
def compute_herding_from_switches(transactions: list) -> tuple:
    switches = [t for t in transactions if t['type'] == 'SWITCH_IN']
    if len(switches) < 2:
        return 50, 25

    chase_count = sum(1 for s in switches if is_top_performer(s.get('scheme_category', ''), s['date']))
    chase_ratio = chase_count / len(switches)

    score = round(chase_ratio * 100)
    sigma = max(8, 22 - len(switches) * 2)
    return score, sigma
```

### 7.6 Overtrading

```python
def compute_overtrading(transactions: list) -> tuple:
    """Annualized turnover = min(buys, sells) / avg_portfolio."""
    import pandas as pd
    buys = sum(abs(t.get('amount', 0)) for t in transactions if t['type'] in ('PURCHASE', 'SWITCH_IN'))
    sells = sum(abs(t.get('amount', 0)) for t in transactions if t['type'] in ('REDEMPTION', 'SWITCH_OUT'))

    dates = [t['date'] for t in transactions]
    if not dates:
        return 50, 25

    years = max(0.5, (max(dates) - min(dates)).days / 365)
    annual_turnover_pct = min(buys, sells) / max(1, (buys + sells) / 2) * 100 / years

    score = max(0, min(100, round(annual_turnover_pct / 2)))
    sigma = 12
    return score, sigma
```

### 7.7 Recency Bias

```python
def compute_recency_bias(transactions: list) -> tuple:
    """Fraction of non-SIP purchases into top-quartile recent performers."""
    lumpsum_buys = [t for t in transactions if t['type'] == 'PURCHASE']
    if len(lumpsum_buys) < 2:
        return 50, 25

    recency_count = sum(1 for b in lumpsum_buys if is_top_performer(b.get('scheme_category', ''), b['date']))
    ratio = recency_count / len(lumpsum_buys)

    score = round(ratio * 100)
    sigma = max(8, 22 - len(lumpsum_buys) * 2)
    return score, sigma
```

### 7.8 Market Data Module

**File: `backend/app/services/market_data.py`**

```python
import yfinance as yf
import pandas as pd
from datetime import datetime

_nifty_cache = None

def get_nifty_history(start='2018-01-01') -> pd.DataFrame:
    global _nifty_cache
    if _nifty_cache is not None:
        return _nifty_cache

    nifty = yf.download('^NSEI', start=start, end=datetime.now().strftime('%Y-%m-%d'))
    nifty['Peak'] = nifty['Close'].cummax()
    nifty['Drawdown'] = (nifty['Close'] - nifty['Peak']) / nifty['Peak'] * 100
    _nifty_cache = nifty
    return nifty

def get_drawdown_on_date(date, nifty_data=None) -> float:
    if nifty_data is None:
        nifty_data = get_nifty_history()
    closest = nifty_data.index.asof(pd.Timestamp(date))
    if pd.isna(closest):
        return None
    return float(nifty_data.loc[closest, 'Drawdown'])

def enrich_with_market_data(upload_id: int, db):
    """Add nifty_on_date and nifty_drawdown_pct to all parsed transactions."""
    nifty = get_nifty_history()
    txns = db.query(ParsedTransaction).filter_by(upload_id=upload_id).all()
    for txn in txns:
        dd = get_drawdown_on_date(txn.date, nifty)
        txn.nifty_drawdown_pct = dd
        closest = nifty.index.asof(pd.Timestamp(txn.date))
        if not pd.isna(closest):
            txn.nifty_on_date = float(nifty.loc[closest, 'Close'])
    db.commit()
```

> **NOTE:** Cache NIFTY data. Don't call yfinance on every upload. Refresh weekly.

---

## 9. Bayesian Fusion

**File: `backend/app/services/bayesian_fusion.py`**

### 8.1 Core Formula

Normal-Normal conjugate updating for each dimension independently:

```python
import numpy as np
from typing import Dict, Tuple, Optional

def bayesian_update(mu_prior: float, sigma_prior: float,
                    mu_observed: float, sigma_observed: float) -> Tuple[float, float]:
    """Normal-Normal conjugate update."""
    prec_prior = 1.0 / (sigma_prior ** 2)
    prec_obs = 1.0 / (sigma_observed ** 2)
    prec_post = prec_prior + prec_obs
    mu_post = (prec_prior * mu_prior + prec_obs * mu_observed) / prec_post
    sigma_post = np.sqrt(1.0 / prec_post)
    return round(float(mu_post), 2), round(float(sigma_post), 2)
```

### 8.2 Profile Fusion

```python
# Mapping: which transaction score informs which trait
TRAIT_TO_TRANSACTION = {
    'loss_aversion': 'disposition_effect',
    'behavioral_stability': 'sip_discipline',
    'emotional_volatility': 'panic_score',
    'regret_sensitivity': 'disposition_effect',
    'horizon_tolerance': 'sip_discipline',
    'liquidity_sensitivity': 'overtrading',
    'decision_confidence': None,    # no transaction equivalent
    'ambiguity_tolerance': None,
    'leverage_comfort': None,
    'goal_rigidity': None,
}

def fuse_profiles(
    psychometric: Optional[Dict],   # {trait: (score, sigma)}
    transaction: Optional[Dict],     # {metric: (score, sigma)}
) -> Dict:
    result = {}
    max_gap = 0
    gap_details = {}

    for trait, txn_key in TRAIT_TO_TRANSACTION.items():
        psych = psychometric.get(trait) if psychometric else None
        txn = transaction.get(txn_key) if (transaction and txn_key) else None

        if psych and txn:
            mu, sigma = bayesian_update(psych[0], psych[1], txn[0], txn[1])
            source = 'FUSED'
            gap = abs(psych[0] - txn[0])
            gap_details[trait] = {'stated': psych[0], 'revealed': txn[0], 'gap': round(gap, 1)}
            max_gap = max(max_gap, gap)
        elif psych:
            mu, sigma = psych
            source = 'PSYCHOMETRIC_ONLY'
        elif txn:
            mu, sigma = txn
            source = 'TRANSACTION_ONLY'
        else:
            mu, sigma = 50, 25
            source = 'DEFAULT'

        ci_lower = max(0, round(mu - 1.96 * sigma, 1))
        ci_upper = min(100, round(mu + 1.96 * sigma, 1))
        result[trait] = {
            'score': round(mu),
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'source': source
        }

    result['_say_do_gap'] = round(max_gap, 1)
    result['_say_do_details'] = gap_details
    result['_data_sources'] = determine_overall_source(psychometric, transaction)
    return result
```

### 8.3 Say-Do Gap Alerts

When `|stated - revealed| > 20` on any dimension, flag for advisor:

> "This investor scored 72 on risk tolerance (assessment) but their actual trading shows panic selling during drawdowns (transaction score: 38). Calibrated score: 48. Recommend conservative allocation despite stated preference."

---

## 10. Market Cycle Overlay & Return Aspiration Check

**File: `backend/app/services/market_cycle.py`**

> *"The distinction I'd draw: in late 2006, 15% annual returns meant buying into razor-thin risk premiums. The same aspiration in March 2009 was entirely reasonable because assets were priced to deliver those returns with much less downside."* — Yash Jhaveri

This module makes risk recommendations **conditional on current market conditions**. It answers: "Given where we are in the cycle, what return is the market offering per unit of risk taken, and does this investor's aspiration make sense?"

### 10.1 Market Regime Detection

```python
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta

def compute_market_regime() -> dict:
    """
    Assess current market regime using valuation + momentum + volatility signals.
    Returns a regime classification and return-per-risk estimate.
    """
    nifty = yf.download('^NSEI', period='5y')

    # 1. Valuation signal: NIFTY PE ratio (use trailing data)
    # Proxy: current price relative to 5-year average
    current = float(nifty['Close'].iloc[-1])
    avg_5y = float(nifty['Close'].mean())
    valuation_ratio = current / avg_5y  # >1.2 = expensive, <0.8 = cheap

    # 2. Momentum: 200-day moving average position
    ma_200 = float(nifty['Close'].rolling(200).mean().iloc[-1])
    momentum = 'BULLISH' if current > ma_200 * 1.05 else ('BEARISH' if current < ma_200 * 0.95 else 'NEUTRAL')

    # 3. Volatility: 30-day realized volatility
    returns = nifty['Close'].pct_change().dropna()
    vol_30d = float(returns.tail(30).std() * np.sqrt(252) * 100)  # annualized %
    vol_regime = 'LOW' if vol_30d < 14 else ('HIGH' if vol_30d > 22 else 'NORMAL')

    # 4. Drawdown from peak
    peak = float(nifty['Close'].cummax().iloc[-1])
    drawdown_pct = (current - peak) / peak * 100

    # Classify regime
    if valuation_ratio > 1.3 and momentum == 'BULLISH' and vol_regime == 'LOW':
        regime = 'LATE_CYCLE_EUPHORIA'
        risk_premium = 'COMPRESSED'
        expected_forward_return = '6-10%'
        risk_per_return = 'POOR'  # high risk per unit of expected return
    elif valuation_ratio < 0.8 and drawdown_pct < -15:
        regime = 'CRISIS_OPPORTUNITY'
        risk_premium = 'EXPANDED'
        expected_forward_return = '14-20%'
        risk_per_return = 'EXCELLENT'
    elif valuation_ratio > 1.15:
        regime = 'ELEVATED_VALUATIONS'
        risk_premium = 'THIN'
        expected_forward_return = '8-12%'
        risk_per_return = 'MODERATE_POOR'
    elif valuation_ratio < 0.9:
        regime = 'ATTRACTIVE_VALUATIONS'
        risk_premium = 'HEALTHY'
        expected_forward_return = '12-16%'
        risk_per_return = 'GOOD'
    else:
        regime = 'MID_CYCLE'
        risk_premium = 'NORMAL'
        expected_forward_return = '10-14%'
        risk_per_return = 'MODERATE'

    return {
        'regime': regime,
        'risk_premium': risk_premium,
        'expected_forward_return': expected_forward_return,
        'risk_per_return': risk_per_return,
        'valuation_ratio': round(valuation_ratio, 2),
        'momentum': momentum,
        'volatility_regime': vol_regime,
        'vol_30d': round(vol_30d, 1),
        'drawdown_from_peak': round(drawdown_pct, 1),
        'nifty_current': round(current),
        'computed_at': datetime.utcnow().isoformat()
    }
```

### 10.2 Return Aspiration Reality Check

```python
def check_return_aspiration(aspiration_pct: float, time_horizon: int, market_regime: dict) -> dict:
    """
    Is the investor's return aspiration realistic given current market conditions?

    Example: Investor wants 15% over 5 years.
    In LATE_CYCLE_EUPHORIA: "Unrealistic without extreme concentration risk"
    In CRISIS_OPPORTUNITY: "Achievable with moderate equity allocation"
    """
    regime = market_regime['regime']
    forward_range = market_regime['expected_forward_return']  # e.g., "8-12%"
    low, high = [float(x.strip('%')) for x in forward_range.split('-')]
    midpoint = (low + high) / 2

    gap = aspiration_pct - midpoint

    if gap <= 0:
        realism = 'ACHIEVABLE'
        equity_needed = max(20, min(80, aspiration_pct / midpoint * 60))
        message = (
            f'Target of {aspiration_pct}% is within the range markets are currently priced to deliver '
            f'({forward_range} forward estimate). Achievable with ~{equity_needed:.0f}% equity allocation.'
        )
    elif gap <= 4:
        realism = 'STRETCH'
        equity_needed = min(90, aspiration_pct / midpoint * 70)
        message = (
            f'Target of {aspiration_pct}% exceeds current forward estimates ({forward_range}) by {gap:.0f}pp. '
            f'Requires concentrated equity (~{equity_needed:.0f}%+) with higher drawdown risk. '
            f'The return per unit of risk is {market_regime["risk_per_return"]}.'
        )
    else:
        realism = 'UNREALISTIC'
        message = (
            f'Target of {aspiration_pct}% significantly exceeds what markets are priced to deliver '
            f'({forward_range}). Achieving this would require either leverage, extreme concentration, '
            f'or timing — none of which are reliably repeatable. '
            f'Current risk premiums are {market_regime["risk_premium"]}. '
            f'Recommend resetting expectations to {midpoint:.0f}-{high:.0f}% or extending the time horizon.'
        )

    # Time horizon adjustment
    if time_horizon >= 10 and realism == 'STRETCH':
        realism = 'ACHIEVABLE_LONG_TERM'
        message += f' Over {time_horizon} years, mean reversion makes this more achievable.'
    elif time_horizon <= 3 and realism != 'ACHIEVABLE':
        realism = 'HIGH_RISK'
        message += f' Critical: {time_horizon}-year horizon leaves no room for recovery from drawdowns.'

    return {
        'aspiration': aspiration_pct,
        'market_forward_estimate': forward_range,
        'gap': round(gap, 1),
        'realism': realism,
        'equity_allocation_needed': round(equity_needed) if gap <= 4 else None,
        'message': message,
        'regime': regime
    }
```

### 10.3 Cycle-Adjusted Risk Recommendation

```python
def adjust_risk_for_cycle(behavioral_risk_score: float, financial_capacity: float, market_regime: dict) -> dict:
    """
    The final risk recommendation considers ALL three inputs:
    1. Behavioral willingness (from games/questionnaire/transactions)
    2. Financial capacity (structural ability)
    3. Market conditions (is risk being rewarded right now?)

    In LATE_CYCLE_EUPHORIA: reduce equity allocation even for risk-tolerant investors
    In CRISIS_OPPORTUNITY: this is when risk-tolerant investors should deploy
    """
    regime = market_regime['regime']
    base_risk = min(behavioral_risk_score, financial_capacity)  # capacity is ceiling

    # Cycle adjustment factors
    cycle_adjustments = {
        'CRISIS_OPPORTUNITY': 1.15,       # nudge up — risk is being well-compensated
        'ATTRACTIVE_VALUATIONS': 1.08,
        'MID_CYCLE': 1.00,                # no adjustment
        'ELEVATED_VALUATIONS': 0.90,      # pull back — risk premium thin
        'LATE_CYCLE_EUPHORIA': 0.80,      # significant pullback — risk premium compressed
    }

    adjustment = cycle_adjustments.get(regime, 1.0)
    adjusted_risk = round(min(100, max(0, base_risk * adjustment)))

    # Generate advisor note
    if adjustment < 1.0:
        cycle_note = (
            f'CYCLE ALERT: Market regime is {regime}. Risk premiums are {market_regime["risk_premium"]}. '
            f'Reducing recommended risk from {base_risk} to {adjusted_risk} ({(1-adjustment)*100:.0f}% reduction). '
            f'Forward returns estimated at only {market_regime["expected_forward_return"]} — '
            f'the return per unit of risk is {market_regime["risk_per_return"]}.'
        )
    elif adjustment > 1.0:
        cycle_note = (
            f'CYCLE OPPORTUNITY: Market regime is {regime}. Risk premiums are {market_regime["risk_premium"]}. '
            f'This is an environment where risk is well-compensated. Forward returns estimated at '
            f'{market_regime["expected_forward_return"]}. Consider deploying above baseline allocation for suitable investors.'
        )
    else:
        cycle_note = f'Market regime is {regime}. No cycle adjustment needed.'

    return {
        'behavioral_risk': behavioral_risk_score,
        'financial_capacity': financial_capacity,
        'market_regime': regime,
        'cycle_adjustment_factor': adjustment,
        'adjusted_risk_score': adjusted_risk,
        'suggested_equity_pct': min(85, max(10, adjusted_risk * 0.85)),
        'cycle_note': cycle_note
    }
```

### 10.4 Database: Market Regime Cache

```python
class MarketRegimeCache(Base):
    __tablename__ = 'market_regime_cache'

    id = Column(Integer, primary_key=True, index=True)
    regime = Column(String(30))
    risk_premium = Column(String(20))
    expected_forward_return = Column(String(20))
    risk_per_return = Column(String(20))
    valuation_ratio = Column(Float)
    momentum = Column(String(20))
    vol_30d = Column(Float)
    drawdown_from_peak = Column(Float)
    nifty_current = Column(Float)
    computed_at = Column(DateTime, default=datetime.utcnow)
```

> **NOTE:** Compute market regime daily or weekly via background task. Cache in database. Don't compute on every request. The regime changes slowly — weekly refresh is sufficient.

### 10.5 Frontend: Aspiration Reality Check Widget

Show on the BehavioralProfile page when return aspiration is captured:
- Visual gauge: aspiration arrow vs market forward estimate range
- Color-coded: green (achievable), amber (stretch), red (unrealistic)
- Clear text: "Markets are currently priced to deliver 8-12% annually. Your target of 15% would require..."
- Cycle indicator: current regime badge with one-line explanation

### 10.6 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/market/regime` | Current market regime (cached) |
| POST | `/api/market/aspiration-check` | `{aspiration_pct, time_horizon}` → realism analysis |
| GET | `/api/profiles/{investor_id}/cycle-adjusted` | Full profile with cycle-adjusted risk |

---

## 11. Product Matching v2 (Cycle-Aware)

**File: `backend/app/services/matching.py` (ENHANCED)**

Keep existing asymmetric matching logic. Changes:
1. Input reads from `behavioral_profiles` table instead of raw `assessment.trait_scores`
2. New field: `match_confidence` = average (100 - CI_width) across relevant traits
3. Wide CI + product demands > investor score = "REVIEW WITH ADVISOR" instead of simple CAUTION

---

## 12. Advisor Intelligence

**File: `backend/app/services/explain.py` (ENHANCED)**

New insight types based on `data_sources`:
- **FUSED profiles**: "Your assessment suggests X, but trading history shows Y. Calibrated to Z."
- **Transaction evidence**: "Investor maintained all SIPs through March 2020 crash. Top 5% discipline."
- **Disposition warnings**: "Redeemed 6 of 8 positions at gains, holds 3 at 15-25% loss."

---

## 13. Frontend Specification

### 11.1 Updated Sidebar

| Nav Item | Route | Status |
|----------|-------|--------|
| Central | `/` | ENHANCED |
| Financial Profile | `/context/:id` | **NEW: The First Conversation** |
| Assess (Games) | `/assess/games/:id` | **NEW** |
| Assess (Questions) | `/assess/questions/:id` | KEEP |
| Upload Documents | `/upload/:id` | **NEW** |
| Behavioral Profile | `/profile/:id` | **NEW** |
| Results | `/results/:id` | ENHANCED |
| Products | `/products` | KEEP |
| Question Bank | `/questions` | KEEP |

### 11.2 NEW: GameAssessment.jsx

**The 4-game assessment flow (~2.5 minutes).**

Flow: Welcome → Game 1 (Risk, 5 trials) → Transition → Game 2 (Loss, 6 trials) → Transition → Game 3 (Time, 5 trials) → Transition → Game 4 (Herding, 3×2 screens) → Processing → Summary

Each game component:
```jsx
function LossAversionGame({ sessionId, onComplete }) {
  const [trial, setTrial] = useState(null);
  const [startTime, setStartTime] = useState(null);

  const handleResponse = async (choice) => {
    const rt = performance.now() - startTime;
    const res = await fetch('/api/games/trial', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        session_id: sessionId,
        game_type: 'loss_aversion',
        trial_number: trial.trial,
        stimulus: trial,
        response: { choice },
        response_time_ms: Math.round(rt)
      })
    });
    const data = await res.json();
    if (data.next_stimulus) {
      setTrial(data.next_stimulus);
      setStartTime(performance.now());
    } else {
      onComplete(data.scores);
    }
  };

  // Render: coin with gain/loss sides, Accept/Reject buttons
}
```

### 11.3 NEW: DocumentUpload.jsx

Features:
- Drag-and-drop accepting .pdf, .csv, .xlsx
- Password input for CAS PDFs (helper: "PAN + DOB as DDMMYYYY")
- Auto-detect file type or manual selection
- Polling status: pending → parsing → parsed → scoring → scored
- On completion: parsed summary (X folios, Y transactions, date range)
- Multiple file support
- Link to Behavioral Profile when done

### 11.4 NEW: BehavioralProfile.jsx

The unified profile page:
- Header: Investor name, segment, data source badges
- 10-trait radar with confidence bands
- Say-Do Gap bars (when FUSED)
- Behavioral flags (critical/warning/info)
- Stress prediction
- Product matches with confidence
- Conversation guide
- Transaction behavior timeline (if available)

### 11.5 ENHANCED: Dashboard.jsx

Add columns:
- Profile Source badge (PSYCHOMETRIC / TRANSACTION / FUSED / NONE)
- Composite Score from behavioral_profiles
- Actions: "Play Games" / "Upload Docs" / "View Profile" buttons

---

## 14. API Contract

### 12.1 Existing (KEEP UNCHANGED)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/investors` | List investors |
| POST | `/api/investors` | Create investor |
| GET | `/api/investors/{id}` | Get investor |
| GET/POST/PUT/DELETE | `/api/questions/...` | Question CRUD |
| POST | `/api/assessments/start` | Start questionnaire |
| POST | `/api/assessments/respond` | Submit response |
| GET | `/api/assessments/{id}` | Get assessment |
| GET | `/api/assessments/{id}/full-report` | Full report |
| GET | `/api/products/` | List products |
| POST | `/api/products/match` | Match products |
| POST | `/api/products/analyze-document` | AI analyze product doc |

### 12.2 New Endpoints

| Method | Path | Body / Params | Returns |
|--------|------|--------------|---------|
| POST | `/api/games/start` | `{investor_id}` | `{session_id, first_trials: {risk, loss, time, herding}}` |
| POST | `/api/games/trial` | `{session_id, game_type, trial_number, stimulus, response, response_time_ms}` | `{next_stimulus}` or `{complete: true, scores}` |
| POST | `/api/games/complete` | `{session_id}` | Computed scores + profile update |
| GET | `/api/games/session/{id}` | — | Session details + all trials |
| POST | `/api/documents/upload` | Multipart: file + investor_id + password | `{upload_id, status}` |
| GET | `/api/documents/status/{upload_id}` | — | `{status, total_transactions, error}` |
| GET | `/api/documents/investor/{investor_id}` | — | List all uploads |
| GET | `/api/profiles/{investor_id}` | — | Unified behavioral profile |
| GET | `/api/profiles/{investor_id}/history` | — | Profile change history |
| POST | `/api/profiles/{investor_id}/recalculate` | — | Force recalculation |

### 12.3 Enhanced Endpoints

| Method | Path | Change |
|--------|------|--------|
| GET | `/api/investors` | ADD: `behavioral_profile_source`, `composite_score` |
| POST | `/api/products/match` | Accept `investor_id`, read from `behavioral_profiles` |

---

## 15. Deployment

### Railway Config

- **Backend**: Root `/backend`, Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Frontend**: Root `/frontend`, Build: `npm run build`, Start: `node server.js`
- **Database**: Railway PostgreSQL, `DATABASE_URL` in env vars

### Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| DATABASE_URL | Backend | PostgreSQL (set by Railway) |
| ANTHROPIC_API_KEY | Backend | For AI product analysis |
| VITE_API_URL | Frontend | Backend URL |

---

## 16. Libraries Reference

| Library | Version | Purpose |
|---------|---------|---------|
| casparser | 0.8.1 | CAMS/KFintech CAS PDF parsing |
| numpy | 1.26.4 | Bayesian math |
| scipy | 1.12.0 | Statistical distributions |
| pandas | 2.2.1 | Transaction data manipulation |
| yfinance | 0.2.36 | NIFTY 50 historical data |
| mftool | 4.0.0 | AMFI NAV data |
| pdfplumber | 0.11.0 | Fallback PDF parser |
| python-dateutil | 2.9.0 | Date parsing |

---

## 17. Implementation Order

### Phase 1: Foundation (Do First)
1. Add new Python dependencies to `requirements.txt`
2. Add ALL new SQLAlchemy models to `database.py` (including `investor_financial_context`, `market_regime_cache`)
3. Create Alembic migration, run locally + Railway
4. Create `services/market_data.py` (NIFTY data)
5. Create `services/bayesian_fusion.py` (the math)
6. Test: import and run `bayesian_update()` with sample values

### Phase 1.5: Financial Life Context ("The First Conversation")
1. Create `services/financial_context.py` — capacity score computation, loss experience analysis, capacity constraint
2. Create `api/context.py` — CRUD + computed capacity endpoint
3. Create `frontend/src/pages/FinancialContext.jsx` — structured form with 6 sections: income & stability, obligations & liquidity needs (1y/3y/5y/10y), existing assets (full balance sheet), real loss experience, return aspirations, decision-making structure
4. Add route + sidebar: "Financial Profile" as the **FIRST** step before games or uploads
5. Test: create context, verify capacity score, verify constraint works
6. Wire capacity constraint: `min(behavioral_risk, financial_capacity)` = effective risk ceiling

### Phase 2: Gamified Assessment (Path A)
1. Create `services/games_engine.py` with all 4 game algorithms
2. Create `api/games.py` with start/trial/complete endpoints
3. Test: start session, submit 19 trials via API, verify scores
4. Create `frontend/src/components/games/` (4 components)
5. Create `frontend/src/pages/GameAssessment.jsx`
6. Add route + sidebar nav
7. E2E test: play games in browser, verify profile created

### Phase 3: Document Upload (Path B)
1. Create `services/cas_parser.py` (casparser wrapper)
2. Create `services/transaction_scorer.py` (7 scores)
3. Create `api/documents.py` (upload + status)
4. Test: upload sample CAS PDF, verify transactions parsed and scored
5. Create `frontend/src/pages/DocumentUpload.jsx`
6. E2E test: upload → watch progress → verify scores

### Phase 4: Fusion, Market Cycle & Profile
1. Wire `bayesian_fusion.py` into profile update pipeline
2. Trigger: game_complete → update_profile, document_scored → update_profile
3. Create `services/market_cycle.py` — regime detection, aspiration reality check, cycle-adjusted risk
4. Create `api/profiles.py` (includes cycle-adjusted endpoint)
5. Create `frontend/src/pages/BehavioralProfile.jsx` — with aspiration reality widget, cycle indicator, say-do gap
6. Enhance `Dashboard.jsx` with profile source, composite score, financial context status
7. E2E test: investor with financial context + games + documents → verify full pipeline: fused + constrained + cycle-adjusted profile

### Phase 5: Polish & Advisor Experience
1. Enhance `Results.jsx` with transaction insights + say-do gap + cycle context + aspiration check
2. Update `matching.py` to use `behavioral_profiles` AND `financial_capacity` AND `market_regime`
3. Enhance advisor conversation guide: include cycle context ("Given current valuations..."), loss experience insights, aspiration gap warnings
4. Profile history tracking
5. Error handling, loading states
6. Deploy to Railway

---

**⚠️ CRITICAL RULES:**
1. Keep existing questionnaire flow 100% working. It's a parallel path, not replaced.
2. Use Alembic for ALL schema changes. Never drop existing tables.
3. Every investor can have: questionnaire only, games only, documents only, or any combination.
4. All game trials must capture `response_time_ms` via `performance.now()`.
5. Background processing for document parsing — never block the API response.
6. Cache NIFTY data and market regime — don't call yfinance on every request. Weekly refresh.
7. Financial capacity is a HARD CEILING on risk. Behavioral willingness cannot exceed structural ability.
8. Loss experience from financial context OVERRIDES questionnaire data — someone who panic-sold in 2008 has demonstrated behavior that is more reliable than any game score.
9. Market cycle overlay adjusts recommendations but does NOT change the investor's profile scores — it adjusts what we DO with those scores.