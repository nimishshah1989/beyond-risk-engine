"""Question Engine API — CRUD + adaptive selection."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.models.database import get_db, QuestionItem, QuestionTier

router = APIRouter(prefix="/api/questions", tags=["Questions"])


class QuestionOut(BaseModel):
    id: int
    code: str
    tier: str
    text: str
    rationale: Optional[str]
    difficulty: float
    discrimination: float
    trait_weights: dict
    options: list
    calibrates: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    code: str
    tier: str  # "anchor", "diagnostic", "calibration"
    text: str
    rationale: Optional[str] = ""
    difficulty: float = 0.5
    discrimination: float = 1.5
    trait_weights: dict
    options: list
    calibrates: Optional[str] = None


@router.get("/", response_model=List[QuestionOut])
def list_questions(
    tier: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """List all questions, optionally filtered by tier."""
    query = db.query(QuestionItem)
    if active_only:
        query = query.filter(QuestionItem.is_active == True)
    if tier:
        query = query.filter(QuestionItem.tier == tier)
    return query.order_by(QuestionItem.code).all()


@router.get("/{code}", response_model=QuestionOut)
def get_question(code: str, db: Session = Depends(get_db)):
    q = db.query(QuestionItem).filter(QuestionItem.code == code).first()
    if not q:
        raise HTTPException(404, f"Question {code} not found")
    return q


@router.post("/", response_model=QuestionOut)
def create_question(data: QuestionCreate, db: Session = Depends(get_db)):
    """Add a new question to the bank."""
    existing = db.query(QuestionItem).filter(QuestionItem.code == data.code).first()
    if existing:
        raise HTTPException(400, f"Question code {data.code} already exists")

    q = QuestionItem(
        code=data.code,
        tier=data.tier,
        text=data.text,
        rationale=data.rationale,
        difficulty=data.difficulty,
        discrimination=data.discrimination,
        trait_weights=data.trait_weights,
        options=data.options,
        calibrates=data.calibrates,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.put("/{code}", response_model=QuestionOut)
def update_question(code: str, data: QuestionCreate, db: Session = Depends(get_db)):
    q = db.query(QuestionItem).filter(QuestionItem.code == code).first()
    if not q:
        raise HTTPException(404)
    for field, value in data.dict(exclude_unset=True).items():
        setattr(q, field, value)
    db.commit()
    db.refresh(q)
    return q


@router.delete("/{code}")
def deactivate_question(code: str, db: Session = Depends(get_db)):
    q = db.query(QuestionItem).filter(QuestionItem.code == code).first()
    if not q:
        raise HTTPException(404)
    q.is_active = False
    db.commit()
    return {"status": "deactivated", "code": code}


@router.get("/stats/summary")
def question_stats(db: Session = Depends(get_db)):
    """Summary stats for the question bank."""
    total = db.query(QuestionItem).filter(QuestionItem.is_active == True).count()
    anchors = db.query(QuestionItem).filter(QuestionItem.tier == "anchor", QuestionItem.is_active == True).count()
    diagnostics = db.query(QuestionItem).filter(QuestionItem.tier == "diagnostic", QuestionItem.is_active == True).count()
    calibrations = db.query(QuestionItem).filter(QuestionItem.tier == "calibration", QuestionItem.is_active == True).count()
    return {
        "total": total,
        "anchors": anchors,
        "diagnostics": diagnostics,
        "calibrations": calibrations,
    }
