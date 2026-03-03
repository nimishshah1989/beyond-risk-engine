"""Financial Life Context — capacity scoring, loss experience analysis, constraint logic.

The first conversation isn't about investments — it's about understanding the person's
financial life completely. This module produces a Financial Capacity Score that acts as a
HARD CEILING on risk allocation.
"""
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("beyond_risk.financial_context")


def compute_total_investable_assets(ctx) -> float:
    """Sum all investable asset classes (excludes primary residence)."""
    fields = [
        ctx.existing_equity_mf, ctx.existing_debt_mf, ctx.existing_direct_equity,
        ctx.existing_fixed_deposits, ctx.existing_real_estate_value, ctx.existing_gold,
        ctx.existing_ppf_epf_nps, ctx.existing_insurance_corpus,
        ctx.existing_other_investments, ctx.existing_cash_savings,
    ]
    return sum(f or 0 for f in fields)


def compute_net_worth(ctx) -> float:
    """Total investable assets + primary residence - liabilities."""
    total_investable = compute_total_investable_assets(ctx)
    primary = ctx.primary_residence_value or 0
    liabilities = ctx.existing_liabilities or 0
    return total_investable + primary - liabilities


def compute_financial_capacity(ctx) -> float:
    """Structural ability to bear investment risk. 0 = cannot afford ANY risk, 100 = maximum capacity.

    This is a HARD CEILING — behavioral willingness cannot exceed structural capacity.
    """
    scores = []

    # 1. Liquidity runway (25% weight)
    monthly_obligations = ctx.monthly_fixed_obligations or 0
    cash_savings = ctx.existing_cash_savings or 0
    if monthly_obligations > 0:
        runway_months = cash_savings / monthly_obligations
    else:
        runway_months = 24  # no obligations = high runway
    runway_score = min(100, runway_months / 12 * 100)  # 12+ months = 100
    scores.append(("runway", runway_score, 0.25))

    # 2. Obligation coverage ratio (20% weight)
    annual_income = ctx.annual_income or 0
    annual_discretionary = ctx.annual_discretionary_spend or 0
    annual_obligations = (monthly_obligations * 12) + annual_discretionary
    if annual_obligations > 0:
        coverage = annual_income / annual_obligations
    else:
        coverage = 5  # no obligations = excellent coverage
    coverage_score = min(100, max(0, (coverage - 1) * 100))  # ratio 1.0 = 0, 2.0+ = 100
    scores.append(("coverage", coverage_score, 0.20))

    # 3. Time horizon (20% weight)
    horizon = ctx.time_horizon_years or ctx.years_to_retirement or 10
    horizon_score = min(100, horizon * 10)  # 10+ years = 100
    scores.append(("horizon", horizon_score, 0.20))

    # 4. Upcoming obligations pressure (15% weight)
    near_obligations = (ctx.upcoming_obligations_1y or 0) + (ctx.upcoming_obligations_3y or 0)
    total_investable = ctx.total_investable_assets or compute_total_investable_assets(ctx)
    if total_investable > 0:
        obligation_pressure = near_obligations / total_investable * 100
    else:
        obligation_pressure = 100 if near_obligations > 0 else 0
    obligation_score = max(0, 100 - obligation_pressure)
    scores.append(("obligations", obligation_score, 0.15))

    # 5. Income stability (10% weight)
    stability_map = {"VERY_STABLE": 90, "STABLE": 70, "MODERATE": 50, "VOLATILE": 25}
    stability_score = stability_map.get(ctx.income_stability, 50)
    scores.append(("stability", stability_score, 0.10))

    # 6. Net worth buffer (10% weight)
    nw = ctx.net_worth or compute_net_worth(ctx)
    nw_score = min(100, max(0, nw / 100 * 10))  # 100L+ net worth = 100
    scores.append(("networth", nw_score, 0.10))

    capacity = sum(s * w for _, s, w in scores)
    return round(capacity, 1)


def compute_liquidity_runway(ctx) -> float:
    """How many months of obligations can be covered by cash/liquid assets."""
    monthly = ctx.monthly_fixed_obligations or 0
    cash = ctx.existing_cash_savings or 0
    if monthly <= 0:
        return 99.0  # effectively unlimited
    return round(cash / monthly, 1)


def compute_obligation_coverage_ratio(ctx) -> float:
    """Annual income divided by annual obligations."""
    annual_income = ctx.annual_income or 0
    monthly_obligations = ctx.monthly_fixed_obligations or 0
    annual_discretionary = ctx.annual_discretionary_spend or 0
    total_annual = (monthly_obligations * 12) + annual_discretionary
    if total_annual <= 0:
        return 99.0
    return round(annual_income / total_annual, 2)


def analyze_loss_experience(ctx) -> Dict:
    """Analyze real loss experience — the strongest predictor of future behavior.

    Someone who held through 2008 has DEMONSTRATED resilience.
    Someone who panic-sold has DEMONSTRATED fragility — regardless of what they say now.
    """
    if not ctx.has_experienced_real_loss:
        return {
            "category": "UNTESTED",
            "insight": (
                "This investor has never experienced a significant real loss. "
                "Their risk tolerance is theoretical and unvalidated. "
                "Treat stated preferences with extra caution."
            ),
            "confidence_modifier": 0.6,
        }

    loss_amount = ctx.worst_loss_amount or 0
    loss_context = ctx.worst_loss_context or "unknown event"

    experience_map = {
        "PANIC_SOLD": {
            "category": "DEMONSTRATED_FRAGILITY",
            "insight": (
                f"Investor panic-sold during {loss_context}. Loss of \u20b9{loss_amount}L. "
                f"This is the strongest predictor of future behavior under stress — "
                f"overrides questionnaire scores."
            ),
            "confidence_modifier": 1.5,
            "override_traits": {"emotional_volatility": "increase_20", "loss_aversion": "increase_15"},
        },
        "HELD_THROUGH": {
            "category": "DEMONSTRATED_RESILIENCE",
            "insight": (
                f"Investor held through {loss_context} despite \u20b9{loss_amount}L paper loss. "
                f"Strong evidence of genuine risk tolerance."
            ),
            "confidence_modifier": 1.3,
            "override_traits": {"behavioral_stability": "increase_15", "emotional_volatility": "decrease_15"},
        },
        "BOUGHT_MORE": {
            "category": "DEMONSTRATED_CONTRARIAN",
            "insight": (
                f"Investor increased allocation during {loss_context}. "
                f"Rare contrarian behavior — top 5% of investors."
            ),
            "confidence_modifier": 1.5,
            "override_traits": {"behavioral_stability": "increase_25", "loss_aversion": "decrease_20"},
        },
        "FROZE": {
            "category": "DEMONSTRATED_PARALYSIS",
            "insight": (
                f"Investor froze during {loss_context} — neither sold nor bought. "
                f"May need direct advisor intervention during future stress."
            ),
            "confidence_modifier": 1.2,
            "override_traits": {"decision_confidence": "decrease_20"},
        },
    }

    return experience_map.get(ctx.behavior_during_loss, {
        "category": "UNKNOWN",
        "insight": "Loss experience recorded but behavior pattern unclear.",
        "confidence_modifier": 1.0,
    })


def apply_capacity_constraint(
    behavioral_risk_score: float, financial_capacity_score: float, ctx
) -> Tuple[float, List[Dict]]:
    """Apply financial capacity as a HARD CEILING on behavioral risk.

    Even if behavioral games say investor is very risk-tolerant (score 85),
    if their financial capacity is 35 (heavy obligations, low runway),
    the EFFECTIVE risk allocation must not exceed capacity.
    """
    if behavioral_risk_score <= financial_capacity_score:
        return behavioral_risk_score, []

    constrained_risk = financial_capacity_score
    gap = behavioral_risk_score - financial_capacity_score

    upcoming_3y = ctx.upcoming_obligations_3y or 0
    runway = ctx.liquidity_runway_months or compute_liquidity_runway(ctx)

    flag = {
        "type": "critical",
        "title": "Risk Appetite Exceeds Financial Capacity",
        "msg": (
            f"Investor wants risk level {behavioral_risk_score:.0f} but can structurally afford "
            f"only {financial_capacity_score:.0f}. Near-term obligations of \u20b9{upcoming_3y:.0f}L "
            f"over 3 years and liquidity runway of only {runway:.0f} months cap the maximum "
            f"appropriate risk exposure."
        ),
        "action": (
            f"Cap equity allocation at {min(70, int(financial_capacity_score))}%. "
            f"Ensure {max(6, 12 - int(financial_capacity_score) // 10)} months of obligations "
            f"in liquid instruments before any equity deployment."
        ),
    }

    return constrained_risk, [flag]


def auto_compute_fields(ctx) -> None:
    """Auto-compute derived fields on the financial context object."""
    ctx.total_investable_assets = compute_total_investable_assets(ctx)
    ctx.net_worth = compute_net_worth(ctx)
    ctx.financial_capacity_score = compute_financial_capacity(ctx)
    ctx.liquidity_runway_months = compute_liquidity_runway(ctx)
    ctx.obligation_coverage_ratio = compute_obligation_coverage_ratio(ctx)
