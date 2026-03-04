"""Transaction Scoring — 7 behavioral metrics from actual trading history.

All scores are 0-100 with associated sigma (confidence / standard deviation).
Higher score = stronger presence of that behavioral trait.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("beyond_risk.transaction_scorer")


def _deplete_lots(lots: List[tuple], sold_units: float) -> List[tuple]:
    """Remove sold units from lot records using FIFO."""
    remaining = sold_units
    new_lots = []
    for units, nav in lots:
        if remaining <= 0:
            new_lots.append((units, nav))
        elif units <= remaining:
            remaining -= units
        else:
            new_lots.append((units - remaining, nav))
            remaining = 0
    return new_lots


def compute_disposition_effect(transactions: List[dict]) -> Tuple[float, float]:
    """Odean (1998) methodology — PGR vs PLR.

    Measures tendency to sell winners too early and hold losers too long.
    Score 50 = neutral, >50 = disposition effect present, <50 = reverse disposition.
    """
    holdings = {}   # scheme -> [(units, purchase_nav)]
    last_nav = {}   # scheme -> last known NAV (for paper gain/loss evaluation)
    realized_gains = 0
    realized_losses = 0
    paper_gains = 0
    paper_losses = 0

    sorted_txns = sorted(transactions, key=lambda x: x["date"])

    for txn in sorted_txns:
        scheme = txn.get("scheme_name", "unknown")
        nav = txn.get("nav") or 0

        # Track last known NAV per scheme
        if nav > 0:
            last_nav[scheme] = nav

        if txn["type"] in ("PURCHASE", "PURCHASE_SIP", "SWITCH_IN"):
            units = abs(txn.get("units") or 0)
            if units > 0 and nav > 0:
                holdings.setdefault(scheme, []).append((units, nav))

        elif txn["type"] in ("REDEMPTION", "SWITCH_OUT") and nav:
            lots = holdings.get(scheme, [])
            if lots:
                total_units = sum(u for u, _ in lots)
                if total_units > 0:
                    avg_cost = sum(u * n for u, n in lots) / total_units
                    if nav > avg_cost:
                        realized_gains += 1
                    else:
                        realized_losses += 1

                    # Deplete sold units from holdings (FIFO)
                    sold_units = abs(txn.get("units") or 0)
                    holdings[scheme] = _deplete_lots(lots, sold_units)

                    # Count paper gains/losses on OTHER held schemes using THEIR last known NAV
                    for other, other_lots in holdings.items():
                        if other != scheme and other_lots:
                            other_total = sum(u for u, _ in other_lots)
                            other_nav = last_nav.get(other)
                            if other_total > 0 and other_nav:
                                other_avg = sum(u * n for u, n in other_lots) / other_total
                                if other_nav > other_avg:
                                    paper_gains += 1
                                else:
                                    paper_losses += 1

    pgr = realized_gains / (realized_gains + paper_gains) if (realized_gains + paper_gains) > 0 else 0
    plr = realized_losses / (realized_losses + paper_losses) if (realized_losses + paper_losses) > 0 else 0
    de = pgr - plr

    score = max(0, min(100, round(50 + de * 200)))
    n_events = realized_gains + realized_losses
    sigma = max(5, 30 - n_events * 2)
    return float(score), float(sigma)


def compute_sip_discipline(transactions: List[dict]) -> Tuple[float, float]:
    """Composite SIP health index (INVERTED: 100 = best discipline)."""
    sips = sorted(
        [t for t in transactions if t["type"] == "PURCHASE_SIP"],
        key=lambda x: x["date"],
    )
    if len(sips) < 3:
        return 50.0, 25.0  # insufficient data

    dates = [pd.Timestamp(s["date"]) for s in sips]
    amounts = [abs(s.get("amount") or 0) for s in sips]

    # 1. Continuation rate (30%): months_with_SIP / expected_months
    total_months = max(1, (dates[-1] - dates[0]).days / 30)
    continuation = min(1.0, len(sips) / total_months)

    # 2. Amount consistency (20%): 1 - CV(amounts)
    mean_amt = np.mean(amounts)
    if mean_amt > 0:
        cv = float(np.std(amounts) / mean_amt)
        consistency = max(0, 1 - cv)
    else:
        consistency = 0

    # 3. Gap penalty (20%): 1 - (longest_gap_months / 6)
    gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
    longest_gap_months = max(gaps) / 30 if gaps else 0
    gap_score = max(0, 1 - longest_gap_months / 6)

    # 4. Downturn discipline (30%): SIP during drawdowns / total SIPs in drawdown periods
    drawdown_sips = sum(1 for s in sips if (s.get("nifty_drawdown_pct") or 0) < -5)
    downturn_disc = drawdown_sips / max(1, len(sips) * 0.3)

    composite = continuation * 30 + consistency * 20 + gap_score * 20 + min(1, downturn_disc) * 30
    sigma = max(5.0, 20 - len(sips) // 5)
    return round(min(100, composite), 1), float(sigma)


def compute_panic_score(transactions: List[dict]) -> Tuple[float, float]:
    """Correlate redemptions with NIFTY drawdowns (>5% from peak).

    Higher score = more panic selling behavior.
    """
    redemptions = [t for t in transactions if t["type"] == "REDEMPTION"]
    if not redemptions:
        return 0.0, 25.0

    panic_events = sum(1 for r in redemptions if (r.get("nifty_drawdown_pct") or 0) < -5)
    panic_ratio = panic_events / len(redemptions)

    score = round(panic_ratio * 100)
    sigma = max(5.0, 25 - len(redemptions) * 3)
    return float(score), float(sigma)


def compute_diversification(transactions: List[dict]) -> Tuple[float, float]:
    """HHI-based diversification score (INVERTED: 100 = best diversified)."""
    holdings = {}
    for t in sorted(transactions, key=lambda x: x["date"]):
        scheme = t.get("scheme_name", "unknown")
        units = abs(t.get("units") or 0)
        nav = t.get("nav") or 0
        value = units * nav

        if t["type"] in ("PURCHASE", "PURCHASE_SIP", "SWITCH_IN"):
            holdings[scheme] = holdings.get(scheme, 0) + value
        elif t["type"] in ("REDEMPTION", "SWITCH_OUT"):
            holdings[scheme] = max(0, holdings.get(scheme, 0) - value)

    holdings = {k: v for k, v in holdings.items() if v > 0}
    if not holdings:
        return 50.0, 25.0

    total = sum(holdings.values())
    weights = [v / total for v in holdings.values()]
    hhi = sum(w ** 2 for w in weights)

    score = max(0, min(100, round((1 - hhi) * 104)))
    sigma = 10.0
    return float(score), sigma


def compute_herding_from_switches(transactions: List[dict]) -> Tuple[float, float]:
    """Detect switch-to-trending behavior from fund switches."""
    switches = [t for t in transactions if t["type"] == "SWITCH_IN"]
    if len(switches) < 2:
        return 50.0, 25.0

    # Simplified: flag switches into categories that were recently trending
    trending_categories = {"Small Cap", "Mid Cap", "Thematic", "Sectoral"}
    chase_count = sum(
        1 for s in switches
        if any(cat in (s.get("scheme_category") or "") for cat in trending_categories)
    )
    chase_ratio = chase_count / len(switches)

    score = round(chase_ratio * 100)
    sigma = max(8.0, 22 - len(switches) * 2)
    return float(score), float(sigma)


def compute_overtrading(transactions: List[dict]) -> Tuple[float, float]:
    """Annualized turnover-based overtrading score."""
    buys = sum(abs(t.get("amount") or 0) for t in transactions if t["type"] in ("PURCHASE", "SWITCH_IN"))
    sells = sum(abs(t.get("amount") or 0) for t in transactions if t["type"] in ("REDEMPTION", "SWITCH_OUT"))

    dates = [t["date"] for t in transactions]
    if not dates:
        return 50.0, 25.0

    min_date = min(dates)
    max_date = max(dates)
    if isinstance(min_date, str):
        min_date = pd.Timestamp(min_date)
        max_date = pd.Timestamp(max_date)
    years = max(0.5, (max_date - min_date).days / 365)

    avg_portfolio = max(buys, sells)
    if avg_portfolio <= 0:
        return 0.0, 25.0

    annual_turnover_pct = min(buys, sells) / avg_portfolio * 100 / years
    score = max(0, min(100, round(annual_turnover_pct / 2)))
    sigma = 12.0
    return float(score), sigma


def compute_recency_bias(transactions: List[dict]) -> Tuple[float, float]:
    """Fraction of non-SIP purchases into top-quartile recent performers."""
    lumpsum_buys = [t for t in transactions if t["type"] == "PURCHASE"]
    if len(lumpsum_buys) < 2:
        return 50.0, 25.0

    # Simplified: check if purchases are concentrated in equity/trending categories
    trending_categories = {"Small Cap", "Mid Cap", "Thematic", "Sectoral", "Momentum"}
    recency_count = sum(
        1 for b in lumpsum_buys
        if any(cat in (b.get("scheme_category") or "") for cat in trending_categories)
    )
    ratio = recency_count / len(lumpsum_buys)

    score = round(ratio * 100)
    sigma = max(8.0, 22 - len(lumpsum_buys) * 2)
    return float(score), float(sigma)


def compute_all_transaction_scores(investor_id: int, db) -> Dict:
    """Compute all 7 behavioral scores from parsed transactions.

    Returns dict of scores suitable for storing in TransactionScore model.
    """
    from app.models.database import ParsedTransaction, TransactionScore

    txns_raw = db.query(ParsedTransaction).filter_by(investor_id=investor_id).all()
    if not txns_raw:
        logger.warning("No transactions found for investor %d", investor_id)
        return {}

    # Convert to dicts for scoring functions
    txns = [
        {
            "date": t.date,
            "type": t.type,
            "amount": t.amount,
            "units": t.units,
            "nav": t.nav,
            "balance_units": t.balance_units,
            "scheme_name": t.scheme_name,
            "scheme_category": t.scheme_category,
            "nifty_drawdown_pct": t.nifty_drawdown_pct,
            "nifty_on_date": t.nifty_on_date,
        }
        for t in txns_raw
    ]

    disp_score, disp_sigma = compute_disposition_effect(txns)
    sip_score, sip_sigma = compute_sip_discipline(txns)
    panic_score, panic_sigma = compute_panic_score(txns)
    div_score, div_sigma = compute_diversification(txns)
    herd_score, herd_sigma = compute_herding_from_switches(txns)
    trade_score, trade_sigma = compute_overtrading(txns)
    recency_score, recency_sigma = compute_recency_bias(txns)

    # Date range
    dates = [t["date"] for t in txns]
    min_date = min(dates)
    max_date = max(dates)
    date_range_months = max(1, int((max_date - min_date).days / 30))

    # Get upload IDs
    upload_ids = list({t.upload_id for t in txns_raw})

    # Save to DB
    existing = db.query(TransactionScore).filter_by(investor_id=investor_id).first()
    if existing:
        score_record = existing
    else:
        score_record = TransactionScore(investor_id=investor_id)
        db.add(score_record)

    score_record.upload_ids = upload_ids
    score_record.disposition_effect = disp_score
    score_record.disposition_sigma = disp_sigma
    score_record.sip_discipline = sip_score
    score_record.sip_sigma = sip_sigma
    score_record.panic_score = panic_score
    score_record.panic_sigma = panic_sigma
    score_record.diversification = div_score
    score_record.diversification_sigma = div_sigma
    score_record.herding_score = herd_score
    score_record.herding_sigma = herd_sigma
    score_record.overtrading = trade_score
    score_record.overtrading_sigma = trade_sigma
    score_record.recency_bias = recency_score
    score_record.recency_sigma = recency_sigma
    score_record.n_transactions = len(txns)
    score_record.date_range_months = date_range_months
    score_record.computed_at = datetime.utcnow()

    db.commit()
    db.refresh(score_record)

    logger.info(
        "Transaction scores computed for investor %d: %d txns, %d months, disp=%s, sip=%s, panic=%s",
        investor_id, len(txns), date_range_months, disp_score, sip_score, panic_score,
    )

    # Data quality metrics
    sip_count = sum(1 for t in txns if t["type"] == "PURCHASE_SIP")
    unique_schemes = len({t["scheme_name"] for t in txns if t.get("scheme_name")})
    if len(txns) >= 100 and date_range_months >= 24:
        richness_label = "HIGH"
    elif len(txns) >= 30 and date_range_months >= 12:
        richness_label = "MEDIUM"
    else:
        richness_label = "LOW"

    return {
        "id": score_record.id,
        "disposition_effect": (disp_score, disp_sigma),
        "sip_discipline": (sip_score, sip_sigma),
        "panic_score": (panic_score, panic_sigma),
        "diversification": (div_score, div_sigma),
        "herding_score": (herd_score, herd_sigma),
        "overtrading": (trade_score, trade_sigma),
        "recency_bias": (recency_score, recency_sigma),
        "n_transactions": len(txns),
        "date_range_months": date_range_months,
        "data_quality": {
            "n_transactions": len(txns),
            "date_range_months": date_range_months,
            "richness_label": richness_label,
            "sip_count": sip_count,
            "unique_schemes": unique_schemes,
        },
    }


def map_transaction_scores_to_traits(scores: Dict) -> Dict[str, Tuple[float, float]]:
    """Map all 7 transaction scores to trait model for Bayesian fusion.

    Includes inversions where high transaction metric = low trait score.
    """
    if not scores:
        return {}

    herding = scores.get("herding_score", (50, 25))
    recency = scores.get("recency_bias", (50, 25))

    return {
        "disposition_effect": scores.get("disposition_effect", (50, 25)),
        "sip_discipline": scores.get("sip_discipline", (50, 25)),
        "panic_score": scores.get("panic_score", (50, 25)),
        "overtrading": scores.get("overtrading", (50, 25)),
        "diversification": scores.get("diversification", (50, 25)),
        "herding_inverted": (max(0, 100 - herding[0]), herding[1]),
        "recency_inverted": (max(0, 100 - recency[0]), recency[1]),
    }
