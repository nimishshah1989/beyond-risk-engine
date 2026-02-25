"""
Scoring Engine — computes Investor Risk Blueprint from responses.
Uses simplified Item Response Theory (weighted Bayesian estimation).
"""
from typing import Dict, List, Optional

TRAIT_IDS = [
    "loss_aversion", "horizon_tolerance", "liquidity_sensitivity",
    "behavioral_stability", "ambiguity_tolerance", "regret_sensitivity",
    "leverage_comfort", "goal_rigidity", "emotional_volatility", "decision_confidence"
]


def compute_trait_scores(
    responses: List[dict],
    questions: List[dict],
) -> Dict:
    """
    Compute trait scores from responses using IRT-weighted estimation.
    
    For each trait:
      score = Σ(option_score × trait_weight × discrimination) / Σ(trait_weight × discrimination)
    
    This is a weighted average where questions with higher discrimination
    (better at separating high/low trait individuals) count more.
    """
    trait_accum = {t: {"weighted_sum": 0.0, "weight_total": 0.0, "count": 0} for t in TRAIT_IDS}

    for resp in responses:
        q = next((q for q in questions if q["code"] == resp["question_code"]), None)
        if not q or resp.get("option_index") is None:
            continue

        option = q["options"][resp["option_index"]]
        trait_weights = q["trait_weights"]
        discrimination = q.get("discrimination", 1.5)

        for trait_id, weight in trait_weights.items():
            if trait_id in option.get("scores", {}):
                score_val = option["scores"][trait_id]
                effective_weight = weight * discrimination
                trait_accum[trait_id]["weighted_sum"] += score_val * effective_weight
                trait_accum[trait_id]["weight_total"] += effective_weight
                trait_accum[trait_id]["count"] += 1

    trait_scores = {}
    confidence_scores = {}

    for trait_id in TRAIT_IDS:
        acc = trait_accum[trait_id]
        if acc["weight_total"] > 0:
            raw = acc["weighted_sum"] / acc["weight_total"]
            trait_scores[trait_id] = round(min(100, max(0, raw)))
            # Confidence increases with more data points
            confidence_scores[trait_id] = min(95, round(40 + acc["count"] * 15))
        else:
            trait_scores[trait_id] = 50  # Prior
            confidence_scores[trait_id] = 10

    return {
        "trait_scores": trait_scores,
        "confidence_scores": confidence_scores,
    }


def compute_behavioral_flags(traits: Dict[str, int]) -> List[Dict]:
    """Detect behavioral patterns, contradictions, and risk indicators."""
    flags = []

    if traits.get("loss_aversion", 0) > 75 and traits.get("emotional_volatility", 0) > 65:
        flags.append({
            "type": "critical",
            "title": "Flight Risk — Loss Aversion + Emotional Volatility",
            "msg": "High loss aversion combined with emotional volatility. This investor is at significant risk of panic-selling during drawdowns.",
            "action": "Implement proactive communication protocol — call within 24hrs of any 5%+ market drop. Consider downside-protected structures as core holdings."
        })

    if traits.get("behavioral_stability", 0) < 35:
        flags.append({
            "type": "warning",
            "title": "Inconsistent Decision Making",
            "msg": "Low behavioral stability indicates investment decisions may change frequently under pressure.",
            "action": "Use automated investment mechanisms (SIPs, auto-rebalancing). Reduce discretionary decision points. Schedule regular check-ins."
        })

    if traits.get("leverage_comfort", 0) > 70 and traits.get("loss_aversion", 0) > 60:
        flags.append({
            "type": "warning",
            "title": "Leverage-Loss Contradiction",
            "msg": "Comfortable with leverage in theory but highly sensitive to losses. May panic specifically in leveraged losing positions.",
            "action": "Test with very small leveraged allocations first. This client will likely want immediate exit if losses occur."
        })

    if traits.get("regret_sensitivity", 0) > 75:
        flags.append({
            "type": "warning",
            "title": "Disposition Effect Risk",
            "msg": "High regret sensitivity creates tendency to hold losers too long and sell winners too early.",
            "action": "Implement systematic rebalancing with pre-agreed rules. Use trailing stop-losses. Give ONE clear recommendation, not multiple options."
        })

    if traits.get("emotional_volatility", 0) > 80:
        flags.append({
            "type": "critical",
            "title": "High Emotional Volatility — Priority Alert",
            "msg": "Very high emotional volatility is the strongest predictor of panic selling and permanent capital loss.",
            "action": "PRIORITY: Reduce portfolio visibility (quarterly only), implement 'call before you sell' protocol, ensure allocation survives a 30% crash."
        })

    if traits.get("goal_rigidity", 0) > 80 and traits.get("horizon_tolerance", 0) < 40:
        flags.append({
            "type": "info",
            "title": "Rigid Goals + Short Patience",
            "msg": "Rigid goals with short patience window. Needs products with defined maturity dates.",
            "action": "Use target-date funds, FMPs, or structured products with maturity. Show goal completion % in every report."
        })

    if traits.get("liquidity_sensitivity", 0) > 80:
        flags.append({
            "type": "info",
            "title": "Extreme Liquidity Preference",
            "msg": "Even excellent returns won't compensate for the anxiety of locked capital.",
            "action": "Avoid all closed-ended products. Use open-ended funds exclusively. Liquid allocation should be larger than mathematically necessary."
        })

    if traits.get("ambiguity_tolerance", 0) < 30 and traits.get("decision_confidence", 0) > 70:
        flags.append({
            "type": "info",
            "title": "Research-Dependent Confidence",
            "msg": "High confidence but needs extensive information. Makes strong decisions but only after thorough research.",
            "action": "Provide comprehensive research reports. This client will act decisively once convinced but needs extensive evidence first."
        })

    return flags


def compute_stress_prediction(traits: Dict[str, int]) -> Dict:
    """Predict investor behavior during a 20%+ market correction."""
    drawdown_tolerance = round(
        100 - (
            traits.get("loss_aversion", 50) * 0.4 +
            traits.get("emotional_volatility", 50) * 0.35 +
            (100 - traits.get("behavioral_stability", 50)) * 0.25
        )
    )

    ev = traits.get("emotional_volatility", 50)
    la = traits.get("loss_aversion", 50)
    bs = traits.get("behavioral_stability", 50)
    rs = traits.get("regret_sensitivity", 50)
    dc = traits.get("decision_confidence", 50)

    if ev > 75 and la > 70:
        label, color = "FLIGHT RISK", "critical"
        text = "Highly likely to redeem during a >15% drawdown. Pre-emptive communication essential. Consider downside-protected structures."
    elif bs > 70 and la < 40:
        label, color = "RESILIENT", "positive"
        text = "Will likely hold through severe corrections and may increase allocation. Ideal for contrarian strategies."
    elif rs > 70 and dc < 40:
        label, color = "PARALYSIS RISK", "warning"
        text = "May freeze during market stress — neither buying nor selling. Needs direct advisor intervention with specific action steps."
    elif ev > 60 and bs < 45:
        label, color = "REACTIVE", "warning"
        text = "Likely to make impulsive changes during prolonged sideways markets. Reduce discretionary decision points."
    else:
        label, color = "MODERATE", "neutral"
        text = "Expected typical anxiety during corrections but unlikely to make drastic changes with proper communication."

    # Scenario probabilities
    scenarios = {
        "panic_sell": min(95, round(ev * 0.6 + la * 0.3)),
        "call_advisor": min(95, round((100 - dc) * 0.5 + ev * 0.3 + 20)),
        "hold_through": min(95, round(bs * 0.5 + traits.get("horizon_tolerance", 50) * 0.3)),
        "buy_more": min(95, round((100 - la) * 0.4 + dc * 0.3)),
    }

    return {
        "label": label,
        "severity": color,
        "text": text,
        "drawdown_tolerance": drawdown_tolerance,
        "scenario_probabilities": scenarios,
    }


def compute_liquidity_buffer(traits: Dict[str, int]) -> str:
    ls = traits.get("liquidity_sensitivity", 50)
    if ls > 75:
        return "12+ months"
    elif ls > 50:
        return "6-9 months"
    elif ls > 25:
        return "3-6 months"
    else:
        return "1-3 months"
