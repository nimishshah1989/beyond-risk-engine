from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text, Boolean,
    DateTime, JSON, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
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


# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)
