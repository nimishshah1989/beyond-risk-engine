"""Financial Life Context API — The First Conversation.

CRUD for investor financial context + computed capacity score endpoint.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.database import get_db, Investor, InvestorFinancialContext
from app.services.financial_context import (
    auto_compute_fields,
    analyze_loss_experience,
    compute_financial_capacity,
)

logger = logging.getLogger("beyond_risk.api.context")
router = APIRouter(prefix="/api/context", tags=["Financial Context"])


# ─── Pydantic schemas ───

class FinancialContextInput(BaseModel):
    """Input schema for creating/updating financial context."""
    # Income & stability
    annual_income: Optional[float] = Field(None, description="Annual income in lakhs")
    income_source: Optional[str] = Field(None, description="SALARIED, BUSINESS, PROFESSIONAL, RETIRED, MIXED")
    income_stability: Optional[str] = Field(None, description="VERY_STABLE, STABLE, MODERATE, VOLATILE")
    income_growth_expectation: Optional[str] = Field(None, description="GROWING, STABLE, DECLINING")
    years_to_retirement: Optional[int] = None

    # Obligations
    monthly_fixed_obligations: Optional[float] = Field(None, description="In lakhs/month")
    annual_discretionary_spend: Optional[float] = Field(None, description="In lakhs/year")
    upcoming_obligations_1y: Optional[float] = Field(None, description="In lakhs")
    upcoming_obligations_3y: Optional[float] = None
    upcoming_obligations_5y: Optional[float] = None
    upcoming_obligations_10y: Optional[float] = None
    obligation_notes: Optional[str] = None

    # Existing assets
    existing_equity_mf: Optional[float] = None
    existing_debt_mf: Optional[float] = None
    existing_direct_equity: Optional[float] = None
    existing_fixed_deposits: Optional[float] = None
    existing_real_estate_value: Optional[float] = None
    existing_gold: Optional[float] = None
    existing_ppf_epf_nps: Optional[float] = None
    existing_insurance_corpus: Optional[float] = None
    existing_other_investments: Optional[float] = None
    existing_cash_savings: Optional[float] = None
    primary_residence_value: Optional[float] = None
    existing_liabilities: Optional[float] = None

    # Meaning of money
    money_meaning: Optional[str] = Field(None, description="security, freedom, legacy, lifestyle, game")
    first_instinct: Optional[str] = Field(None, description="save, invest, spend, give")

    # Fear & emotional landscape
    worst_fear: Optional[str] = Field(None, description="drawdown, illiquidity, inflation, fomo, trust, legacy")
    fear_impact: Optional[str] = Field(None, description="panic, anxious, steady, detached")
    regret_preference: Optional[str] = Field(None, description="loss_regret, miss_regret")

    # Knowledge & experience
    knowledge_level: Optional[str] = Field(None, description="basic, intermediate, advanced, expert")
    investment_experience: Optional[list] = Field(None, description="List of experience types")
    wealth_concentration: Optional[float] = Field(None, description="% of total wealth this portfolio represents")
    equity_experience: Optional[bool] = None
    downturn_behavior: Optional[str] = Field(None, description="sold_all, sold_some, held, bought_more, not_invested")
    recovery_behavior: Optional[str] = Field(None, description="full_recovery, exited_early, never_returned")

    # Loss experience
    has_experienced_real_loss: Optional[bool] = None
    worst_loss_amount: Optional[float] = None
    worst_loss_context: Optional[str] = None
    behavior_during_loss: Optional[str] = Field(None, description="PANIC_SOLD, HELD_THROUGH, BOUGHT_MORE, FROZE, NOT_APPLICABLE")
    loss_recovery_experience: Optional[str] = Field(None, description="RECOVERED_FULLY, PARTIAL_RECOVERY, PERMANENT_LOSS, NOT_APPLICABLE")

    # Return aspirations
    target_return_annual_pct: Optional[float] = None
    return_purpose: Optional[str] = None
    time_horizon_years: Optional[int] = None

    # Decision making
    decision_maker: Optional[str] = Field(None, description="SELF, JOINT_SPOUSE, FAMILY_ELDER, ADVISOR_DEPENDENT")
    family_influence_level: Optional[str] = Field(None, description="NONE, LOW, MODERATE, HIGH, DOMINANT")
    existing_advisor_relationship: Optional[bool] = None
    tax_bracket: Optional[str] = None


# ─── Endpoints ───

@router.get("/{investor_id}")
def get_financial_context(investor_id: int, db: Session = Depends(get_db)):
    """Get the financial context for an investor."""
    investor = db.query(Investor).filter_by(id=investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    ctx = db.query(InvestorFinancialContext).filter_by(investor_id=investor_id).first()
    if not ctx:
        return {"investor_id": investor_id, "exists": False, "context": None}

    return {
        "investor_id": investor_id,
        "exists": True,
        "context": _context_to_dict(ctx),
    }


@router.post("/{investor_id}")
def save_financial_context(
    investor_id: int, data: FinancialContextInput, db: Session = Depends(get_db)
):
    """Create or update the financial context for an investor. Supports partial updates (save as you go)."""
    investor = db.query(Investor).filter_by(id=investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    ctx = db.query(InvestorFinancialContext).filter_by(investor_id=investor_id).first()

    if not ctx:
        ctx = InvestorFinancialContext(investor_id=investor_id)
        db.add(ctx)

    # Apply all provided fields (partial update)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(ctx, field):
            setattr(ctx, field, value)

    # Auto-compute derived fields
    auto_compute_fields(ctx)

    db.commit()
    db.refresh(ctx)

    logger.info(
        "Financial context saved for investor %d (capacity: %.1f)",
        investor_id, ctx.financial_capacity_score or 0,
    )

    return {
        "investor_id": investor_id,
        "context": _context_to_dict(ctx),
        "financial_capacity_score": ctx.financial_capacity_score,
    }


@router.get("/{investor_id}/capacity")
def get_capacity_score(investor_id: int, db: Session = Depends(get_db)):
    """Get the computed financial capacity score with breakdown and constraints."""
    investor = db.query(Investor).filter_by(id=investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    ctx = db.query(InvestorFinancialContext).filter_by(investor_id=investor_id).first()
    if not ctx:
        raise HTTPException(status_code=404, detail="Financial context not yet captured")

    # Recompute to ensure fresh
    auto_compute_fields(ctx)
    db.commit()

    loss_analysis = analyze_loss_experience(ctx)

    return {
        "investor_id": investor_id,
        "financial_capacity_score": ctx.financial_capacity_score,
        "liquidity_runway_months": ctx.liquidity_runway_months,
        "obligation_coverage_ratio": ctx.obligation_coverage_ratio,
        "total_investable_assets": ctx.total_investable_assets,
        "net_worth": ctx.net_worth,
        "loss_experience": loss_analysis,
    }


# ─── Helpers ───

def _context_to_dict(ctx: InvestorFinancialContext) -> dict:
    """Convert SQLAlchemy model to dict for JSON response."""
    return {
        "id": ctx.id,
        "investor_id": ctx.investor_id,
        # Income
        "annual_income": ctx.annual_income,
        "income_source": ctx.income_source,
        "income_stability": ctx.income_stability,
        "income_growth_expectation": ctx.income_growth_expectation,
        "years_to_retirement": ctx.years_to_retirement,
        # Obligations
        "monthly_fixed_obligations": ctx.monthly_fixed_obligations,
        "annual_discretionary_spend": ctx.annual_discretionary_spend,
        "upcoming_obligations_1y": ctx.upcoming_obligations_1y,
        "upcoming_obligations_3y": ctx.upcoming_obligations_3y,
        "upcoming_obligations_5y": ctx.upcoming_obligations_5y,
        "upcoming_obligations_10y": ctx.upcoming_obligations_10y,
        "obligation_notes": ctx.obligation_notes,
        # Assets
        "existing_equity_mf": ctx.existing_equity_mf,
        "existing_debt_mf": ctx.existing_debt_mf,
        "existing_direct_equity": ctx.existing_direct_equity,
        "existing_fixed_deposits": ctx.existing_fixed_deposits,
        "existing_real_estate_value": ctx.existing_real_estate_value,
        "existing_gold": ctx.existing_gold,
        "existing_ppf_epf_nps": ctx.existing_ppf_epf_nps,
        "existing_insurance_corpus": ctx.existing_insurance_corpus,
        "existing_other_investments": ctx.existing_other_investments,
        "existing_cash_savings": ctx.existing_cash_savings,
        "primary_residence_value": ctx.primary_residence_value,
        "total_investable_assets": ctx.total_investable_assets,
        "existing_liabilities": ctx.existing_liabilities,
        "net_worth": ctx.net_worth,
        # Meaning of money
        "money_meaning": ctx.money_meaning,
        "first_instinct": ctx.first_instinct,
        # Fear & emotional landscape
        "worst_fear": ctx.worst_fear,
        "fear_impact": ctx.fear_impact,
        "regret_preference": ctx.regret_preference,
        # Knowledge & experience
        "knowledge_level": ctx.knowledge_level,
        "investment_experience": ctx.investment_experience,
        "wealth_concentration": ctx.wealth_concentration,
        "equity_experience": ctx.equity_experience,
        "downturn_behavior": ctx.downturn_behavior,
        "recovery_behavior": ctx.recovery_behavior,
        # Loss experience
        "has_experienced_real_loss": ctx.has_experienced_real_loss,
        "worst_loss_amount": ctx.worst_loss_amount,
        "worst_loss_context": ctx.worst_loss_context,
        "behavior_during_loss": ctx.behavior_during_loss,
        "loss_recovery_experience": ctx.loss_recovery_experience,
        # Aspirations
        "target_return_annual_pct": ctx.target_return_annual_pct,
        "return_purpose": ctx.return_purpose,
        "time_horizon_years": ctx.time_horizon_years,
        "is_aspiration_realistic": ctx.is_aspiration_realistic,
        "aspiration_gap_notes": ctx.aspiration_gap_notes,
        # Decision making
        "decision_maker": ctx.decision_maker,
        "family_influence_level": ctx.family_influence_level,
        "existing_advisor_relationship": ctx.existing_advisor_relationship,
        "tax_bracket": ctx.tax_bracket,
        # Computed
        "financial_capacity_score": ctx.financial_capacity_score,
        "liquidity_runway_months": ctx.liquidity_runway_months,
        "obligation_coverage_ratio": ctx.obligation_coverage_ratio,
        "updated_at": ctx.updated_at.isoformat() if ctx.updated_at else None,
    }
