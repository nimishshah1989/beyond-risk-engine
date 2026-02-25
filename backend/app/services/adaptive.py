"""
Adaptive Question Selection Engine — IRT-based Computerized Adaptive Testing.

Three-tier flow:
1. ANCHOR items first (always asked, ensure comparability)
2. DIAGNOSTIC items selected adaptively (maximize information gain)
3. CALIBRATION items inserted every 3 diagnostics (detect inconsistency)

Stops when: confidence threshold reached OR max 25 questions.
"""
from typing import List, Dict, Optional


def select_next_question(
    answered_codes: List[str],
    all_questions: List[dict],
    current_confidence: Dict[str, int],
) -> Optional[dict]:
    """
    Select the next question using adaptive logic.
    Returns None if no more questions available.
    """
    unanswered = [q for q in all_questions if q["code"] not in answered_codes and q.get("is_active", True)]
    if not unanswered:
        return None

    # Phase 1: All anchors first
    anchors = [q for q in unanswered if q["tier"] == "anchor"]
    if anchors:
        return anchors[0]

    # Count diagnostics and calibrations answered so far
    diag_count = sum(
        1 for code in answered_codes
        if any(q["code"] == code and q["tier"] == "diagnostic" for q in all_questions)
    )
    cal_count = sum(
        1 for code in answered_codes
        if any(q["code"] == code and q["tier"] == "calibration" for q in all_questions)
    )

    # Phase 2: Insert calibration every 3 diagnostic items
    if diag_count > 0 and diag_count % 3 == 0 and cal_count < (diag_count // 3):
        calibrations = [q for q in unanswered if q["tier"] == "calibration"]
        if calibrations:
            return calibrations[0]

    # Phase 3: Select diagnostic maximizing information gain
    diagnostics = [q for q in unanswered if q["tier"] == "diagnostic"]
    if not diagnostics:
        # Fall back to remaining calibrations
        calibrations = [q for q in unanswered if q["tier"] == "calibration"]
        return calibrations[0] if calibrations else None

    # Find the trait with highest uncertainty (lowest confidence)
    lowest_conf = 100
    lowest_trait = None
    for trait_id, conf in current_confidence.items():
        if conf < lowest_conf:
            lowest_conf = conf
            lowest_trait = trait_id

    if not lowest_trait:
        return diagnostics[0]

    # Score each diagnostic by expected information gain for that trait
    scored = []
    for q in diagnostics:
        trait_weight = q.get("trait_weights", {}).get(lowest_trait, 0)
        discrimination = q.get("discrimination", 1.5)
        uncertainty_factor = (1 - lowest_conf / 100)
        info_gain = trait_weight * discrimination * uncertainty_factor
        scored.append((info_gain, q))

    scored.sort(key=lambda x: -x[0])
    return scored[0][1] if scored else diagnostics[0]


def should_stop_assessment(
    num_responses: int,
    confidence_scores: Dict[str, int],
    max_questions: int = 25,
    min_questions: int = 12,
    confidence_threshold: float = 72,
) -> bool:
    """
    Determine if assessment should stop.
    
    Stops when:
    - Hard cap reached (25 questions)
    - Soft stop: >= 12 questions AND average confidence >= 72%
    """
    if num_responses >= max_questions:
        return True

    if num_responses >= min_questions:
        avg_conf = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
        if avg_conf >= confidence_threshold:
            return True

    return False
