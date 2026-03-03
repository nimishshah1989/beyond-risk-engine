"""Document Upload API — CAS/demat PDF upload, parsing, and scoring pipeline."""
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.database import (
    get_db, SessionLocal, Investor, DocumentUpload, ParsedTransaction,
    BehavioralProfile, ProfileHistory,
)
from app.services.cas_parser import parse_cas_pdf, parse_demat_pdf, parse_broker_csv, detect_file_type, normalize_transactions
from app.services.transaction_scorer import compute_all_transaction_scores
from app.services.market_data import enrich_with_market_data
from app.services.bayesian_fusion import fuse_profiles, compute_composite_risk_score

logger = logging.getLogger("beyond_risk.api.documents")
router = APIRouter(prefix="/api/documents", tags=["Document Upload"])


@router.post("/upload")
async def upload_document(
    investor_id: int = Form(...),
    password: str = Form(default=""),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """Upload a CAS/demat PDF or broker CSV. Processing happens in background."""
    investor = db.query(Investor).filter_by(id=investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    # Read file content
    content = await file.read()
    file_type = detect_file_type(file.filename, content)

    # Save to temp location
    upload_id = str(uuid.uuid4())[:8]
    temp_dir = "/tmp/beyond_risk_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"cas_{upload_id}_{file.filename}")
    with open(temp_path, "wb") as f:
        f.write(content)

    # Create upload record
    upload = DocumentUpload(
        investor_id=investor_id,
        filename=file.filename,
        file_type=file_type,
        file_size_bytes=len(content),
        status="pending",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    logger.info(
        "Document upload %d: %s (%s, %d bytes) for investor %d",
        upload.id, file.filename, file_type, len(content), investor_id,
    )

    # Launch background processing
    background_tasks.add_task(process_document_pipeline, upload.id, temp_path, password)

    return {
        "upload_id": upload.id,
        "status": "pending",
        "file_type": file_type,
        "filename": file.filename,
    }


@router.get("/status/{upload_id}")
def get_upload_status(upload_id: int, db: Session = Depends(get_db)):
    """Poll the status of an upload."""
    upload = db.query(DocumentUpload).filter_by(id=upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    return {
        "upload_id": upload.id,
        "status": upload.status,
        "filename": upload.filename,
        "file_type": upload.file_type,
        "total_folios": upload.total_folios,
        "total_transactions": upload.total_transactions,
        "statement_from": upload.statement_from.isoformat() if upload.statement_from else None,
        "statement_to": upload.statement_to.isoformat() if upload.statement_to else None,
        "error": upload.error_message,
        "uploaded_at": upload.uploaded_at.isoformat() if upload.uploaded_at else None,
        "parsed_at": upload.parsed_at.isoformat() if upload.parsed_at else None,
        "scored_at": upload.scored_at.isoformat() if upload.scored_at else None,
    }


@router.get("/investor/{investor_id}")
def get_investor_uploads(investor_id: int, db: Session = Depends(get_db)):
    """List all document uploads for an investor."""
    investor = db.query(Investor).filter_by(id=investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    uploads = (
        db.query(DocumentUpload)
        .filter_by(investor_id=investor_id)
        .order_by(DocumentUpload.uploaded_at.desc())
        .all()
    )

    return [
        {
            "upload_id": u.id,
            "filename": u.filename,
            "file_type": u.file_type,
            "status": u.status,
            "total_transactions": u.total_transactions,
            "uploaded_at": u.uploaded_at.isoformat() if u.uploaded_at else None,
            "scored_at": u.scored_at.isoformat() if u.scored_at else None,
            "error": u.error_message,
        }
        for u in uploads
    ]


# ─── Background Processing Pipeline ───

def process_document_pipeline(upload_id: int, file_path: str, password: str):
    """Background task: parse document, store transactions, enrich, score, update profile."""
    db = SessionLocal()
    try:
        upload = db.query(DocumentUpload).get(upload_id)
        if not upload:
            logger.error("Upload %d not found in pipeline", upload_id)
            return

        # Step 1: Parse
        upload.status = "parsing"
        db.commit()
        logger.info("Parsing document %d: %s", upload_id, upload.filename)

        if upload.file_type in ("CAMS", "KFINTECH"):
            result = parse_cas_pdf(file_path, password)
        elif upload.file_type in ("NSDL", "CDSL"):
            result = parse_demat_pdf(file_path)
        elif upload.file_type == "BROKER_CSV":
            result = parse_broker_csv(file_path)
        else:
            result = parse_cas_pdf(file_path, password)  # default try CAS

        if not result.get("success"):
            upload.status = "failed"
            upload.error_message = result.get("error", "Unknown parsing error")
            db.commit()
            logger.error("Parsing failed for upload %d: %s", upload_id, upload.error_message)
            return

        # Step 2: Normalize and store transactions
        data = result.get("data", {})
        normalized = normalize_transactions(data, upload.file_type)

        # Store metadata
        meta = result.get("meta", {})
        if meta.get("statement_from"):
            upload.statement_from = meta["statement_from"]
        if meta.get("statement_to"):
            upload.statement_to = meta["statement_to"]
        if meta.get("investor_name"):
            upload.investor_name_in_doc = meta["investor_name"]
        if meta.get("pan"):
            upload.investor_pan_in_doc = meta["pan"]
        upload.total_folios = meta.get("total_folios", 0)

        txn_count = 0
        for txn in normalized:
            pt = ParsedTransaction(
                upload_id=upload_id,
                investor_id=upload.investor_id,
                date=txn["date"],
                type=txn["type"],
                amount=txn.get("amount", 0),
                units=txn.get("units"),
                nav=txn.get("nav"),
                balance_units=txn.get("balance_units"),
                scheme_name=txn.get("scheme_name"),
                isin=txn.get("isin"),
                amfi_code=txn.get("amfi_code"),
                folio_number=txn.get("folio_number"),
                amc_name=txn.get("amc_name"),
                scheme_category=txn.get("scheme_category"),
            )
            db.add(pt)
            txn_count += 1

        upload.status = "parsed"
        upload.total_transactions = txn_count
        upload.parsed_at = datetime.utcnow()
        db.commit()
        logger.info("Parsed %d transactions from upload %d", txn_count, upload_id)

        if txn_count == 0:
            upload.status = "scored"
            upload.scored_at = datetime.utcnow()
            db.commit()
            return

        # Step 3: Enrich with NIFTY market data
        upload.status = "scoring"
        db.commit()
        try:
            enrich_with_market_data(upload_id, db)
        except Exception as exc:
            logger.warning("Market data enrichment failed: %s (continuing without)", exc)

        # Step 4: Compute behavioral scores
        scores = compute_all_transaction_scores(upload.investor_id, db)

        # Step 5: Update behavioral profile
        if scores:
            _update_profile_from_transactions(upload.investor_id, scores, db)

        upload.status = "scored"
        upload.scored_at = datetime.utcnow()
        db.commit()
        logger.info("Upload %d fully processed and scored", upload_id)

    except Exception as exc:
        logger.error("Pipeline failed for upload %d: %s", upload_id, exc, exc_info=True)
        try:
            upload = db.query(DocumentUpload).get(upload_id)
            if upload:
                upload.status = "failed"
                upload.error_message = str(exc)[:500]
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
        # Cleanup temp file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass


def _update_profile_from_transactions(investor_id: int, txn_scores: dict, db: Session):
    """Update behavioral profile with transaction-derived scores."""
    profile = db.query(BehavioralProfile).filter_by(investor_id=investor_id).first()

    # Build transaction data for fusion
    transaction_data = {
        k: v for k, v in txn_scores.items()
        if isinstance(v, tuple) and len(v) == 2
    }

    # Check for existing psychometric data
    existing_psych = None
    if profile and profile.last_game_session_id:
        from app.models.database import GameSession
        from app.services.games_engine import map_game_scores_to_traits
        gs = db.query(GameSession).filter_by(id=profile.last_game_session_id).first()
        if gs and gs.status == "completed":
            game_scores = {
                "risk_tolerance_score": gs.risk_tolerance_score,
                "loss_aversion_lambda": gs.loss_aversion_lambda,
                "loss_aversion_score": max(0, min(100, round((gs.loss_aversion_lambda - 0.5) / 4.0 * 100))) if gs.loss_aversion_lambda else 50,
                "loss_aversion_sigma": gs.loss_aversion_sigma or 10,
                "time_preference_k": gs.time_preference_k,
                "time_preference_score": 50,
                "time_preference_sigma": gs.time_preference_sigma or 14,
                "herding_index": gs.herding_index,
                "herding_score": round((gs.herding_index or 0) * 100),
                "herding_sigma": gs.herding_sigma or 20,
                "risk_tolerance_sigma": gs.risk_tolerance_sigma or 12,
            }
            existing_psych = map_game_scores_to_traits(game_scores)

    # Fuse
    fused = fuse_profiles(existing_psych, transaction_data)

    if not profile:
        profile = BehavioralProfile(investor_id=investor_id)
        db.add(profile)

    profile.data_sources = fused["_data_sources"]
    profile.last_transaction_score_id = txn_scores.get("id")
    profile.say_do_gap = fused["_say_do_gap"]
    profile.say_do_details = fused.get("_say_do_details")

    # Update all trait scores from fusion result
    for trait_name in ["loss_aversion", "horizon_tolerance", "liquidity_sensitivity",
                       "behavioral_stability", "ambiguity_tolerance", "regret_sensitivity",
                       "leverage_comfort", "goal_rigidity", "emotional_volatility", "decision_confidence"]:
        trait_data = fused.get(trait_name, {})
        if hasattr(profile, trait_name) and isinstance(trait_data, dict):
            setattr(profile, trait_name, trait_data.get("score"))
            ci_lower = f"{trait_name}_ci_lower"
            ci_upper = f"{trait_name}_ci_upper"
            if hasattr(profile, ci_lower):
                setattr(profile, ci_lower, trait_data.get("ci_lower"))
            if hasattr(profile, ci_upper):
                setattr(profile, ci_upper, trait_data.get("ci_upper"))

    profile.composite_risk_score = compute_composite_risk_score(fused)

    # Profile history
    snapshot = {
        trait: fused[trait] for trait in fused
        if not trait.startswith("_") and isinstance(fused[trait], dict)
    }
    snapshot["composite"] = profile.composite_risk_score
    history = ProfileHistory(
        investor_id=investor_id,
        profile_snapshot=snapshot,
        trigger="DOCUMENT_PARSED",
    )
    db.add(history)
    db.commit()
