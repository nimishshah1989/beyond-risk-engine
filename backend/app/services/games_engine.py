"""Gamified Assessment Engine — 4 behavioral games, 19 trials total (~2.5 minutes).

Game 1: Risk Tolerance (Falk GPS Staircase) — 5 trials
Game 2: Loss Aversion (Adaptive Bisection) — 6 trials
Game 3: Time Preference (Koffarnus Adjusting Delay) — 5 trials
Game 4: Herding Susceptibility (Social Proof Shift) — 3 scenarios × 2 phases
"""
import logging
import math
import statistics
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("beyond_risk.games_engine")

# ─── Game 1: Risk Tolerance (Falk GPS Staircase) ───

RISK_GUARANTEED = 50000
RISK_GAMBLE_RANGE = [60000, 300000]
RISK_TRIALS = 5


def risk_tolerance_first_stimulus() -> dict:
    """Get the first stimulus for the risk tolerance game."""
    mid = (RISK_GAMBLE_RANGE[0] + RISK_GAMBLE_RANGE[1]) / 2
    return {
        "guaranteed": RISK_GUARANTEED,
        "gamble_win": round(mid),
        "gamble_prob": 0.5,
        "trial": 1,
    }


def risk_tolerance_next(trial_num: int, choice: str, current_range: List[float]) -> Tuple[Optional[dict], List[float]]:
    """Process response and return next stimulus (or None if done)."""
    mid = (current_range[0] + current_range[1]) / 2
    if choice == "gamble":
        new_range = [mid, current_range[1]]  # more risk tolerant — increase gamble
    else:
        new_range = [current_range[0], mid]  # less risk tolerant — decrease gamble

    if trial_num >= RISK_TRIALS:
        return None, new_range

    new_mid = (new_range[0] + new_range[1]) / 2
    return {
        "guaranteed": RISK_GUARANTEED,
        "gamble_win": round(new_mid),
        "gamble_prob": 0.5,
        "trial": trial_num + 1,
    }, new_range


def risk_tolerance_score(final_range: List[float]) -> Tuple[float, float]:
    """Convert final gamble range to 0-100 risk tolerance score.

    Lower gamble_win needed to take gamble = MORE risk tolerant.
    """
    mid = (final_range[0] + final_range[1]) / 2
    ce_ratio = RISK_GUARANTEED / mid  # certainty equivalent ratio
    score = max(0, min(100, round((1 - ce_ratio) * 125 + 15)))
    sigma = 12.0
    return float(score), sigma


# ─── Game 2: Loss Aversion (Adaptive Bisection) ───

LOSS_GAIN = 20000
LOSS_RANGE = [5000, 40000]
LOSS_TRIALS = 6


def loss_aversion_first_stimulus() -> dict:
    mid = round((LOSS_RANGE[0] + LOSS_RANGE[1]) / 2)
    return {
        "gain": LOSS_GAIN,
        "loss": mid,
        "probability": 0.5,
        "trial": 1,
    }


def loss_aversion_next(trial_num: int, choice: str, current_range: List[float]) -> Tuple[Optional[dict], List[float]]:
    mid = (current_range[0] + current_range[1]) / 2
    if choice == "accept":
        new_range = [mid, current_range[1]]  # tolerant, try higher loss
    else:
        new_range = [current_range[0], mid]  # averse, try lower loss

    if trial_num >= LOSS_TRIALS:
        return None, new_range

    new_mid = round((new_range[0] + new_range[1]) / 2)
    return {
        "gain": LOSS_GAIN,
        "loss": new_mid,
        "probability": 0.5,
        "trial": trial_num + 1,
    }, new_range


def loss_aversion_score(final_range: List[float]) -> Tuple[float, float, float]:
    """Returns (lambda_raw, score_0_100, sigma)."""
    switching_loss = (final_range[0] + final_range[1]) / 2
    lambda_raw = LOSS_GAIN / switching_loss if switching_loss > 0 else 2.25

    # lambda ~1.0 = low loss aversion (~20), ~2.25 = average (~50), ~4.0+ = extreme (~95)
    score = max(0, min(100, round((lambda_raw - 0.5) / 4.0 * 100)))
    sigma = 10.0
    return round(lambda_raw, 3), float(score), sigma


# ─── Game 3: Time Preference (Koffarnus Adjusting Delay) ───

TIME_IMMEDIATE = 50000
TIME_DELAYED = 100000
DELAY_SEQUENCE = [1, 7, 30, 180, 365, 1095, 3650, 9125]
DELAY_LABELS = ["1 day", "1 week", "1 month", "6 months", "1 year", "3 years", "10 years", "25 years"]
TIME_TRIALS = 5


def time_preference_first_stimulus() -> dict:
    idx = (0 + len(DELAY_SEQUENCE) - 1) // 2
    return {
        "immediate": TIME_IMMEDIATE,
        "delayed": TIME_DELAYED,
        "delay_days": DELAY_SEQUENCE[idx],
        "delay_label": DELAY_LABELS[idx],
        "trial": 1,
    }


def time_preference_next(trial_num: int, choice: str, current_range: List[int]) -> Tuple[Optional[dict], List[int]]:
    idx = (current_range[0] + current_range[1]) // 2
    if choice == "immediate":
        new_range = [current_range[0], idx]  # impatient, try shorter delay
    else:
        new_range = [idx, current_range[1]]  # patient, try longer delay

    if trial_num >= TIME_TRIALS:
        return None, new_range

    new_idx = (new_range[0] + new_range[1]) // 2
    new_idx = max(0, min(len(DELAY_SEQUENCE) - 1, new_idx))
    return {
        "immediate": TIME_IMMEDIATE,
        "delayed": TIME_DELAYED,
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


# ─── Game 4: Herding Susceptibility ───

HERDING_SCENARIOS = [
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
        "description": "Markets have fallen 12% this month. What do you do with your equity SIPs?",
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


def herding_get_scenarios() -> dict:
    """Return all 3 scenarios for the herding game (phase 1: without social signal)."""
    return {
        "phase": "without_signal",
        "scenarios": [
            {
                "id": s["id"],
                "description": s["description"],
                "option_a": s["option_a"],
                "option_b": s["option_b"],
            }
            for s in HERDING_SCENARIOS
        ],
    }


def herding_get_with_signal() -> dict:
    """Return scenarios WITH social signal (phase 2)."""
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
            for s in HERDING_SCENARIOS
        ],
    }


def herding_score(phase1_choices: List[str], phase2_choices: List[str]) -> Tuple[float, float, float]:
    """Compute herding index from before/after social signal choices.

    Returns (herding_index_0_1, herding_score_0_100, sigma).
    """
    shifts_toward_social = 0
    for i in range(len(HERDING_SCENARIOS)):
        if i < len(phase1_choices) and i < len(phase2_choices):
            if phase1_choices[i] != phase2_choices[i]:
                # Social signal always favors option A in our design
                if phase2_choices[i] == "A":
                    shifts_toward_social += 1

    herding_index = shifts_toward_social / len(HERDING_SCENARIOS)
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
    valid_times = [rt for rt in response_times if rt >= 300]
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
) -> Dict:
    """Compute all scores for a completed game session."""
    rt_score, rt_sigma = risk_tolerance_score(risk_range)
    la_lambda, la_score, la_sigma = loss_aversion_score(loss_range)
    tp_k, tp_score, tp_sigma = time_preference_score(time_range)
    h_index, h_score, h_sigma = herding_score(herding_p1, herding_p2)
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
