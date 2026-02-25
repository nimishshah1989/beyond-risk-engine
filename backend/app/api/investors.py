"""Investor & Assessment API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.database import (
    get_db, Investor, Assessment, InvestorResponse,
    QuestionItem, AssessmentStatus
)
from app.services.scoring import (
    compute_trait_scores, compute_behavioral_flags,
    compute_stress_prediction, compute_liquidity_buffer
)
from app.services.adaptive import select_next_question, should_stop_assessment
from app.services.explain import generate_advisor_insights, generate_conversation_guide

router = APIRouter(prefix="/api", tags=["Investors"])

TRAIT_IDS = [
    "loss_aversion", "horizon_tolerance", "liquidity_sensitivity",
    "behavioral_stability", "ambiguity_tolerance", "regret_sensitivity",
    "leverage_comfort", "goal_rigidity", "emotional_volatility", "decision_confidence"
]

class InvestorCreate(BaseModel):
    name: str
    code: str
    age: Optional[str] = None
    aum: Optional[float] = 0
    segment: Optional[str] = None

class SubmitResponseRequest(BaseModel):
    assessment_id: int
    question_code: str
    option_index: int
    response_time_ms: Optional[int] = None


def _q_to_dict(q):
    return {"code": q.code, "tier": q.tier.value if hasattr(q.tier, 'value') else q.tier,
            "text": q.text, "rationale": q.rationale, "difficulty": q.difficulty,
            "discrimination": q.discrimination, "trait_weights": q.trait_weights,
            "options": q.options, "calibrates": q.calibrates, "is_active": q.is_active}

def _assessment_dict(a):
    if not a: return None
    return {"id": a.id, "investor_id": a.investor_id, "status": a.status.value if hasattr(a.status,'value') else a.status,
            "started_at": str(a.started_at), "completed_at": str(a.completed_at) if a.completed_at else None,
            "total_questions": a.total_questions, "trait_scores": a.trait_scores,
            "confidence_scores": a.confidence_scores, "behavioral_flags": a.behavioral_flags,
            "drawdown_tolerance": a.drawdown_tolerance, "liquidity_buffer": a.liquidity_buffer,
            "stress_prediction": a.stress_prediction, "conversation_guide": a.conversation_guide}


@router.get("/investors")
def list_investors(db: Session = Depends(get_db)):
    return [{"id": i.id, "name": i.name, "code": i.code, "age": i.age,
             "aum": i.aum, "segment": i.segment} for i in db.query(Investor).all()]

@router.post("/investors")
def create_investor(data: InvestorCreate, db: Session = Depends(get_db)):
    if db.query(Investor).filter(Investor.code == data.code).first():
        raise HTTPException(400, "Code exists")
    inv = Investor(**data.dict())
    db.add(inv); db.commit(); db.refresh(inv)
    return {"id": inv.id, "name": inv.name, "code": inv.code}

@router.get("/investors/{inv_id}")
def get_investor(inv_id: int, db: Session = Depends(get_db)):
    inv = db.query(Investor).filter(Investor.id == inv_id).first()
    if not inv: raise HTTPException(404)
    latest = db.query(Assessment).filter(
        Assessment.investor_id == inv_id, Assessment.status == AssessmentStatus.COMPLETED
    ).order_by(Assessment.completed_at.desc()).first()
    return {"investor": {"id": inv.id, "name": inv.name, "code": inv.code, "age": inv.age, "aum": inv.aum},
            "latest_assessment": _assessment_dict(latest)}


@router.post("/assessments/start")
def start_assessment(investor_id: int, db: Session = Depends(get_db)):
    inv = db.query(Investor).filter(Investor.id == investor_id).first()
    if not inv: raise HTTPException(404, "Investor not found")
    a = Assessment(investor_id=investor_id)
    db.add(a); db.commit(); db.refresh(a)
    questions = [_q_to_dict(q) for q in db.query(QuestionItem).filter(QuestionItem.is_active == True).all()]
    init_conf = {t: 10 for t in TRAIT_IDS}
    first_q = select_next_question([], questions, init_conf)
    return {"assessment_id": a.id, "question": first_q, "question_number": 1, "is_complete": False}


@router.post("/assessments/respond")
def submit_response(req: SubmitResponseRequest, db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == req.assessment_id).first()
    if not a: raise HTTPException(404)
    if a.status == AssessmentStatus.COMPLETED: raise HTTPException(400, "Already completed")

    resp = InvestorResponse(assessment_id=req.assessment_id, question_code=req.question_code,
                            option_index=req.option_index, response_time_ms=req.response_time_ms)
    db.add(resp); db.commit()

    all_resp = db.query(InvestorResponse).filter(InvestorResponse.assessment_id == req.assessment_id).all()
    resp_dicts = [{"question_code": r.question_code, "option_index": r.option_index} for r in all_resp]
    questions = [_q_to_dict(q) for q in db.query(QuestionItem).filter(QuestionItem.is_active == True).all()]
    irb = compute_trait_scores(resp_dicts, questions)

    if should_stop_assessment(len(resp_dicts), irb["confidence_scores"]):
        return _finish(a, irb, db)

    answered = [r.question_code for r in all_resp]
    next_q = select_next_question(answered, questions, irb["confidence_scores"])
    if not next_q:
        return _finish(a, irb, db)

    return {"assessment_id": a.id, "question": next_q, "question_number": len(all_resp) + 1,
            "is_complete": False, "current_scores": irb["trait_scores"], "current_confidence": irb["confidence_scores"]}


@router.get("/assessments/{aid}")
def get_assessment(aid: int, db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == aid).first()
    if not a: raise HTTPException(404)
    return _assessment_dict(a)


@router.get("/assessments/{aid}/full-report")
def full_report(aid: int, db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == aid).first()
    if not a or not a.trait_scores: raise HTTPException(404, "Not found or not completed")
    traits = a.trait_scores
    return {"assessment": _assessment_dict(a), "insights": generate_advisor_insights(traits),
            "conversation_guide": generate_conversation_guide(traits)}


def _finish(a, irb, db):
    traits = irb["trait_scores"]
    flags = compute_behavioral_flags(traits)
    stress = compute_stress_prediction(traits)
    convo = generate_conversation_guide(traits)
    a.status = AssessmentStatus.COMPLETED
    a.completed_at = datetime.utcnow()
    a.total_questions = db.query(InvestorResponse).filter(InvestorResponse.assessment_id == a.id).count()
    a.trait_scores = traits
    a.confidence_scores = irb["confidence_scores"]
    a.behavioral_flags = [{"type": f["type"], "title": f["title"], "msg": f["msg"], "action": f["action"]} for f in flags]
    a.drawdown_tolerance = stress["drawdown_tolerance"]
    a.liquidity_buffer = compute_liquidity_buffer(traits)
    a.stress_prediction = {"label": stress["label"], "severity": stress["severity"],
                           "text": stress["text"], "scenarios": stress["scenario_probabilities"]}
    a.conversation_guide = convo
    db.commit()
    return {"assessment_id": a.id, "is_complete": True, "trait_scores": traits,
            "confidence_scores": irb["confidence_scores"], "behavioral_flags": a.behavioral_flags,
            "stress_prediction": a.stress_prediction, "drawdown_tolerance": a.drawdown_tolerance,
            "liquidity_buffer": a.liquidity_buffer, "conversation_guide": convo}
