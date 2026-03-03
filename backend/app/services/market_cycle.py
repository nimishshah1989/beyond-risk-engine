"""Market cycle service — regime detection, return aspiration check, cycle-adjusted risk."""
import logging
from datetime import datetime, timedelta
import numpy as np
from app.services.market_data import get_nifty_history
from app.models.database import MarketRegimeCache, SessionLocal

logger = logging.getLogger("beyond_risk.market_cycle")

_REGIME_MAP = {
    # (regime, risk_premium, forward_return, risk_per_return)
    "CRISIS":   ("CRISIS_OPPORTUNITY",    "EXPANDED",   "14-18%", "EXCELLENT"),
    "EUPHORIA": ("LATE_CYCLE_EUPHORIA",   "COMPRESSED", "4-7%",   "POOR"),
    "ELEVATED": ("ELEVATED_VALUATIONS",   "THIN",       "6-10%",  "MODERATE_POOR"),
    "CHEAP":    ("ATTRACTIVE_VALUATIONS", "HEALTHY",    "12-16%", "GOOD"),
    "MID":      ("MID_CYCLE",             "NORMAL",     "10-13%", "MODERATE"),
}

_CYCLE_ADJUSTMENTS = {
    "CRISIS_OPPORTUNITY": 1.15, "ATTRACTIVE_VALUATIONS": 1.08,
    "MID_CYCLE": 1.00, "ELEVATED_VALUATIONS": 0.90, "LATE_CYCLE_EUPHORIA": 0.80,
}
_CYCLE_NOTES = {
    "CRISIS_OPPORTUNITY": "Markets in crisis — risk-reward favors slightly higher equity allocation.",
    "ATTRACTIVE_VALUATIONS": "Valuations attractive — modest upward tilt warranted.",
    "MID_CYCLE": "Mid-cycle conditions — no cycle adjustment applied.",
    "ELEVATED_VALUATIONS": "Elevated valuations — recommending caution, trimming equity allocation.",
    "LATE_CYCLE_EUPHORIA": "Late-cycle euphoria detected — significant risk reduction recommended.",
}
_REGIME_KEYS = ("regime", "risk_premium", "expected_forward_return", "risk_per_return",
                "valuation_ratio", "momentum", "volatility_regime", "vol_30d",
                "drawdown_from_peak", "nifty_current", "computed_at")
_CACHE_FIELDS = ("regime", "risk_premium", "expected_forward_return", "risk_per_return",
                 "valuation_ratio", "momentum", "vol_30d", "drawdown_from_peak", "nifty_current")


def _make_regime(regime_key: str, val_ratio=1.0, momentum="NEUTRAL", vol_regime="NORMAL",
                 vol_30d=15.0, drawdown=0.0, nifty=0.0) -> dict:
    r, rp, fwd, rpr = _REGIME_MAP[regime_key]
    return dict(zip(_REGIME_KEYS, (r, rp, fwd, rpr, val_ratio, momentum,
                                    vol_regime, vol_30d, drawdown, nifty,
                                    datetime.utcnow().isoformat())))


# ─── REGIME DETECTION ───

def compute_market_regime() -> dict:
    """Assess current market regime using valuation + momentum + volatility signals."""
    nifty = get_nifty_history()
    if nifty.empty or len(nifty) < 252:
        logger.warning("Insufficient NIFTY data for regime computation")
        return _make_regime("MID")
    try:
        close = nifty["Close"].astype(float)
        current = float(close.iloc[-1])
        drawdown = round(float(nifty["Drawdown"].iloc[-1]), 2)

        avg_5y = float(close.iloc[-1260:].mean()) if len(close) >= 1260 else float(close.mean())
        val_ratio = round(current / avg_5y, 2)

        ma200 = float(close.iloc[-200:].mean())
        momentum = "BULLISH" if current > ma200 * 1.05 else ("BEARISH" if current < ma200 * 0.95 else "NEUTRAL")

        returns = close.pct_change().dropna()
        vol_30d = round(float(returns.iloc[-30:].std() * np.sqrt(252) * 100), 1)
        vol_regime = "LOW" if vol_30d < 14 else ("HIGH" if vol_30d > 22 else "NORMAL")

        # Classify
        if drawdown < -20 or (momentum == "BEARISH" and vol_regime == "HIGH" and val_ratio < 0.9):
            key = "CRISIS"
        elif val_ratio > 1.3 and momentum == "BULLISH" and vol_regime == "LOW":
            key = "EUPHORIA"
        elif val_ratio > 1.2:
            key = "ELEVATED"
        elif val_ratio < 0.85:
            key = "CHEAP"
        else:
            key = "MID"

        return _make_regime(key, val_ratio, momentum, vol_regime, vol_30d, drawdown, round(current, 2))
    except Exception as exc:
        logger.error("Regime computation failed: %s", exc)
        return _make_regime("MID")


# ─── CACHING ───

def get_cached_regime(db=None) -> dict:
    """Get market regime from DB cache. Recompute if stale (>24h) or missing."""
    owns_db = db is None
    if owns_db:
        db = SessionLocal()
    try:
        cached = db.query(MarketRegimeCache).first()
        if cached and cached.computed_at and (datetime.utcnow() - cached.computed_at) < timedelta(hours=24):
            d = {k: getattr(cached, k, None) for k in _CACHE_FIELDS}
            d["volatility_regime"] = "NORMAL"  # not stored in DB
            d["computed_at"] = cached.computed_at.isoformat()
            return d
        regime = compute_market_regime()
        _upsert_cache(db, regime)
        return regime
    except Exception as exc:
        logger.error("get_cached_regime failed: %s", exc)
        return _make_regime("MID")
    finally:
        if owns_db:
            db.close()


def _upsert_cache(db, regime: dict) -> None:
    try:
        existing = db.query(MarketRegimeCache).first()
        if existing:
            for key in _CACHE_FIELDS:
                setattr(existing, key, regime.get(key))
            existing.computed_at = datetime.utcnow()
        else:
            db.add(MarketRegimeCache(**{k: regime.get(k) for k in _CACHE_FIELDS}))
        db.commit()
    except Exception as exc:
        logger.error("Failed to upsert regime cache: %s", exc)
        db.rollback()


# ─── RETURN ASPIRATION CHECK ───

def _parse_return_range(s: str) -> tuple:
    parts = s.replace("%", "").strip().split("-")
    try:
        return float(parts[0]), float(parts[1])
    except (IndexError, ValueError):
        return 10.0, 13.0


def check_return_aspiration(aspiration_pct: float, time_horizon: int, market_regime: dict) -> dict:
    """Check if the investor's return aspiration is realistic given the current cycle."""
    fwd_str = market_regime.get("expected_forward_return", "10-13%")
    low, high = _parse_return_range(fwd_str)
    mid = (low + high) / 2
    gap = aspiration_pct - mid

    if gap <= 0:
        realism, eq = "ACHIEVABLE", max(20, min(80, aspiration_pct / mid * 60))
    elif gap <= 4:
        realism, eq = "STRETCH", min(90, aspiration_pct / mid * 70)
    else:
        realism, eq = "UNREALISTIC", 95

    if time_horizon >= 10 and realism == "STRETCH":
        realism = "ACHIEVABLE_LONG_TERM"
    if time_horizon <= 3 and realism != "ACHIEVABLE":
        realism = "HIGH_RISK"

    msgs = {
        "ACHIEVABLE": f"A {aspiration_pct}% return target is realistic given current market conditions.",
        "STRETCH": f"A {aspiration_pct}% target is a stretch — markets currently price {fwd_str} forward returns.",
        "UNREALISTIC": f"A {aspiration_pct}% target significantly exceeds market-implied returns of {fwd_str}.",
        "ACHIEVABLE_LONG_TERM": f"A {aspiration_pct}% target is a stretch today but achievable over a {time_horizon}-year horizon.",
        "HIGH_RISK": f"Targeting {aspiration_pct}% in {time_horizon} years requires aggressive positioning with high downside risk.",
    }
    return {
        "aspiration": aspiration_pct, "market_forward_estimate": fwd_str,
        "gap": round(gap, 1), "realism": realism,
        "equity_allocation_needed": round(eq, 1), "message": msgs[realism],
        "regime": market_regime.get("regime", "MID_CYCLE"),
    }


# ─── CYCLE-ADJUSTED RISK ───

def adjust_risk_for_cycle(behavioral_risk_score: float, financial_capacity: float, market_regime: dict) -> dict:
    """Final risk recommendation blending behavioral score, financial capacity, and market cycle."""
    regime = market_regime.get("regime", "MID_CYCLE")
    factor = _CYCLE_ADJUSTMENTS.get(regime, 1.0)
    base_risk = min(behavioral_risk_score, financial_capacity)
    adjusted = round(max(0, min(100, base_risk * factor)), 1)
    equity_pct = round(max(10, min(85, adjusted * 0.85)), 1)

    return {
        "behavioral_risk_score": behavioral_risk_score, "financial_capacity": financial_capacity,
        "market_regime": regime, "cycle_adjustment_factor": factor,
        "adjusted_risk_score": adjusted, "suggested_equity_pct": equity_pct,
        "cycle_note": _CYCLE_NOTES.get(regime, "No adjustment."),
    }
