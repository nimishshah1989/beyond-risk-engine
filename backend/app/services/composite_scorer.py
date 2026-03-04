"""Composite Scorer — 6-dimension risk profiling inspired by yash-v2.

Produces a comprehensive assessment combining:
  1. Financial Capacity (25%) — structural ability to bear risk
  2. Behavioral Pattern (25%) — actual behavior under stress
  3. Fear-Risk Coherence (20%) — internal consistency of fears vs tolerance
  4. Money Meaning (15%) — emotional driver mapped to risk
  5. Knowledge (10%) — experience breadth + knowledge depth
  6. Market Cycle (5%) — current regime adjustment

Also computes: equity ceiling, allocation, Liquidity x Drawdown matrix,
investment approaches, behavioral flags, and wisdom quotes.
"""
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger("beyond_risk.composite_scorer")

# ─── Score Mappings (from yash-v2) ───

MEANING_SCORES = {
    "security": 25, "freedom": 45, "lifestyle": 50, "legacy": 60, "game": 80,
}
MEANING_LABELS = {
    "security": "Security & Protection",
    "freedom": "Freedom & Autonomy",
    "lifestyle": "Lifestyle & Experience",
    "legacy": "Legacy & Growth",
    "game": "The Score & The Game",
}
MEANING_DESCRIPTIONS = {
    "security": "Money means never worrying about bills, emergencies, or dependence on others. Your portfolio must feel safe above all.",
    "freedom": "Money means the ability to say no, to work because you want to, not because you must. Optionality is your priority.",
    "lifestyle": "Money means living well — travel, comfort, education, experiences. Returns must fund the life you want.",
    "legacy": "Money means building something that outlasts you — generational wealth, funding what matters beyond yourself.",
    "game": "Money is the score. You enjoy the building process itself. Wealth is a measure of capability and intellect.",
}

FEAR_SCORES = {
    "drawdown": 20, "illiquidity": 30, "trust": 25,
    "inflation": 55, "legacy": 45, "fomo": 75,
}

IMPACT_SCORES = {"panic": 10, "anxious": 35, "steady": 65, "detached": 90}

REGRET_SCORES = {"loss_regret": 30, "miss_regret": 70}

KNOWLEDGE_SCORES = {"basic": 20, "intermediate": 45, "advanced": 75, "expert": 95}

DOWNTURN_SCORES = {
    "sold_all": 15, "sold_some": 35, "held": 65, "bought_more": 90, "not_invested": 40,
}

RECOVERY_SCORES = {"full_recovery": 85, "exited_early": 40, "never_returned": 10}

DROP_REACTION_SCORES = {"panic": 10, "anxious": 30, "steady": 65, "detached": 90}

# ─── Profile Labels ───

PROFILE_LABELS = [
    (25, "Conservative", "#5DADE2"),
    (40, "Moderate-Conservative", "#58D68D"),
    (60, "Moderate", "#C9A84C"),
    (80, "Moderate-Aggressive", "#E8913A"),
    (100, "Aggressive", "#E74C3C"),
]

EQUITY_SUB_ALLOCATION = {
    "Conservative": {"large_cap": 70, "mid_cap": 20, "small_cap": 0, "international": 10},
    "Moderate-Conservative": {"large_cap": 55, "mid_cap": 25, "small_cap": 5, "international": 15},
    "Moderate": {"large_cap": 40, "mid_cap": 30, "small_cap": 15, "international": 15},
    "Moderate-Aggressive": {"large_cap": 30, "mid_cap": 30, "small_cap": 25, "international": 15},
    "Aggressive": {"large_cap": 30, "mid_cap": 30, "small_cap": 25, "international": 15},
}


def get_profile_label(score: float) -> Dict[str, str]:
    """Map composite score to profile label and color."""
    for threshold, label, color in PROFILE_LABELS:
        if score <= threshold:
            return {"label": label, "color": color}
    return {"label": "Aggressive", "color": "#E74C3C"}


# ─── Dimension Scorers ───

def score_financial_capacity(ctx) -> Dict:
    """Score from existing financial context service (already 0-100)."""
    score = ctx.financial_capacity_score or 0
    return {"score": round(score, 1), "weight": 0.25, "label": "Financial Capacity"}


def score_behavioral_pattern(ctx, game_scores: Optional[Dict] = None) -> Dict:
    """Score from actual behavior under stress + game scores."""
    has_equity = ctx.equity_experience if ctx.equity_experience is not None else ctx.has_experienced_real_loss

    if has_equity and ctx.downturn_behavior:
        downturn_s = DOWNTURN_SCORES.get(ctx.downturn_behavior, 40)
        drop_s = DROP_REACTION_SCORES.get(ctx.fear_impact, 50)
        recovery_s = RECOVERY_SCORES.get(ctx.recovery_behavior, 40)
        behavioral = downturn_s * 0.5 + drop_s * 0.2 + recovery_s * 0.3
    elif ctx.fear_impact:
        behavioral = DROP_REACTION_SCORES.get(ctx.fear_impact, 50) * 0.5
    else:
        behavioral = 50.0

    # Blend with game-derived composite if available
    if game_scores and game_scores.get("composite_risk_score") is not None:
        game_composite = game_scores["composite_risk_score"]
        behavioral = behavioral * 0.4 + game_composite * 0.6

    # Emotional penalty for demonstrated panic
    if ctx.behavior_during_loss == "PANIC_SOLD":
        behavioral = max(0, behavioral - 10)

    return {"score": round(max(0, min(100, behavioral)), 1), "weight": 0.25, "label": "Behavioral Pattern"}


def score_fear_coherence(ctx) -> Dict:
    """Measures internal consistency between fears and tolerance."""
    fear_s = FEAR_SCORES.get(ctx.worst_fear, 50)
    impact_s = IMPACT_SCORES.get(ctx.fear_impact, 50)
    regret_s = REGRET_SCORES.get(ctx.regret_preference, 50)

    coherence = fear_s * 0.4 + impact_s * 0.35 + regret_s * 0.25
    return {"score": round(coherence, 1), "weight": 0.20, "label": "Fear-Risk Coherence"}


def score_money_meaning(ctx) -> Dict:
    """Direct mapping from meaning of money archetype."""
    score = MEANING_SCORES.get(ctx.money_meaning, 50)
    return {"score": float(score), "weight": 0.15, "label": "Money Meaning"}


def score_knowledge(ctx) -> Dict:
    """Knowledge level + investment experience breadth."""
    knowledge_s = KNOWLEDGE_SCORES.get(ctx.knowledge_level, 35)
    experience_count = len(ctx.investment_experience or [])
    experience_s = min(100, experience_count * 12)
    combined = knowledge_s * 0.6 + experience_s * 0.4
    return {"score": round(combined, 1), "weight": 0.10, "label": "Knowledge & Experience"}


def score_market_cycle(regime: Optional[Dict]) -> Dict:
    """Market cycle adjustment — neutral if no regime data."""
    if not regime:
        return {"score": 50.0, "weight": 0.05, "label": "Market Cycle"}
    regime_name = regime.get("regime", "neutral")
    cycle_map = {"expansion": 60, "consolidation": 50, "contraction": 35, "neutral": 50}
    score = cycle_map.get(regime_name.lower(), 50)
    return {"score": float(score), "weight": 0.05, "label": "Market Cycle"}


# ─── Composite Score ───

def compute_composite(dimensions: List[Dict]) -> float:
    """Weighted sum of all 6 dimensions."""
    total = sum(d["score"] * d["weight"] for d in dimensions)
    return round(max(0, min(100, total)), 1)


# ─── Equity Ceiling & Hard Constraints ───

def compute_equity_ceiling(ctx, composite: float) -> Dict:
    """Hard caps on equity allocation based on constraints."""
    ceiling = 85  # max possible
    constraints = []

    # Emergency fund < 3 months
    cash = ctx.existing_cash_savings or 0
    monthly = ctx.monthly_fixed_obligations or 0
    runway = cash / monthly if monthly > 0 else 24
    if runway < 3:
        ceiling = min(ceiling, 40)
        constraints.append("Emergency fund under 3 months — equity capped at 40%")

    # Time horizon < 1 year
    horizon = ctx.time_horizon_years or ctx.years_to_retirement or 10
    if horizon < 1:
        ceiling = min(ceiling, 10)
        constraints.append("Investment horizon under 1 year — equity capped at 10%")

    # Over-concentrated
    concentration = ctx.wealth_concentration or 0
    if concentration > 80:
        ceiling = max(0, ceiling - 25)
        constraints.append("Over 80% wealth concentrated — equity reduced by 25%")
    elif concentration > 60:
        ceiling = max(0, ceiling - 15)
        constraints.append("Over 60% wealth concentrated — equity reduced by 15%")

    # Unproven (no equity experience)
    if not ctx.equity_experience:
        composite = min(composite, 60)
        constraints.append("No equity experience — composite capped at 60")

    # Expectation-fear conflict (FOMO fear + low impact tolerance)
    if ctx.worst_fear == "fomo" and ctx.fear_impact in ("panic", "anxious"):
        composite = min(composite, 50)
        constraints.append("Expectation-fear conflict detected — composite capped at 50")

    return {
        "ceiling": ceiling,
        "effective_composite": round(composite, 1),
        "constraints": constraints,
    }


# ─── Allocation Recommendation ───

def compute_allocation(composite: float, ceiling: int, cycle_adj: float = 0) -> Dict:
    """Recommended asset allocation based on composite score."""
    equity_pct = min(ceiling, max(0, round(composite * 0.85 + cycle_adj)))
    remaining = 100 - equity_pct
    fixed_income = round(remaining * 0.65)
    alternatives = round(remaining * 0.20)
    cash = remaining - fixed_income - alternatives

    profile = get_profile_label(composite)
    sub_alloc = EQUITY_SUB_ALLOCATION.get(profile["label"], EQUITY_SUB_ALLOCATION["Moderate"])

    return {
        "equity": equity_pct,
        "fixed_income": fixed_income,
        "alternatives": alternatives,
        "cash": cash,
        "equity_sub_allocation": sub_alloc,
    }


# ─── Liquidity x Drawdown Matrix ───

MATRIX_CELLS = {
    "HL_HD": {
        "label": "Liquid Growth",
        "subtitle": "High liquidity need + High drawdown tolerance",
        "description": "You need access to your money but can handle market swings. Ideal for diversified equity, global allocation, and concentrated quality strategies.",
    },
    "HL_LD": {
        "label": "Capital-Protected Growth",
        "subtitle": "High liquidity need + Low drawdown tolerance",
        "description": "You need liquidity AND stability. Bond strategies, low-volatility equity, and dynamic allocation protect while keeping money accessible.",
    },
    "LL_HD": {
        "label": "Patient Capital",
        "subtitle": "Low liquidity need + High drawdown tolerance",
        "description": "You can lock money away AND stomach volatility. Private markets, long-horizon compounding, and thematic conviction plays suit you.",
    },
    "LL_LD": {
        "label": "Structured Stability",
        "subtitle": "Low liquidity need + Low drawdown tolerance",
        "description": "Capital preservation is paramount. Structured returns, target-date approaches, and defined-outcome strategies provide certainty.",
    },
}


def compute_matrix_position(ctx, behavioral_score: float, coherence_score: float) -> Dict:
    """Determine position in Liquidity x Drawdown 2x2 matrix."""
    # High liquidity = liquidity is critical or important
    ls = ctx.liquidity_sensitivity if hasattr(ctx, 'liquidity_sensitivity') else None
    high_liquidity = True  # default
    if ctx.time_horizon_years and ctx.time_horizon_years >= 7:
        high_liquidity = False
    if ctx.upcoming_obligations_1y and ctx.upcoming_obligations_1y > 0:
        high_liquidity = True

    # High drawdown tolerance = behavioral >= 55 AND coherence >= 50
    high_drawdown = behavioral_score >= 55 and coherence_score >= 50

    if high_liquidity and high_drawdown:
        cell = "HL_HD"
    elif high_liquidity and not high_drawdown:
        cell = "HL_LD"
    elif not high_liquidity and high_drawdown:
        cell = "LL_HD"
    else:
        cell = "LL_LD"

    return {"cell": cell, "high_liquidity": high_liquidity, "high_drawdown": high_drawdown, **MATRIX_CELLS[cell]}


# ─── Investment Approaches ───

APPROACHES = [
    # Tier 0 — all profiles
    {
        "name": "Capital Protection Strategy",
        "description": "High-quality fixed income, laddered maturities, sovereign-backed instruments. The bedrock of capital safety.",
        "risk": "Low", "suitability": "All profiles", "allocation_range": "25-40%", "horizon": "1-3 years",
        "tier": 0,
    },
    {
        "name": "Income Generation Approach",
        "description": "Cash flow generation through bonds, dividend strategies, and regular-income instruments. Reliable yield without principal risk.",
        "risk": "Low-Moderate", "suitability": "All profiles", "allocation_range": "15-25%", "horizon": "2-5 years",
        "tier": 0,
    },
    {
        "name": "Gold & Real Asset Allocation",
        "description": "Gold, inflation-linked instruments, and real asset exposure as a crisis hedge and inflation protector.",
        "risk": "Moderate", "suitability": "All profiles", "allocation_range": "5-10%", "horizon": "Evergreen",
        "tier": 0,
    },
    # Tier 1 — Moderate-Conservative+
    {
        "name": "Low-Volatility Equity Strategy",
        "description": "Dynamic hedging, low-beta stocks, and drawdown-controlled equity exposure. Growth with guardrails.",
        "risk": "Moderate", "suitability": "Moderate-Conservative and above", "allocation_range": "20-35%", "horizon": "3-5 years",
        "tier": 1,
    },
    {
        "name": "Dynamic Asset Allocation",
        "description": "Systematic shifts between equity and debt based on valuations and market signals. Adapts to conditions.",
        "risk": "Moderate", "suitability": "Moderate-Conservative and above", "allocation_range": "20-30%", "horizon": "3-7 years",
        "tier": 1,
    },
    # Tier 2 — Moderate+
    {
        "name": "Diversified Growth Strategy",
        "description": "Multi-cap equity with sector allocation and global diversification. The classic wealth-building approach.",
        "risk": "Moderate-High", "suitability": "Moderate and above", "allocation_range": "30-50%", "horizon": "5-10 years",
        "tier": 2,
    },
    {
        "name": "Global Equity Allocation",
        "description": "Developed and emerging market equities with rupee-hedge optionality. Diversification beyond Indian markets.",
        "risk": "Moderate-High", "suitability": "Moderate and above", "allocation_range": "10-20%", "horizon": "5-10 years",
        "tier": 2,
    },
    {
        "name": "Concentrated Quality Strategy",
        "description": "15-25 high-conviction businesses with competitive moats. Quality over quantity.",
        "risk": "High", "suitability": "Moderate and above", "allocation_range": "25-40%", "horizon": "5-10 years",
        "tier": 2,
    },
    # Tier 3 — Moderate-Aggressive+
    {
        "name": "Long-Horizon Compounding",
        "description": "High-growth businesses with 7-10 year holding periods. Maximum compounding potential with patience.",
        "risk": "High", "suitability": "Moderate-Aggressive and above", "allocation_range": "30-50%", "horizon": "7-10+ years",
        "tier": 3,
    },
    {
        "name": "Private Markets Access",
        "description": "Pre-IPO opportunities, structured credit, and private equity with 3-7 year lock-in. Illiquidity premium.",
        "risk": "High", "suitability": "Moderate-Aggressive and above", "allocation_range": "10-20%", "horizon": "3-7 years",
        "tier": 3,
    },
    {
        "name": "Thematic & Sectoral Conviction",
        "description": "Concentrated bets on 2-3 structural themes with multi-year patience. High conviction required.",
        "risk": "Very High", "suitability": "Moderate-Aggressive and above", "allocation_range": "10-20%", "horizon": "5-10 years",
        "tier": 3,
    },
]

MEANING_APPROACHES = {
    "legacy": {
        "name": "Intergenerational Wealth Framework",
        "description": "Multi-decade, multi-generational compounding. 60-80% growth assets with 20+ year horizon. Designed to outlast you.",
        "risk": "Variable", "suitability": "Legacy-minded investors", "allocation_range": "60-80% growth", "horizon": "20+ years",
    },
    "security": {
        "name": "All-Weather Portfolio",
        "description": "Performs adequately in all market regimes — bull, bear, recession, inflation. Diversified across uncorrelated assets.",
        "risk": "Low-Moderate", "suitability": "Security-minded investors", "allocation_range": "Balanced", "horizon": "Evergreen",
    },
}


def get_suitable_approaches(composite: float, meaning: Optional[str], knowledge: Optional[str]) -> List[Dict]:
    """Filter approaches based on profile tier."""
    profile = get_profile_label(composite)
    profile_tiers = {
        "Conservative": 0,
        "Moderate-Conservative": 1,
        "Moderate": 2,
        "Moderate-Aggressive": 3,
        "Aggressive": 4,
    }
    max_tier = profile_tiers.get(profile["label"], 2)
    suitable = [a for a in APPROACHES if a["tier"] <= max_tier]

    # Add meaning-specific approach if applicable
    if meaning in MEANING_APPROACHES:
        knowledge_ok = knowledge in ("intermediate", "advanced", "expert")
        if meaning == "legacy" and knowledge_ok:
            suitable.append(MEANING_APPROACHES["legacy"])
        elif meaning == "security":
            suitable.append(MEANING_APPROACHES["security"])

    return suitable


# ─── Behavioral Flags ───

def compute_composite_flags(ctx, composite: float, dimensions: List[Dict]) -> List[Dict]:
    """Generate behavioral flags from composite analysis."""
    flags = []

    # Expectation-Fear Conflict
    if ctx.worst_fear == "fomo" and ctx.fear_impact in ("panic", "anxious"):
        flags.append({
            "type": "critical",
            "title": "Expectation-Fear Conflict",
            "explanation": "You fear missing out on gains (FOMO), but your emotional response to drawdowns is panic or high anxiety. This creates a dangerous cycle — chasing returns then panic-selling during corrections.",
            "action": "Start with conservative allocation. Gradually increase equity exposure only after surviving a real 10%+ drawdown without selling.",
        })

    # Unproven Under Stress
    if not ctx.equity_experience:
        flags.append({
            "type": "warning",
            "title": "Unproven Under Stress",
            "explanation": "You have no equity market experience through a major downturn. Your stated risk tolerance is theoretical and unvalidated. Many investors discover their true tolerance only during their first crash.",
            "action": "Begin with lower equity allocation than the model suggests. Use SIPs to build positions gradually. Your real risk profile will emerge after your first market correction.",
        })

    # Over-Concentrated
    concentration = ctx.wealth_concentration or 0
    if concentration > 60:
        flags.append({
            "type": "warning",
            "title": "Over-Concentrated Portfolio",
            "explanation": f"This investment represents {concentration:.0f}% of your total wealth. A major drawdown here affects your entire financial life, not just this portfolio.",
            "action": "Reduce concentration before increasing risk. Consider diversifying across multiple instruments and asset classes.",
        })

    # No Safety Net
    cash = ctx.existing_cash_savings or 0
    monthly = ctx.monthly_fixed_obligations or 0
    runway = cash / monthly if monthly > 0 else 24
    if runway < 6:
        flags.append({
            "type": "critical",
            "title": "Insufficient Safety Net",
            "explanation": f"You have only {runway:.0f} months of emergency reserves. A job loss, health crisis, or market downturn could force you to liquidate investments at the worst time.",
            "action": "Build emergency fund to 6-12 months before increasing equity allocation. This is more important than any investment return.",
        })

    return flags


# ─── Wisdom Quotes ───

def select_wisdom(ctx, composite: float, flags: List[Dict]) -> Dict:
    """Select contextual investment wisdom based on profile."""
    flag_titles = [f["title"] for f in flags]

    if "Expectation-Fear Conflict" in flag_titles:
        return {
            "quote": "The investor's chief problem — and even his worst enemy — is likely to be himself.",
            "author": "Benjamin Graham",
            "insight": "Your desire for returns and your fear of losses are pulling in opposite directions. Resolve this tension before deploying capital. The market will test both sides.",
        }
    if ctx.money_meaning == "security":
        return {
            "quote": "There are old investors and there are bold investors, but there are very few old bold investors.",
            "author": "Howard Marks",
            "insight": "Your instinct for protection is wise. Build a portfolio that lets you sleep at night. The best investment plan is one you can actually stick with through storms.",
        }
    if ctx.money_meaning == "freedom":
        return {
            "quote": "Wealth is the ability to fully experience life.",
            "author": "Henry David Thoreau",
            "insight": "Freedom requires a portfolio that generates optionality, not one that demands your constant attention. Invest in a way that frees your mind, not one that imprisons it.",
        }
    if ctx.money_meaning == "game" and "Unproven Under Stress" in flag_titles:
        return {
            "quote": "In order to win, you must first survive.",
            "author": "Warren Buffett",
            "insight": "The game of investing rewards those who stay in it longest. Before optimizing for returns, ensure your portfolio can survive bad years without forcing you to the sidelines.",
        }
    if ctx.money_meaning == "legacy":
        return {
            "quote": "Someone is sitting in the shade today because someone planted a tree a long time ago.",
            "author": "Warren Buffett",
            "insight": "Legacy building requires patience measured in decades, not quarters. The portfolio you build today should compound through market cycles your grandchildren haven't yet imagined.",
        }
    if "Unproven Under Stress" in flag_titles:
        return {
            "quote": "Experience is what you get when you didn't get what you wanted.",
            "author": "Howard Marks",
            "insight": "Your first real market crash will teach you more about yourself than any questionnaire. Start conservatively, learn from the experience, and adjust from a position of knowledge, not theory.",
        }
    # Default
    return {
        "quote": "The essence of investment management is the management of risks, not the management of returns.",
        "author": "Benjamin Graham",
        "insight": "Your risk profile shapes every recommendation in this report. Returns are the reward for bearing the right amount of risk — not too much, not too little.",
    }


# ─── Main Entry Point ───

def compute_comprehensive_report(
    ctx,
    game_scores: Optional[Dict] = None,
    behavioral_profile: Optional[Dict] = None,
    regime: Optional[Dict] = None,
) -> Dict:
    """Compute the full comprehensive assessment report.

    Args:
        ctx: InvestorFinancialContext SQLAlchemy object
        game_scores: Dict with composite_risk_score from BehavioralProfile
        behavioral_profile: Full behavioral profile data
        regime: Market regime data

    Returns:
        Complete report dict for frontend ComprehensiveReport component.
    """
    # 1. Score all 6 dimensions
    dim_financial = score_financial_capacity(ctx)
    dim_behavioral = score_behavioral_pattern(ctx, game_scores)
    dim_coherence = score_fear_coherence(ctx)
    dim_meaning = score_money_meaning(ctx)
    dim_knowledge = score_knowledge(ctx)
    dim_cycle = score_market_cycle(regime)

    dimensions = [dim_financial, dim_behavioral, dim_coherence, dim_meaning, dim_knowledge, dim_cycle]

    # 2. Composite score
    raw_composite = compute_composite(dimensions)

    # 3. Equity ceiling & constraints
    ceiling_data = compute_equity_ceiling(ctx, raw_composite)
    effective_composite = ceiling_data["effective_composite"]

    # 4. Profile label
    profile = get_profile_label(effective_composite)

    # 5. Allocation
    allocation = compute_allocation(effective_composite, ceiling_data["ceiling"])

    # 6. Liquidity x Drawdown matrix
    matrix = compute_matrix_position(ctx, dim_behavioral["score"], dim_coherence["score"])

    # 7. Investment approaches
    approaches = get_suitable_approaches(effective_composite, ctx.money_meaning, ctx.knowledge_level)

    # 8. Flags
    flags = compute_composite_flags(ctx, effective_composite, dimensions)

    # 9. Wisdom
    wisdom = select_wisdom(ctx, effective_composite, flags)

    # 10. Meaning reveal
    meaning_reveal = {
        "meaning": ctx.money_meaning,
        "label": MEANING_LABELS.get(ctx.money_meaning, "Not specified"),
        "description": MEANING_DESCRIPTIONS.get(ctx.money_meaning, ""),
    }

    return {
        "composite_score": effective_composite,
        "raw_composite": raw_composite,
        "profile": profile,
        "dimensions": dimensions,
        "meaning_reveal": meaning_reveal,
        "allocation": allocation,
        "matrix": matrix,
        "approaches": approaches,
        "flags": flags,
        "wisdom": wisdom,
        "equity_ceiling": ceiling_data,
        "behavioral_profile": behavioral_profile,
    }
