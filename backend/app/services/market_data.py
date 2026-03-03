"""Market data service — NIFTY historical data, drawdown computation, enrichment."""
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf

from app.models.database import ParsedTransaction, SessionLocal

logger = logging.getLogger("beyond_risk.market_data")

# Module-level cache for NIFTY data
_nifty_cache: Optional[pd.DataFrame] = None
_nifty_cache_time: Optional[datetime] = None
CACHE_TTL_HOURS = 168  # 7 days — regime changes slowly


def get_nifty_history(start: str = "2018-01-01") -> pd.DataFrame:
    """Fetch NIFTY 50 historical data with drawdown computation. Cached for 7 days."""
    global _nifty_cache, _nifty_cache_time

    if _nifty_cache is not None and _nifty_cache_time is not None:
        age_hours = (datetime.utcnow() - _nifty_cache_time).total_seconds() / 3600
        if age_hours < CACHE_TTL_HOURS:
            return _nifty_cache

    try:
        logger.info("Fetching NIFTY 50 history from yfinance (start=%s)", start)
        nifty = yf.download("^NSEI", start=start, end=datetime.now().strftime("%Y-%m-%d"), progress=False)

        if nifty.empty:
            logger.warning("yfinance returned empty data for ^NSEI")
            if _nifty_cache is not None:
                return _nifty_cache
            return pd.DataFrame()

        # Handle MultiIndex columns from yfinance
        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)

        nifty["Peak"] = nifty["Close"].cummax()
        nifty["Drawdown"] = (nifty["Close"] - nifty["Peak"]) / nifty["Peak"] * 100

        _nifty_cache = nifty
        _nifty_cache_time = datetime.utcnow()
        logger.info("NIFTY cache refreshed: %d rows, %s to %s", len(nifty), nifty.index[0].date(), nifty.index[-1].date())
        return nifty

    except Exception as exc:
        logger.error("Failed to fetch NIFTY data: %s", exc)
        if _nifty_cache is not None:
            return _nifty_cache
        return pd.DataFrame()


def get_drawdown_on_date(date, nifty_data: Optional[pd.DataFrame] = None) -> Optional[float]:
    """Get NIFTY drawdown percentage on a specific date."""
    if nifty_data is None:
        nifty_data = get_nifty_history()

    if nifty_data.empty:
        return None

    try:
        closest = nifty_data.index.asof(pd.Timestamp(date))
        if pd.isna(closest):
            return None
        return float(nifty_data.loc[closest, "Drawdown"])
    except Exception:
        return None


def get_nifty_close_on_date(date, nifty_data: Optional[pd.DataFrame] = None) -> Optional[float]:
    """Get NIFTY 50 closing price on a specific date."""
    if nifty_data is None:
        nifty_data = get_nifty_history()

    if nifty_data.empty:
        return None

    try:
        closest = nifty_data.index.asof(pd.Timestamp(date))
        if pd.isna(closest):
            return None
        return float(nifty_data.loc[closest, "Close"])
    except Exception:
        return None


def enrich_with_market_data(upload_id: int, db) -> int:
    """Add nifty_on_date and nifty_drawdown_pct to all parsed transactions for an upload.
    Returns count of enriched transactions."""
    nifty = get_nifty_history()
    if nifty.empty:
        logger.warning("Cannot enrich transactions — NIFTY data unavailable")
        return 0

    txns = db.query(ParsedTransaction).filter_by(upload_id=upload_id).all()
    enriched = 0

    for txn in txns:
        try:
            dd = get_drawdown_on_date(txn.date, nifty)
            close = get_nifty_close_on_date(txn.date, nifty)
            if dd is not None:
                txn.nifty_drawdown_pct = dd
            if close is not None:
                txn.nifty_on_date = close
            enriched += 1
        except Exception as exc:
            logger.warning("Failed to enrich txn %d: %s", txn.id, exc)

    db.commit()
    logger.info("Enriched %d/%d transactions with NIFTY data for upload %d", enriched, len(txns), upload_id)
    return enriched
