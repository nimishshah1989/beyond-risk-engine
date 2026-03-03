"""Products API — CRUD + AI-powered factsheet analysis."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.models.database import get_db, Product, BehavioralProfile, InvestorFinancialContext
from app.services.matching import match_investor_to_products
from app.services.instrument_analyzer import extract_text_from_pdf, analyze_instrument

router = APIRouter(prefix="/api/products", tags=["Products"])


class ProductOut(BaseModel):
    id: int
    code: str
    name: str
    category: str
    subcategory: Optional[str]
    description: Optional[str]
    risk_vector: dict
    min_investment: Optional[float]
    lock_in_years: Optional[float]
    expected_return_range: Optional[str]
    risk_label: Optional[str]
    liquidity: Optional[str]
    vector_source: Optional[str]
    ai_analysis_notes: Optional[str]
    is_active: bool
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ProductOut])
def list_products(category: Optional[str] = None, active_only: bool = True, db: Session = Depends(get_db)):
    q = db.query(Product)
    if active_only: q = q.filter(Product.is_active == True)
    if category: q = q.filter(Product.category == category)
    return q.order_by(Product.category, Product.name).all()


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(Product.category).distinct().all()
    return [c[0] for c in cats]


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p: raise HTTPException(404)
    return p


@router.post("/match")
def match_products(body: dict, db: Session = Depends(get_db)):
    """Match investor traits against all products. Accepts raw traits or investor_id."""
    # If investor_id provided, read from BehavioralProfile
    investor_id = body.get("investor_id")
    if investor_id:
        profile = db.query(BehavioralProfile).filter_by(investor_id=investor_id).first()
        if profile:
            trait_ids = ["loss_aversion", "horizon_tolerance", "liquidity_sensitivity",
                         "behavioral_stability", "ambiguity_tolerance", "regret_sensitivity",
                         "leverage_comfort", "goal_rigidity", "emotional_volatility", "decision_confidence"]
            investor_traits = {t: getattr(profile, t, 50) or 50 for t in trait_ids}
            ci_widths = {}
            for t in trait_ids:
                lo = getattr(profile, f"{t}_ci_lower", None)
                hi = getattr(profile, f"{t}_ci_upper", None)
                if lo is not None and hi is not None:
                    ci_widths[t] = hi - lo
        else:
            investor_traits = body
            ci_widths = None
        fin_ctx = db.query(InvestorFinancialContext).filter_by(investor_id=investor_id).first()
        capacity = fin_ctx.financial_capacity_score if fin_ctx else None
    else:
        investor_traits = body
        ci_widths = None
        capacity = None

    products = db.query(Product).filter(Product.is_active == True).all()
    p_dicts = [{"id": p.id, "code": p.code, "name": p.name, "category": p.category,
                "subcategory": p.subcategory, "description": p.description,
                "risk_vector": p.risk_vector, "min_investment": p.min_investment,
                "lock_in_years": p.lock_in_years, "expected_return_range": p.expected_return_range,
                "risk_label": p.risk_label, "liquidity": p.liquidity} for p in products]
    return match_investor_to_products(investor_traits, p_dicts, capacity, ci_widths)


@router.post("/analyze-document")
async def analyze_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a product factsheet (PDF) and let AI compute the risk vector.
    Returns the analysis with risk vector, extracted info, and reasoning.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported currently")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 10MB)")

    # Extract text from PDF
    text = extract_text_from_pdf(content)
    if not text.strip():
        raise HTTPException(400, "Could not extract text from PDF. Ensure it's not scanned/image-only.")

    # Analyze with AI
    result = await analyze_instrument(text, file.filename)

    if "error" in result:
        raise HTTPException(500, result["error"])

    return {
        "status": "analyzed",
        "filename": file.filename,
        "analysis": result,
        "message": "Review the analysis and use /api/products/save-analyzed to save to database"
    }


@router.post("/save-analyzed")
def save_analyzed_product(data: dict, db: Session = Depends(get_db)):
    """Save an AI-analyzed product to the database after review."""
    risk_vector = data.get("risk_vector")
    info = data.get("extracted_info", {})
    reasoning = data.get("reasoning", {})

    if not risk_vector:
        raise HTTPException(400, "risk_vector is required")

    code = data.get("code") or info.get("product_name", "NEW")[:15].upper().replace(" ", "-")
    existing = db.query(Product).filter(Product.code == code).first()
    if existing:
        code = code + "-AI"

    p = Product(
        code=code,
        name=info.get("product_name", "Unnamed Product"),
        category=info.get("category", "Other"),
        subcategory=info.get("subcategory"),
        description=info.get("description"),
        risk_vector=risk_vector,
        min_investment=info.get("min_investment"),
        lock_in_years=info.get("lock_in_years", 0),
        expected_return_range=info.get("expected_return_range"),
        risk_label=info.get("risk_label"),
        liquidity=info.get("liquidity"),
        vector_source="ai_analyzed",
        source_documents=[data.get("source_file", "uploaded")],
        ai_analysis_notes=str(reasoning),
    )
    db.add(p); db.commit(); db.refresh(p)
    return {"id": p.id, "code": p.code, "name": p.name, "status": "saved"}


@router.put("/{product_id}/vector")
def update_risk_vector(product_id: int, risk_vector: dict, db: Session = Depends(get_db)):
    """Manually update a product's risk vector."""
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p: raise HTTPException(404)
    p.risk_vector = risk_vector
    p.vector_source = "manual_override"
    db.commit()
    return {"status": "updated", "id": p.id}
