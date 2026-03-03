"""Gamified Assessment API — 4 behavioral games, 19 trials."""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.database import (
    get_db, Investor, GameSession, GameTrial, BehavioralProfile, ProfileHistory,
)
from app.services.games_engine import (
    risk_tolerance_first_stimulus, risk_tolerance_next,
    loss_aversion_first_stimulus, loss_aversion_next,
    time_preference_first_stimulus, time_preference_next,
    herding_get_scenarios, herding_get_with_signal,
    compute_game_session_scores, map_game_scores_to_traits,
    RISK_GAMBLE_RANGE, LOSS_RANGE, DELAY_SEQUENCE,
)
from app.services.bayesian_fusion import fuse_profiles, compute_composite_risk_score

logger = logging.getLogger("beyond_risk.api.games")
router = APIRouter(prefix="/api/games", tags=["Gamified Assessment"])


# ─── Schemas ───

class StartGameRequest(BaseModel):
    investor_id: int
    device_type: Optional[str] = None


class TrialRequest(BaseModel):
    session_id: int
    game_type: str  # risk_tolerance, loss_aversion, time_preference, herding
    trial_number: int
    stimulus: dict
    response: dict  # {"choice": "gamble"/"guaranteed"/"accept"/"reject"/"immediate"/"delayed"/"A"/"B"}
    response_time_ms: int


class CompleteRequest(BaseModel):
    session_id: int


# ─── Helper: extract game state from existing trials ───

def _get_game_state(session_id: int, game_type: str, db: Session) -> tuple:
    """Get current state (range/choices) from existing trials."""
    trials = (
        db.query(GameTrial)
        .filter_by(session_id=session_id, game_type=game_type)
        .order_by(GameTrial.trial_number)
        .all()
    )

    if game_type == "risk_tolerance":
        current_range = list(RISK_GAMBLE_RANGE)
        for t in trials:
            choice = t.response.get("choice", "")
            mid = (current_range[0] + current_range[1]) / 2
            if choice == "gamble":
                current_range = [mid, current_range[1]]
            else:
                current_range = [current_range[0], mid]
        return current_range, len(trials)

    elif game_type == "loss_aversion":
        current_range = list(LOSS_RANGE)
        for t in trials:
            choice = t.response.get("choice", "")
            mid = (current_range[0] + current_range[1]) / 2
            if choice == "accept":
                current_range = [mid, current_range[1]]
            else:
                current_range = [current_range[0], mid]
        return current_range, len(trials)

    elif game_type == "time_preference":
        current_range = [0, len(DELAY_SEQUENCE) - 1]
        for t in trials:
            choice = t.response.get("choice", "")
            idx = (current_range[0] + current_range[1]) // 2
            if choice == "immediate":
                current_range = [current_range[0], idx]
            else:
                current_range = [idx, current_range[1]]
        return current_range, len(trials)

    elif game_type == "herding":
        p1_choices = []
        p2_choices = []
        for t in trials:
            phase = t.stimulus.get("phase", "")
            choice = t.response.get("choice", "")
            if phase == "without_signal":
                p1_choices.append(choice)
            else:
                p2_choices.append(choice)
        return (p1_choices, p2_choices), len(trials)

    return None, 0


# ─── Endpoints ───

@router.post("/start")
def start_game_session(req: StartGameRequest, db: Session = Depends(get_db)):
    """Start a new game session for an investor. Returns first stimuli for all 4 games."""
    investor = db.query(Investor).filter_by(id=req.investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    session = GameSession(
        investor_id=req.investor_id,
        device_type=req.device_type,
        status="in_progress",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    logger.info("Game session %d started for investor %d", session.id, req.investor_id)

    return {
        "session_id": session.id,
        "status": "in_progress",
        "first_trials": {
            "risk_tolerance": risk_tolerance_first_stimulus(),
            "loss_aversion": loss_aversion_first_stimulus(),
            "time_preference": time_preference_first_stimulus(),
            "herding": herding_get_scenarios(),
        },
    }


@router.post("/trial")
def submit_trial(req: TrialRequest, db: Session = Depends(get_db)):
    """Submit a single game trial response. Returns next stimulus or completion."""
    session = db.query(GameSession).filter_by(id=req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Session is not in progress")

    # Store the trial
    trial = GameTrial(
        session_id=req.session_id,
        game_type=req.game_type,
        trial_number=req.trial_number,
        stimulus=req.stimulus,
        response=req.response,
        response_time_ms=req.response_time_ms,
    )
    db.add(trial)
    db.commit()

    choice = req.response.get("choice", "")

    # Compute next stimulus based on game type
    if req.game_type == "risk_tolerance":
        current_range, _ = _get_game_state(req.session_id, "risk_tolerance", db)
        next_stim, new_range = risk_tolerance_next(req.trial_number, choice, current_range)
        if next_stim:
            return {"next_stimulus": next_stim, "game_type": "risk_tolerance"}
        return {"complete": True, "game_type": "risk_tolerance"}

    elif req.game_type == "loss_aversion":
        current_range, _ = _get_game_state(req.session_id, "loss_aversion", db)
        next_stim, new_range = loss_aversion_next(req.trial_number, choice, current_range)
        if next_stim:
            return {"next_stimulus": next_stim, "game_type": "loss_aversion"}
        return {"complete": True, "game_type": "loss_aversion"}

    elif req.game_type == "time_preference":
        current_range, _ = _get_game_state(req.session_id, "time_preference", db)
        next_stim, new_range = time_preference_next(req.trial_number, choice, current_range)
        if next_stim:
            return {"next_stimulus": next_stim, "game_type": "time_preference"}
        return {"complete": True, "game_type": "time_preference"}

    elif req.game_type == "herding":
        (p1, p2), count = _get_game_state(req.session_id, "herding", db)
        # Phase 1: 3 scenarios without signal, Phase 2: 3 with signal
        if len(p1) < 3:
            return {"next_phase": "without_signal", "remaining": 3 - len(p1), "game_type": "herding"}
        elif len(p2) < 3:
            if len(p2) == 0:
                return {"next_phase": "with_signal", "scenarios": herding_get_with_signal(), "game_type": "herding"}
            return {"next_phase": "with_signal", "remaining": 3 - len(p2), "game_type": "herding"}
        return {"complete": True, "game_type": "herding"}

    raise HTTPException(status_code=400, detail=f"Unknown game type: {req.game_type}")


@router.post("/complete")
def complete_session(req: CompleteRequest, db: Session = Depends(get_db)):
    """Complete a game session — compute all scores and update behavioral profile."""
    session = db.query(GameSession).filter_by(id=req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Gather final state for each game
    risk_range, _ = _get_game_state(req.session_id, "risk_tolerance", db)
    loss_range, _ = _get_game_state(req.session_id, "loss_aversion", db)
    time_range, _ = _get_game_state(req.session_id, "time_preference", db)
    (herding_p1, herding_p2), _ = _get_game_state(req.session_id, "herding", db)

    # Gather all response times
    all_trials = db.query(GameTrial).filter_by(session_id=req.session_id).all()
    response_times = [t.response_time_ms for t in all_trials if t.response_time_ms]

    # Compute scores
    scores = compute_game_session_scores(
        risk_range, loss_range, time_range,
        herding_p1, herding_p2, response_times,
    )

    # Update session
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    session.risk_tolerance_score = scores["risk_tolerance_score"]
    session.risk_tolerance_sigma = scores["risk_tolerance_sigma"]
    session.loss_aversion_lambda = scores["loss_aversion_lambda"]
    session.loss_aversion_sigma = scores["loss_aversion_sigma"]
    session.time_preference_k = scores["time_preference_k"]
    session.time_preference_sigma = scores["time_preference_sigma"]
    session.herding_index = scores["herding_index"]
    session.herding_sigma = scores["herding_sigma"]
    session.consistency_score = scores["session_quality"]
    session.median_response_time_ms = scores["median_response_time_ms"]

    # Map to trait model and update behavioral profile
    trait_map = map_game_scores_to_traits(scores)
    _update_behavioral_profile(session.investor_id, session.id, trait_map, db)

    db.commit()

    logger.info(
        "Game session %d completed. RT=%s, LA=%.2f, TP=%.4f, Herding=%.2f, Quality=%.0f",
        session.id, scores["risk_tolerance_score"], scores["loss_aversion_lambda"],
        scores["time_preference_k"], scores["herding_index"], scores["session_quality"],
    )

    return {
        "session_id": session.id,
        "status": "completed",
        "scores": scores,
        "trait_mapping": {k: {"score": v[0], "sigma": v[1]} for k, v in trait_map.items()},
    }


@router.get("/session/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    """Get session details with all trials."""
    session = db.query(GameSession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    trials = (
        db.query(GameTrial)
        .filter_by(session_id=session_id)
        .order_by(GameTrial.game_type, GameTrial.trial_number)
        .all()
    )

    return {
        "session": {
            "id": session.id,
            "investor_id": session.investor_id,
            "status": session.status,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "risk_tolerance_score": session.risk_tolerance_score,
            "risk_tolerance_sigma": session.risk_tolerance_sigma,
            "loss_aversion_lambda": session.loss_aversion_lambda,
            "loss_aversion_sigma": session.loss_aversion_sigma,
            "time_preference_k": session.time_preference_k,
            "time_preference_sigma": session.time_preference_sigma,
            "herding_index": session.herding_index,
            "herding_sigma": session.herding_sigma,
            "consistency_score": session.consistency_score,
            "median_response_time_ms": session.median_response_time_ms,
        },
        "trials": [
            {
                "game_type": t.game_type,
                "trial_number": t.trial_number,
                "stimulus": t.stimulus,
                "response": t.response,
                "response_time_ms": t.response_time_ms,
            }
            for t in trials
        ],
    }


def _update_behavioral_profile(investor_id: int, session_id: int, trait_map: dict, db: Session):
    """Create or update the unified behavioral profile after game completion."""
    profile = db.query(BehavioralProfile).filter_by(investor_id=investor_id).first()

    # Check for existing questionnaire data
    existing_psych = None
    if profile and profile.last_assessment_id:
        from app.models.database import Assessment
        assessment = db.query(Assessment).filter_by(id=profile.last_assessment_id).first()
        if assessment and assessment.trait_scores:
            existing_psych = {
                trait: (score, 15.0)  # questionnaire has wider sigma
                for trait, score in assessment.trait_scores.items()
            }

    # Fuse game scores with existing questionnaire data
    fused = fuse_profiles(trait_map, existing_psych)

    if not profile:
        profile = BehavioralProfile(investor_id=investor_id)
        db.add(profile)

    profile.data_sources = fused["_data_sources"]
    profile.last_game_session_id = session_id
    profile.say_do_gap = fused["_say_do_gap"]
    profile.say_do_details = fused.get("_say_do_details")

    # Set trait scores
    for trait_name in trait_map:
        trait_data = fused.get(trait_name, {})
        if hasattr(profile, trait_name):
            setattr(profile, trait_name, trait_data.get("score"))
        ci_lower_attr = f"{trait_name}_ci_lower"
        ci_upper_attr = f"{trait_name}_ci_upper"
        if hasattr(profile, ci_lower_attr):
            setattr(profile, ci_lower_attr, trait_data.get("ci_lower"))
        if hasattr(profile, ci_upper_attr):
            setattr(profile, ci_upper_attr, trait_data.get("ci_upper"))

    profile.composite_risk_score = compute_composite_risk_score(fused)

    # Save profile history snapshot
    snapshot = {trait: fused[trait] for trait in trait_map if trait in fused}
    snapshot["composite"] = profile.composite_risk_score
    history = ProfileHistory(
        investor_id=investor_id,
        profile_snapshot=snapshot,
        trigger="GAME_COMPLETE",
    )
    db.add(history)
