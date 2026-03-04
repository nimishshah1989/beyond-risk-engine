from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text, Boolean,
    DateTime, JSON, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from datetime import datetime
import enum
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./beyond_risk.db")

# Railway gives postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
    age = Column(String(20))  # Can be "Corp" for corporate
    aum = Column(Float, default=0)
    segment = Column(String(50))  # UHNI, HNI, etc.
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
    rationale = Column(Text)  # Why this question exists
    difficulty = Column(Float, default=0.5)  # IRT difficulty parameter
    discrimination = Column(Float, default=1.5)  # IRT discrimination parameter
    trait_weights = Column(JSON, nullable=False)  # {"loss_aversion": 0.85, ...}
    options = Column(JSON, nullable=False)  # [{text, scores: {trait: value}}]
    calibrates = Column(String(50))  # For calibration items: which trait it cross-checks
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

    # Final computed results (populated on completion)
    trait_scores = Column(JSON)  # {"loss_aversion": 82, ...}
    confidence_scores = Column(JSON)  # {"loss_aversion": 89, ...}
    behavioral_flags = Column(JSON)  # [{type, msg, action}]
    drawdown_tolerance = Column(Float)
    liquidity_buffer = Column(String(50))
    stress_prediction = Column(JSON)  # {label, text}
    conversation_guide = Column(JSON)  # {style, points}

    investor = relationship("Investor", back_populates="assessments")
    responses = relationship("InvestorResponse", back_populates="assessment")


class InvestorResponse(Base):
    __tablename__ = "investor_responses"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    question_code = Column(String(10), nullable=False)
    option_index = Column(Integer, nullable=False)
    response_time_ms = Column(Integer)  # How long they took to answer
    created_at = Column(DateTime, default=datetime.utcnow)

    assessment = relationship("Assessment", back_populates="responses")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # PMS, AIF, Debt MF, etc.
    subcategory = Column(String(100))
    description = Column(Text)
    
    # Risk vector — the behavioral demands of this product
    risk_vector = Column(JSON, nullable=False)  # {trait: 0-100 demand score}
    
    # Product details
    min_investment = Column(Float)  # In lakhs
    lock_in_years = Column(Float, default=0)
    expected_return_range = Column(String(50))  # "12-18%"
    risk_label = Column(String(50))  # "High", "Moderate", etc.
    liquidity = Column(String(100))  # "T+3", "3-year lock", etc.
    
    # Source of risk vector
    vector_source = Column(String(50), default="manual")  # "manual" or "ai_analyzed"
    source_documents = Column(JSON)  # filenames of analyzed docs
    ai_analysis_notes = Column(Text)  # AI's reasoning for the scores
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─── v3 MODELS ───

class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey("investors.id"), nullable=False)
    status = Column(String(20), default="in_progress")  # in_progress, completed, abandoned
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    device_type = Column(String(20))  # mobile, desktop, tablet
    median_response_time_ms = Column(Integer)
    calibration_data = Column(JSON)  # {"anchor_amount": 300000, "knowledge_level": "advanced", "has_context": true}

    # Computed scores (populated on completion)
    risk_tolerance_score = Column(Float)
    risk_tolerance_sigma = Column(Float)
    loss_aversion_lambda = Column(Float)  # raw lambda (typically 1.0-4.0)
    loss_aversion_sigma = Column(Float)
    time_preference_k = Column(Float)  # discount rate k (geometric mean)
    time_preference_k_short = Column(Float)  # annual discount rate at 1yr horizon
    time_preference_k_long = Column(Float)  # annualized discount rate at 5yr horizon
    time_preference_sigma = Column(Float)
    herding_index = Column(Float)  # 0-1 shift magnitude
    herding_sigma = Column(Float)
    consistency_score = Column(Float)  # 0-100

    investor = relationship("Investor", backref="game_sessions")
    trials = relationship("GameTrial", back_populates="session")


class GameTrial(Base):
    __tablename__ = "game_trials"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    game_type = Column(String(30), nullable=False)  # risk_tolerance, loss_aversion, time_preference, herding
    trial_number = Column(Integer, nullable=False)  # 1-based within each game
    stimulus = Column(JSON, nullable=False)
    response = Column(JSON, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("GameSession", back_populates="trials")


class DocumentUpload(Base):
    __tablename__ = "document_uploads"

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey("investors.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # CAMS, KFINTECH, NSDL, CDSL, BROKER_CSV
    file_size_bytes = Column(Integer)
    status = Column(String(20), default="pending")  # pending, parsing, parsed, scoring, scored, failed
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

    investor = relationship("Investor", backref="document_uploads")
    transactions = relationship("ParsedTransaction", back_populates="upload")


class ParsedTransaction(Base):
    __tablename__ = "parsed_transactions"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("document_uploads.id"), nullable=False)
    investor_id = Column(Integer, ForeignKey("investors.id"), nullable=False)

    # Transaction details
    date = Column(DateTime, nullable=False)
    type = Column(String(30), nullable=False)  # PURCHASE, PURCHASE_SIP, REDEMPTION, SWITCH_IN, SWITCH_OUT, DIVIDEND_PAYOUT, DIVIDEND_REINVEST
    amount = Column(Float, nullable=False)  # INR (positive=buy, negative=sell)
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
    nifty_on_date = Column(Float)  # NIFTY 50 close
    nifty_drawdown_pct = Column(Float)  # drawdown from peak (negative = in drawdown)
    scheme_nav_on_date = Column(Float)  # for PGR/PLR

    upload = relationship("DocumentUpload", back_populates="transactions")


class TransactionScore(Base):
    __tablename__ = "transaction_scores"

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey("investors.id"), nullable=False)
    upload_ids = Column(JSON)  # list of document_upload ids used

    # 7 Behavioral Scores (0-100, higher = more biased/stronger trait)
    disposition_effect = Column(Float)  # PGR-PLR
    disposition_sigma = Column(Float)
    sip_discipline = Column(Float)  # composite SIP health (INVERTED: 100 = best discipline)
    sip_sigma = Column(Float)
    panic_score = Column(Float)  # redemptions during drawdowns
    panic_sigma = Column(Float)
    diversification = Column(Float)  # HHI-based (INVERTED: 100 = best diversified)
    diversification_sigma = Column(Float)
    herding_score = Column(Float)  # switch-to-trending
    herding_sigma = Column(Float)
    overtrading = Column(Float)  # turnover-based
    overtrading_sigma = Column(Float)
    recency_bias = Column(Float)  # chase recent performers
    recency_sigma = Column(Float)

    n_transactions = Column(Integer)
    date_range_months = Column(Integer)
    computed_at = Column(DateTime, default=datetime.utcnow)

    investor = relationship("Investor", backref="transaction_scores")


class BehavioralProfile(Base):
    """Unified output — one active row per investor. Product matching and advisor reports read from this."""
    __tablename__ = "behavioral_profiles"

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey("investors.id"), unique=True, nullable=False)

    # Source tracking
    data_sources = Column(String(50))  # PSYCHOMETRIC_ONLY, TRANSACTION_ONLY, QUESTIONNAIRE_ONLY, FUSED
    last_game_session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=True)
    last_assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    last_transaction_score_id = Column(Integer, ForeignKey("transaction_scores.id"), nullable=True)

    # 10 unified trait scores (0-100) — posterior after Bayesian fusion
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

    # Composite
    composite_risk_score = Column(Float)
    say_do_gap = Column(Float)  # max divergence stated vs revealed
    say_do_details = Column(JSON)  # per-trait breakdown

    # Flags & insights
    behavioral_flags = Column(JSON)
    stress_prediction = Column(JSON)
    drawdown_tolerance = Column(Float)
    liquidity_buffer = Column(String(50))
    conversation_guide = Column(JSON)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    investor = relationship("Investor", backref=backref("behavioral_profile", uselist=False))


class ProfileHistory(Base):
    __tablename__ = "profile_history"

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey("investors.id"), nullable=False)
    profile_snapshot = Column(JSON, nullable=False)
    trigger = Column(String(50))  # GAME_COMPLETE, DOCUMENT_PARSED, QUESTIONNAIRE_COMPLETE, MANUAL_OVERRIDE
    created_at = Column(DateTime, default=datetime.utcnow)


class InvestorFinancialContext(Base):
    __tablename__ = "investor_financial_context"

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey("investors.id"), unique=True, nullable=False)

    # Income & stability
    annual_income = Column(Float)  # in lakhs
    income_source = Column(String(50))  # SALARIED, BUSINESS, PROFESSIONAL, RETIRED, MIXED
    income_stability = Column(String(20))  # VERY_STABLE, STABLE, MODERATE, VOLATILE
    income_growth_expectation = Column(String(20))  # GROWING, STABLE, DECLINING
    years_to_retirement = Column(Integer)

    # Obligations & liquidity needs
    monthly_fixed_obligations = Column(Float)  # EMIs, rent, insurance, school fees — in lakhs/month
    annual_discretionary_spend = Column(Float)  # lifestyle, travel — in lakhs
    upcoming_obligations_1y = Column(Float)  # known big expenses next 12 months (lakhs)
    upcoming_obligations_3y = Column(Float)  # next 1-3 years
    upcoming_obligations_5y = Column(Float)  # next 3-5 years
    upcoming_obligations_10y = Column(Float)  # next 5-10 years
    obligation_notes = Column(Text)  # free text

    # Existing assets (full picture)
    existing_equity_mf = Column(Float)  # in lakhs
    existing_debt_mf = Column(Float)
    existing_direct_equity = Column(Float)
    existing_fixed_deposits = Column(Float)
    existing_real_estate_value = Column(Float)  # non-primary residence
    existing_gold = Column(Float)
    existing_ppf_epf_nps = Column(Float)
    existing_insurance_corpus = Column(Float)
    existing_other_investments = Column(Float)
    existing_cash_savings = Column(Float)
    primary_residence_value = Column(Float)  # not counted as investable
    total_investable_assets = Column(Float)  # auto-computed
    existing_liabilities = Column(Float)  # total outstanding loans
    net_worth = Column(Float)  # auto-computed

    # Real loss experience
    has_experienced_real_loss = Column(Boolean)
    worst_loss_amount = Column(Float)  # in lakhs, actual realized loss
    worst_loss_context = Column(String(100))  # "2008 crash", "bad stock pick"
    behavior_during_loss = Column(String(50))  # PANIC_SOLD, HELD_THROUGH, BOUGHT_MORE, FROZE, NOT_APPLICABLE
    loss_recovery_experience = Column(String(50))  # RECOVERED_FULLY, PARTIAL_RECOVERY, PERMANENT_LOSS, NOT_APPLICABLE

    # Return aspirations
    target_return_annual_pct = Column(Float)  # what they WANT (e.g., 15%)
    return_purpose = Column(Text)  # WHY they want this return
    time_horizon_years = Column(Integer)  # for this aspiration
    is_aspiration_realistic = Column(Boolean)  # computed by market cycle engine
    aspiration_gap_notes = Column(Text)

    # Meaning of money (emotional driver)
    money_meaning = Column(String(20))  # security, freedom, legacy, lifestyle, game
    first_instinct = Column(String(20))  # save, invest, spend, give

    # Fear & emotional landscape
    worst_fear = Column(String(20))  # drawdown, illiquidity, inflation, fomo, trust, legacy
    fear_impact = Column(String(20))  # panic, anxious, steady, detached
    regret_preference = Column(String(20))  # loss_regret, miss_regret

    # Knowledge & experience
    knowledge_level = Column(String(20))  # basic, intermediate, advanced, expert
    investment_experience = Column(JSON)  # list of experience types
    wealth_concentration = Column(Float)  # % of total wealth this portfolio represents
    equity_experience = Column(Boolean)  # has past equity experience
    downturn_behavior = Column(String(30))  # sold_all, sold_some, held, bought_more, not_invested
    recovery_behavior = Column(String(30))  # full_recovery, exited_early, never_returned

    # Decision making structure
    decision_maker = Column(String(30))  # SELF, JOINT_SPOUSE, FAMILY_ELDER, ADVISOR_DEPENDENT
    family_influence_level = Column(String(20))  # NONE, LOW, MODERATE, HIGH, DOMINANT
    existing_advisor_relationship = Column(Boolean)
    tax_bracket = Column(String(20))  # 0%, 5%, 20%, 30%, SURCHARGE

    # Computed
    financial_capacity_score = Column(Float)  # 0-100: structural ability to bear risk
    liquidity_runway_months = Column(Float)  # existing_cash / monthly_obligations
    obligation_coverage_ratio = Column(Float)  # annual_income / annual_obligations

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    investor = relationship("Investor", backref=backref("financial_context", uselist=False))


class MarketRegimeCache(Base):
    __tablename__ = "market_regime_cache"

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


# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)
