"""Gamified Assessment Engine — 4 behavioral games with contextual anchoring.

Game 1: Risk Tolerance (Multiplier Bisection) — 5 trials
Game 2: Loss Aversion (Lambda Ratio Bisection) — 5 trials
Game 3: Time Preference (Adjusting Delay) — 5 trials
Game 4: Herding Susceptibility (Knowledge-Aware Social Proof) — 3 scenarios x 2 phases

Amounts scale to investor's financial reality via an anchor amount (~3% of investable assets).
Bisection operates on multipliers/ratios, not absolute rupee amounts.
"""
import logging
import math
import statistics
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("beyond_risk.games_engine")

# ─── Anchor Amount System ───

DEFAULT_ANCHOR = 200000  # 2L fallback when no financial context
ANCHOR_FLOOR = 25000     # minimum 25K
ANCHOR_CAP = 50000000    # maximum 5Cr


def round_to_clean_amount(n: float) -> int:
    """Round to psychologically clean numbers for Indian currency."""
    n = int(n)
    if n < 100000:       # < 1L: round to nearest 5K
        return max(5000, round(n / 5000) * 5000)
    elif n < 1000000:    # 1L-10L: round to nearest 25K
        return round(n / 25000) * 25000
    elif n < 10000000:   # 10L-1Cr: round to nearest 1L
        return round(n / 100000) * 100000
    else:                # > 1Cr: round to nearest 5L
        return round(n / 500000) * 500000


def compute_anchor_amount(financial_context) -> int:
    """Compute a psychologically meaningful base amount from investor's financial context.

    Target: ~3% of investable assets. Enough to feel meaningful
    but not so large it triggers irrational panic.
    """
    if financial_context and financial_context.total_investable_assets:
        raw = financial_context.total_investable_assets * 100000 * 0.03  # lakhs to INR, then 3%
    elif financial_context and financial_context.annual_income:
        raw = financial_context.annual_income * 100000 * 0.10  # 10% of annual income
    else:
        raw = DEFAULT_ANCHOR

    clamped = max(ANCHOR_FLOOR, min(raw, ANCHOR_CAP))
    return round_to_clean_amount(clamped)


# ─── Game 1: Risk Tolerance (Multiplier Bisection) ───

RISK_MULTIPLIER_RANGE = [1.2, 6.0]  # gamble = anchor x multiplier, 50% chance
RISK_TRIALS = 5


def risk_tolerance_first_stimulus(anchor: int) -> dict:
    """First stimulus: guaranteed=anchor vs gamble at midpoint multiplier."""
    mid_mult = (RISK_MULTIPLIER_RANGE[0] + RISK_MULTIPLIER_RANGE[1]) / 2
    return {
        "guaranteed": anchor,
        "gamble_win": round_to_clean_amount(anchor * mid_mult),
        "gamble_prob": 0.5,
        "multiplier": round(mid_mult, 2),
        "trial": 1,
    }


def risk_tolerance_next(
    trial_num: int, choice: str, current_range: List[float], anchor: int
) -> Tuple[Optional[dict], List[float]]:
    """Bisect the multiplier range based on choice."""
    mid = (current_range[0] + current_range[1]) / 2
    if choice == "gamble":
        new_range = [mid, current_range[1]]  # risk tolerant — needs less premium
    else:
        new_range = [current_range[0], mid]  # risk averse — reduce gamble

    if trial_num >= RISK_TRIALS:
        return None, new_range

    new_mid = (new_range[0] + new_range[1]) / 2
    return {
        "guaranteed": anchor,
        "gamble_win": round_to_clean_amount(anchor * new_mid),
        "gamble_prob": 0.5,
        "multiplier": round(new_mid, 2),
        "trial": trial_num + 1,
    }, new_range


def risk_tolerance_score(final_range: List[float]) -> Tuple[float, float]:
    """Convert final multiplier range to 0-100 risk tolerance score.

    Lower multiplier needed to gamble = MORE risk tolerant.
    1.2x → ~95, 2.0x → ~60, 4.0x+ → ~15
    """
    multiplier = (final_range[0] + final_range[1]) / 2
    score = max(0, min(100, round(110 - 25 * multiplier)))
    sigma = 12.0
    return float(score), sigma


# ─── Game 2: Loss Aversion (Lambda Ratio Bisection) ───

LOSS_LAMBDA_RANGE = [0.25, 4.0]  # loss = gain * ratio; bisect the ratio
LOSS_TRIALS = 5


def loss_aversion_first_stimulus(anchor: int) -> dict:
    """First stimulus: gain = anchor/2, loss = gain * midpoint_ratio."""
    gain = round_to_clean_amount(anchor * 0.5)
    mid_ratio = (LOSS_LAMBDA_RANGE[0] + LOSS_LAMBDA_RANGE[1]) / 2
    loss = round_to_clean_amount(gain * mid_ratio)
    return {
        "gain": gain,
        "loss": loss,
        "probability": 0.5,
        "lambda_ratio": round(mid_ratio, 3),
        "trial": 1,
    }


def loss_aversion_next(
    trial_num: int, choice: str, current_range: List[float], anchor: int
) -> Tuple[Optional[dict], List[float]]:
    """Bisect the lambda ratio range based on accept/reject."""
    mid = (current_range[0] + current_range[1]) / 2
    if choice == "accept":
        new_range = [mid, current_range[1]]  # tolerant of loss, try higher ratio
    else:
        new_range = [current_range[0], mid]  # averse, try lower ratio

    if trial_num >= LOSS_TRIALS:
        return None, new_range

    gain = round_to_clean_amount(anchor * 0.5)
    new_mid = (new_range[0] + new_range[1]) / 2
    loss = round_to_clean_amount(gain * new_mid)
    return {
        "gain": gain,
        "loss": loss,
        "probability": 0.5,
        "lambda_ratio": round(new_mid, 3),
        "trial": trial_num + 1,
    }, new_range


def loss_aversion_score(final_range: List[float]) -> Tuple[float, float, float]:
    """Returns (lambda_raw, score_0_100, sigma).

    final_range contains the bisection ratio (loss/gain proportion).
    KT lambda = 1/ratio (how much more painful losses are vs gains).
    lambda ~0.5 → score ~10, lambda ~2.25 → ~50, lambda ~4.0 → ~95
    """
    ratio = (final_range[0] + final_range[1]) / 2
    ratio = max(0.1, ratio)  # avoid div-by-zero
    lambda_raw = 1.0 / ratio  # KT loss aversion coefficient

    score = max(0, min(100, round(math.log(max(lambda_raw, 0.1)) / math.log(4.0) * 100)))
    sigma = 10.0
    return round(lambda_raw, 3), float(score), sigma


# ─── Game 3: Time Preference (Adjusting Delay) ───

DELAY_SEQUENCE = [1, 7, 30, 180, 365, 1095, 3650, 9125]
DELAY_LABELS = ["1 day", "1 week", "1 month", "6 months", "1 year", "3 years", "10 years", "25 years"]
TIME_TRIALS = 5


def time_preference_first_stimulus(anchor: int) -> dict:
    """First stimulus: immediate=anchor, delayed=anchor*2, at midpoint delay."""
    idx = (0 + len(DELAY_SEQUENCE) - 1) // 2
    return {
        "immediate": anchor,
        "delayed": round_to_clean_amount(anchor * 2),
        "delay_days": DELAY_SEQUENCE[idx],
        "delay_label": DELAY_LABELS[idx],
        "trial": 1,
    }


def time_preference_next(
    trial_num: int, choice: str, current_range: List[int], anchor: int
) -> Tuple[Optional[dict], List[int]]:
    """Bisect the delay index. Accepts both 'now'/'immediate' as impatient."""
    idx = (current_range[0] + current_range[1]) // 2
    if choice in ("immediate", "now"):
        new_range = [current_range[0], idx]  # impatient, try shorter delay
    else:
        new_range = [idx, current_range[1]]  # patient, try longer delay

    if trial_num >= TIME_TRIALS:
        return None, new_range

    new_idx = (new_range[0] + new_range[1]) // 2
    new_idx = max(0, min(len(DELAY_SEQUENCE) - 1, new_idx))
    return {
        "immediate": anchor,
        "delayed": round_to_clean_amount(anchor * 2),
        "delay_days": DELAY_SEQUENCE[new_idx],
        "delay_label": DELAY_LABELS[new_idx],
        "trial": trial_num + 1,
    }, new_range


def time_preference_score(final_range: List[int]) -> Tuple[float, float, float]:
    """Returns (k_discount, patience_score_0_100, sigma)."""
    idx = (final_range[0] + final_range[1]) // 2
    idx = max(0, min(len(DELAY_SEQUENCE) - 1, idx))
    ed50_days = DELAY_SEQUENCE[idx]
    k = 1.0 / ed50_days if ed50_days > 0 else 1.0

    # high k = impatient = low patience score
    patience_score = max(0, min(100, round(90 - math.log10(max(k, 1e-6)) * 20)))
    sigma = 14.0
    return round(k, 6), float(patience_score), sigma


# ─── Game 4: Herding Susceptibility (Knowledge-Aware) ───

HERDING_SCENARIOS_BASIC = [
    {
        "id": 1,
        "description": "Choose between two equity mutual funds for a 5-year investment",
        "option_a": {"name": "Fund Alpha", "return_3y": "14.2%", "risk": "Moderate", "expense": "1.8%"},
        "option_b": {"name": "Fund Beta", "return_3y": "11.8%", "risk": "Low-Moderate", "expense": "0.9%"},
        "social_signal": "87% of investors chose Fund Alpha this month",
        "rational_choice": "B",
    },
    {
        "id": 2,
        "description": "Markets have fallen 15% this month. What do you do with your equity SIPs?",
        "option_a": {"name": "Continue SIPs as planned"},
        "option_b": {"name": "Pause SIPs and wait for stability"},
        "social_signal": "73% of investors have paused their SIPs",
        "rational_choice": "A",
    },
    {
        "id": 3,
        "description": "A new NFO from a trending AMC vs an established fund",
        "option_a": {"name": "New NFO (no track record)", "category": "Thematic - AI & Robotics"},
        "option_b": {"name": "Established fund (8yr track record)", "category": "Flexi Cap"},
        "social_signal": "This NFO collected \u20b95,200 Cr in 3 days",
        "rational_choice": "B",
    },
]

HERDING_SCENARIOS_ADVANCED = [
    {
        "id": 1,
        "description": "Choose a PMS strategy for your \u20b91 Cr+ allocation",
        "option_a": {"name": "Momentum Alpha PMS", "return_3y": "22.4%", "drawdown": "-18%", "fee": "2.5% + 20% profit share"},
        "option_b": {"name": "Smart Beta PMS", "return_3y": "16.8%", "drawdown": "-11%", "fee": "1.5% flat"},
        "social_signal": "Momentum Alpha PMS topped the PMS rankings for 3 consecutive quarters",
        "rational_choice": "B",
    },
    {
        "id": 2,
        "description": "Allocating 15% of portfolio internationally. Which approach?",
        "option_a": {"name": "Emerging Markets Fund", "exposure": "China, Vietnam, Indonesia", "volatility": "High"},
        "option_b": {"name": "Domestic Large Cap Index", "exposure": "NIFTY 50 top weights", "volatility": "Moderate"},
        "social_signal": "FIIs have increased EM allocation by 40% this quarter",
        "rational_choice": "B",
    },
    {
        "id": 3,
        "description": "Alternative investment for portfolio diversification",
        "option_a": {"name": "Category II AIF", "lock_in": "3 years", "min_ticket": "\u20b91 Cr", "target_return": "18-22%"},
        "option_b": {"name": "REIT (Embassy/Brookfield)", "lock_in": "None", "min_ticket": "\u20b915,000", "target_return": "8-12% + capital appreciation"},
        "social_signal": "AIF inflows crossed \u20b92.5 lakh Cr this year, up 65% YoY",
        "rational_choice": "B",
    },
]


def _get_herding_scenarios(knowledge_level: Optional[str] = None) -> List[dict]:
    """Select scenario pool based on investor knowledge level."""
    if knowledge_level in ("advanced", "expert"):
        return HERDING_SCENARIOS_ADVANCED
    return HERDING_SCENARIOS_BASIC


def herding_get_scenarios(knowledge_level: Optional[str] = None) -> dict:
    """Return scenarios for phase 1 (without social signal)."""
    scenarios = _get_herding_scenarios(knowledge_level)
    return {
        "phase": "without_signal",
        "scenarios": [
            {
                "id": s["id"],
                "description": s["description"],
                "option_a": s["option_a"],
                "option_b": s["option_b"],
            }
            for s in scenarios
        ],
    }


def herding_get_with_signal(knowledge_level: Optional[str] = None) -> dict:
    """Return scenarios WITH social signal (phase 2)."""
    scenarios = _get_herding_scenarios(knowledge_level)
    return {
        "phase": "with_signal",
        "scenarios": [
            {
                "id": s["id"],
                "description": s["description"],
                "option_a": s["option_a"],
                "option_b": s["option_b"],
                "social_signal": s["social_signal"],
            }
            for s in scenarios
        ],
    }


def herding_score(
    phase1_choices: List[str], phase2_choices: List[str],
    knowledge_level: Optional[str] = None,
) -> Tuple[float, float, float]:
    """Compute herding index from before/after social signal choices.

    Returns (herding_index_0_1, herding_score_0_100, sigma).
    """
    scenarios = _get_herding_scenarios(knowledge_level)
    shifts_toward_social = 0
    for i in range(len(scenarios)):
        if i < len(phase1_choices) and i < len(phase2_choices):
            if phase1_choices[i] != phase2_choices[i]:
                # Social signal always favors option A in our design
                if phase2_choices[i] == "A":
                    shifts_toward_social += 1

    herding_index = shifts_toward_social / len(scenarios)
    score = round(herding_index * 100)
    sigma = 20.0  # inherently uncertain with only 3 scenarios
    return round(herding_index, 3), float(score), sigma


# ─── Session Quality & Score Aggregation ───

def validate_response_time(response_time_ms: int) -> dict:
    """Classify response time quality."""
    if response_time_ms < 300:
        return {"quality": "random_click", "weight": 0.0, "flag": "Response too fast — likely random"}
    elif response_time_ms < 1500:
        return {"quality": "strong_preference", "weight": 1.2, "flag": None}
    elif response_time_ms <= 5000:
        return {"quality": "normal", "weight": 1.0, "flag": None}
    elif response_time_ms <= 12000:
        return {"quality": "uncertain", "weight": 0.8, "flag": None}
    else:
        return {"quality": "distracted", "weight": 0.5, "flag": "Response very slow — possible distraction"}


def compute_session_quality(response_times: List[int]) -> Tuple[float, int]:
    """Compute session quality score and median response time.

    Returns (quality_score_0_100, median_rt_ms).
    """
    if not response_times:
        return 50.0, 0

    median_rt = int(statistics.median(response_times))
    random_clicks = sum(1 for rt in response_times if rt < 300)

    # Quality factors
    random_penalty = random_clicks / len(response_times) * 40
    rushing_penalty = 20 if median_rt < 800 else 0
    base_score = 100 - random_penalty - rushing_penalty

    return round(max(0, min(100, base_score)), 1), median_rt


def compute_game_session_scores(
    risk_range: List[float],
    loss_range: List[float],
    time_range: List[int],
    herding_p1: List[str],
    herding_p2: List[str],
    response_times: List[int],
    knowledge_level: Optional[str] = None,
) -> Dict:
    """Compute all scores for a completed game session."""
    rt_score, rt_sigma = risk_tolerance_score(risk_range)
    la_lambda, la_score, la_sigma = loss_aversion_score(loss_range)
    tp_k, tp_score, tp_sigma = time_preference_score(time_range)
    h_index, h_score, h_sigma = herding_score(herding_p1, herding_p2, knowledge_level)
    quality, median_rt = compute_session_quality(response_times)

    # Widen sigmas if session quality is low
    if quality < 40:
        rt_sigma *= 1.5
        la_sigma *= 1.5
        tp_sigma *= 1.5
        h_sigma *= 1.5

    return {
        "risk_tolerance_score": rt_score,
        "risk_tolerance_sigma": round(rt_sigma, 2),
        "loss_aversion_lambda": la_lambda,
        "loss_aversion_score": la_score,
        "loss_aversion_sigma": round(la_sigma, 2),
        "time_preference_k": tp_k,
        "time_preference_score": tp_score,
        "time_preference_sigma": round(tp_sigma, 2),
        "herding_index": h_index,
        "herding_score": h_score,
        "herding_sigma": round(h_sigma, 2),
        "session_quality": quality,
        "median_response_time_ms": median_rt,
    }


def map_game_scores_to_traits(scores: Dict) -> Dict[str, Tuple[float, float]]:
    """Map game scores to the 10-trait model for Bayesian fusion.

    Returns {trait_name: (score, sigma)} for traits that have game-derived data.
    """
    return {
        "loss_aversion": (scores["loss_aversion_score"], scores["loss_aversion_sigma"]),
        "horizon_tolerance": (scores["time_preference_score"], scores["time_preference_sigma"]),
        "behavioral_stability": (scores["risk_tolerance_score"], scores["risk_tolerance_sigma"]),
        "emotional_volatility": (max(0, 100 - scores["risk_tolerance_score"]), scores["risk_tolerance_sigma"]),
        "decision_confidence": (scores["risk_tolerance_score"], scores["risk_tolerance_sigma"] * 1.2),
        # Herding maps to ambiguity tolerance (inverse)
        "ambiguity_tolerance": (max(0, 100 - scores["herding_score"]), scores["herding_sigma"]),
    }
