"""Bayesian fusion — Normal-Normal conjugate updating for dual-path behavioral profiling."""
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("beyond_risk.bayesian_fusion")

# Which transaction score informs which trait
TRAIT_TO_TRANSACTION = {
    "loss_aversion": "disposition_effect",
    "behavioral_stability": "sip_discipline",
    "emotional_volatility": "panic_score",
    "regret_sensitivity": "disposition_effect",
    "horizon_tolerance": "sip_discipline",
    "liquidity_sensitivity": "overtrading",
    "decision_confidence": None,  # no transaction equivalent
    "ambiguity_tolerance": None,
    "leverage_comfort": None,
    "goal_rigidity": None,
}

TRAIT_IDS = [
    "loss_aversion", "horizon_tolerance", "liquidity_sensitivity",
    "behavioral_stability", "ambiguity_tolerance", "regret_sensitivity",
    "leverage_comfort", "goal_rigidity", "emotional_volatility", "decision_confidence",
]


def bayesian_update(mu_prior: float, sigma_prior: float,
                    mu_observed: float, sigma_observed: float) -> Tuple[float, float]:
    """Normal-Normal conjugate update.

    Given a prior N(mu_prior, sigma_prior^2) and observation N(mu_observed, sigma_observed^2),
    returns posterior (mu_post, sigma_post).

    Narrower sigma (more confident) data naturally dominates — this is why
    transaction data (narrow CI from many data points) overrides questionnaire data
    (wide CI from few questions).
    """
    if sigma_prior <= 0:
        sigma_prior = 0.01
    if sigma_observed <= 0:
        sigma_observed = 0.01

    prec_prior = 1.0 / (sigma_prior ** 2)
    prec_obs = 1.0 / (sigma_observed ** 2)
    prec_post = prec_prior + prec_obs

    mu_post = (prec_prior * mu_prior + prec_obs * mu_observed) / prec_post
    sigma_post = np.sqrt(1.0 / prec_post)

    return round(float(mu_post), 2), round(float(sigma_post), 2)


def determine_overall_source(psychometric: Optional[Dict], transaction: Optional[Dict]) -> str:
    """Determine the data_sources label for the profile."""
    has_psych = psychometric is not None and len(psychometric) > 0
    has_txn = transaction is not None and len(transaction) > 0

    if has_psych and has_txn:
        return "FUSED"
    elif has_psych:
        return "PSYCHOMETRIC_ONLY"
    elif has_txn:
        return "TRANSACTION_ONLY"
    return "NONE"


def fuse_profiles(
    psychometric: Optional[Dict[str, Tuple[float, float]]],
    transaction: Optional[Dict[str, Tuple[float, float]]],
) -> Dict:
    """Fuse psychometric and transaction profiles using Bayesian updating.

    Args:
        psychometric: {trait_name: (score, sigma)} from games/questionnaire
        transaction: {metric_name: (score, sigma)} from transaction scoring

    Returns:
        Dict with per-trait results including score, CI, source, plus say-do gap analysis.
    """
    result = {}
    max_gap = 0.0
    gap_details = {}

    for trait in TRAIT_IDS:
        txn_key = TRAIT_TO_TRANSACTION.get(trait)
        psych = psychometric.get(trait) if psychometric else None
        txn = transaction.get(txn_key) if (transaction and txn_key) else None

        if psych and txn:
            mu, sigma = bayesian_update(psych[0], psych[1], txn[0], txn[1])
            source = "FUSED"
            gap = abs(psych[0] - txn[0])
            gap_details[trait] = {
                "stated": round(psych[0], 1),
                "revealed": round(txn[0], 1),
                "gap": round(gap, 1),
            }
            max_gap = max(max_gap, gap)
        elif psych:
            mu, sigma = psych[0], psych[1]
            source = "PSYCHOMETRIC_ONLY"
        elif txn:
            mu, sigma = txn[0], txn[1]
            source = "TRANSACTION_ONLY"
        else:
            mu, sigma = 50.0, 25.0
            source = "DEFAULT"

        ci_lower = max(0, round(mu - 1.96 * sigma, 1))
        ci_upper = min(100, round(mu + 1.96 * sigma, 1))

        result[trait] = {
            "score": round(mu),
            "sigma": round(sigma, 2),
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "source": source,
        }

    result["_say_do_gap"] = round(max_gap, 1)
    result["_say_do_details"] = gap_details
    result["_data_sources"] = determine_overall_source(psychometric, transaction)

    return result


def compute_composite_risk_score(profile_traits: Dict) -> float:
    """Compute a single composite risk score from the 10-trait profile.

    Higher score = more risk-tolerant overall.
    Weights reflect which traits matter most for risk allocation decisions.
    """
    weights = {
        "loss_aversion": -0.20,       # high LA = lower risk tolerance (negative)
        "horizon_tolerance": 0.15,     # long horizon = more risk capacity
        "liquidity_sensitivity": -0.10, # high LS = needs liquidity = less risk
        "behavioral_stability": 0.15,   # stable = can handle risk
        "ambiguity_tolerance": 0.10,    # tolerates uncertainty
        "regret_sensitivity": -0.08,    # high regret = less risk
        "leverage_comfort": 0.07,       # comfortable with leverage
        "goal_rigidity": -0.05,         # rigid goals = needs certainty
        "emotional_volatility": -0.15,  # volatile emotions = dangerous with risk
        "decision_confidence": 0.05,    # confident decisions
    }

    weighted_sum = 0.0
    for trait, weight in weights.items():
        trait_data = profile_traits.get(trait, {})
        score = trait_data.get("score", 50) if isinstance(trait_data, dict) else 50
        # For negative weights: high trait score REDUCES composite
        # For positive weights: high trait score INCREASES composite
        if weight < 0:
            weighted_sum += (100 - score) * abs(weight)
        else:
            weighted_sum += score * weight

    return round(max(0, min(100, weighted_sum)), 1)


def generate_say_do_alerts(gap_details: Dict, threshold: float = 20.0) -> List[Dict]:
    """Generate advisor alerts when stated vs revealed behavior diverges significantly.

    threshold: minimum gap to trigger an alert (default 20 points)
    """
    alerts = []
    trait_labels = {
        "loss_aversion": "Risk Tolerance",
        "behavioral_stability": "Behavioral Stability",
        "emotional_volatility": "Emotional Control",
        "regret_sensitivity": "Regret Sensitivity",
        "horizon_tolerance": "Investment Patience",
        "liquidity_sensitivity": "Liquidity Need",
    }

    for trait, detail in gap_details.items():
        if detail["gap"] >= threshold:
            label = trait_labels.get(trait, trait.replace("_", " ").title())
            direction = "higher" if detail["stated"] > detail["revealed"] else "lower"

            alerts.append({
                "type": "warning" if detail["gap"] < 30 else "critical",
                "title": f"Say-Do Gap: {label}",
                "msg": (
                    f"Investor scored {detail['stated']:.0f} on {label} (assessment) "
                    f"but actual trading shows {direction} behavior (transaction score: {detail['revealed']:.0f}). "
                    f"Gap of {detail['gap']:.0f} points."
                ),
                "action": (
                    f"Calibrate allocation to revealed preference ({detail['revealed']:.0f}), "
                    f"not stated preference ({detail['stated']:.0f}). "
                    f"Discuss this divergence with the investor."
                ),
                "trait": trait,
                "gap": detail["gap"],
            })

    return sorted(alerts, key=lambda a: a["gap"], reverse=True)
