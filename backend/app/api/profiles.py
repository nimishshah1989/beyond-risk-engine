"""Unified Behavioral Profile & Market Cycle API."""
import logging, math
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.database import (
    get_db, Investor, BehavioralProfile, ProfileHistory,
    InvestorFinancialContext, GameSession, Assessment, TransactionScore,
)
from app.services.bayesian_fusion import (
    fuse_profiles, compute_composite_risk_score, generate_say_do_alerts, TRAIT_IDS,
)
from app.services.games_engine import map_game_scores_to_traits
from app.services.financial_context import compute_financial_capacity, analyze_loss_experience

# Market cycle service may not exist yet — degrade gracefully
try:
    from app.services.market_cycle import get_cached_regime, check_return_aspiration, adjust_risk_for_cycle
except ImportError:
    def get_cached_regime(db): return None  # type: ignore[misc]
    def check_return_aspiration(pct, horizon, regime): return None  # type: ignore[misc]
    def adjust_risk_for_cycle(score, regime): return score  # type: ignore[misc]

logger = logging.getLogger("beyond_risk.api.profiles")
router = APIRouter(prefix="/api", tags=["Profiles", "Market"])


class AspirationCheckRequest(BaseModel):
    aspiration_pct: float
    time_horizon: int

# ─── Helpers ───

def _build_trait_scores(profile: BehavioralProfile) -> dict:
    return {
        trait: {"score": getattr(profile, trait, None),
                "ci_lower": getattr(profile, f"{trait}_ci_lower", None),
                "ci_upper": getattr(profile, f"{trait}_ci_upper", None)}
        for trait in TRAIT_IDS
    }

def _empty_profile(investor_id: int) -> dict:
    t = {"score": None, "ci_lower": None, "ci_upper": None}
    return {
        "investor_id": investor_id, "data_sources": "NONE",
        "trait_scores": {k: t for k in TRAIT_IDS},
        "composite_risk_score": None, "say_do_gap": None, "say_do_details": None,
        "behavioral_flags": [], "stress_prediction": None, "conversation_guide": None,
        "financial_capacity": None, "market_regime": None,
        "cycle_adjusted_risk": None, "aspiration_check": None, "updated_at": None,
    }

def _extract_psychometric(s: GameSession) -> dict:
    """Build psychometric trait dict from a completed GameSession."""
    la_lambda = s.loss_aversion_lambda or 2.25
    tp_score, tp_sigma = 50.0, s.time_preference_sigma or 14.0
    if s.time_preference_k is not None:
        tp_score = max(0, min(100, round(90 - math.log10(max(s.time_preference_k, 1e-6)) * 20)))
    return map_game_scores_to_traits({
        "risk_tolerance_score": s.risk_tolerance_score,
        "risk_tolerance_sigma": s.risk_tolerance_sigma or 12.0,
        "loss_aversion_score": max(0, min(100, round((la_lambda - 0.5) / 4.0 * 100))),
        "loss_aversion_sigma": s.loss_aversion_sigma or 10.0,
        "time_preference_score": tp_score, "time_preference_sigma": tp_sigma,
        "herding_score": (s.herding_index or 0) * 100, "herding_sigma": s.herding_sigma or 20.0,
    })

def _extract_questionnaire(a: Assessment) -> dict:
    if not a.trait_scores:
        return {}
    return {t: (sc, 15.0) for t, sc in a.trait_scores.items() if t in TRAIT_IDS}

def _extract_transaction(ts: TransactionScore) -> dict:
    return {
        "disposition_effect": (ts.disposition_effect or 50, ts.disposition_sigma or 25),
        "sip_discipline": (ts.sip_discipline or 50, ts.sip_sigma or 25),
        "panic_score": (ts.panic_score or 50, ts.panic_sigma or 25),
        "overtrading": (ts.overtrading or 50, ts.overtrading_sigma or 25),
    }

def _set_profile_traits(profile: BehavioralProfile, fused: dict) -> None:
    for trait in TRAIT_IDS:
        td = fused.get(trait, {})
        if hasattr(profile, trait):
            setattr(profile, trait, td.get("score"))
        for sfx in ("ci_lower", "ci_upper"):
            attr = f"{trait}_{sfx}"
            if hasattr(profile, attr):
                setattr(profile, attr, td.get(sfx))

# ─── Profile Endpoints ───

@router.get("/profiles/{investor_id}")
def get_profile(investor_id: int, db: Session = Depends(get_db)):
    """Get the unified behavioral profile for an investor."""
    if not db.query(Investor).filter_by(id=investor_id).first():
        raise HTTPException(status_code=404, detail="Investor not found")
    profile = db.query(BehavioralProfile).filter_by(investor_id=investor_id).first()
    if not profile:
        return {"data": _empty_profile(investor_id)}

    result = {
        "investor_id": investor_id,
        "data_sources": profile.data_sources or "NONE",
        "trait_scores": _build_trait_scores(profile),
        "composite_risk_score": profile.composite_risk_score,
        "say_do_gap": profile.say_do_gap,
        "say_do_details": profile.say_do_details,
        "behavioral_flags": profile.behavioral_flags or [],
        "stress_prediction": profile.stress_prediction,
        "conversation_guide": profile.conversation_guide,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }
    # Financial capacity
    fin_ctx = db.query(InvestorFinancialContext).filter_by(investor_id=investor_id).first()
    result["financial_capacity"] = fin_ctx.financial_capacity_score if fin_ctx else None
    # Market regime + cycle-adjusted risk
    regime = get_cached_regime(db)
    result["market_regime"] = regime
    capacity = fin_ctx.financial_capacity_score if fin_ctx else 100.0
    if profile.composite_risk_score is not None and regime:
        cycle_result = adjust_risk_for_cycle(profile.composite_risk_score, capacity, regime)
        result["cycle_adjusted_risk"] = cycle_result
    else:
        result["cycle_adjusted_risk"] = None
    # Aspiration check — only when investor has a target return
    result["aspiration_check"] = None
    if fin_ctx and fin_ctx.target_return_annual_pct is not None:
        result["aspiration_check"] = check_return_aspiration(
            fin_ctx.target_return_annual_pct, fin_ctx.time_horizon_years or 5, regime)
    return {"data": result}


@router.get("/profiles/{investor_id}/history")
def get_profile_history(investor_id: int, db: Session = Depends(get_db)):
    """Profile change history ordered by most recent first."""
    if not db.query(Investor).filter_by(id=investor_id).first():
        raise HTTPException(status_code=404, detail="Investor not found")
    rows = (db.query(ProfileHistory).filter_by(investor_id=investor_id)
            .order_by(ProfileHistory.created_at.desc()).all())
    return {"data": [
        {"id": r.id, "profile_snapshot": r.profile_snapshot, "trigger": r.trigger,
         "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows
    ]}


@router.post("/profiles/{investor_id}/recalculate")
def recalculate_profile(investor_id: int, db: Session = Depends(get_db)):
    """Force full fusion pipeline recalculation."""
    if not db.query(Investor).filter_by(id=investor_id).first():
        raise HTTPException(status_code=404, detail="Investor not found")

    # a) Latest completed GameSession -> psychometric
    game = (db.query(GameSession).filter_by(investor_id=investor_id, status="completed")
            .order_by(GameSession.completed_at.desc()).first())
    psychometric = _extract_psychometric(game) if game else {}

    # b) Latest completed Assessment -> questionnaire
    assess = (db.query(Assessment)
              .filter(Assessment.investor_id == investor_id, Assessment.status == "completed")
              .order_by(Assessment.completed_at.desc()).first())
    questionnaire = _extract_questionnaire(assess) if assess else {}

    # Merge: games take priority, questionnaire fills gaps
    merged_psych = {**questionnaire, **psychometric} if (psychometric or questionnaire) else None

    # c) Latest TransactionScore
    txn_score = (db.query(TransactionScore).filter_by(investor_id=investor_id)
                 .order_by(TransactionScore.computed_at.desc()).first())
    transaction = _extract_transaction(txn_score) if txn_score else None

    # d) Fuse all data sources
    fused = fuse_profiles(merged_psych, transaction)
    composite = compute_composite_risk_score(fused)

    # e+f) Create or update BehavioralProfile
    profile = db.query(BehavioralProfile).filter_by(investor_id=investor_id).first()
    if not profile:
        profile = BehavioralProfile(investor_id=investor_id)
        db.add(profile)

    profile.data_sources = fused["_data_sources"]
    profile.last_game_session_id = game.id if game else None
    profile.last_assessment_id = assess.id if assess else None
    profile.last_transaction_score_id = txn_score.id if txn_score else None
    profile.say_do_gap = fused["_say_do_gap"]
    profile.say_do_details = fused.get("_say_do_details")
    profile.composite_risk_score = composite
    _set_profile_traits(profile, fused)

    # Carry forward assessment insights + append say-do alerts
    if assess:
        profile.behavioral_flags = assess.behavioral_flags
        profile.stress_prediction = assess.stress_prediction
        profile.conversation_guide = assess.conversation_guide
        profile.drawdown_tolerance = assess.drawdown_tolerance
        profile.liquidity_buffer = assess.liquidity_buffer
    say_do_alerts = generate_say_do_alerts(fused.get("_say_do_details", {}))
    profile.behavioral_flags = (profile.behavioral_flags or []) + say_do_alerts
    profile.updated_at = datetime.utcnow()
    db.flush()

    # g) Save history snapshot
    snapshot = {t: fused[t] for t in TRAIT_IDS if t in fused}
    snapshot.update({"composite": composite, "data_sources": fused["_data_sources"]})
    db.add(ProfileHistory(investor_id=investor_id, profile_snapshot=snapshot,
                          trigger="MANUAL_RECALCULATE"))
    db.commit()
    logger.info("Profile recalculated for investor %d: sources=%s, composite=%.1f",
                investor_id, fused["_data_sources"], composite)
    return get_profile(investor_id, db)

# ─── Market Endpoints ───

@router.get("/market/regime")
def get_market_regime(db: Session = Depends(get_db)):
    """Get the current market regime (cached)."""
    regime = get_cached_regime(db)
    if regime is None:
        return {"data": None, "message": "Market regime data not available"}
    return {"data": regime}

@router.post("/market/aspiration-check")
def aspiration_check(req: AspirationCheckRequest, db: Session = Depends(get_db)):
    """Check whether a return aspiration is realistic given current market regime."""
    return {"data": check_return_aspiration(req.aspiration_pct, req.time_horizon, get_cached_regime(db))}
