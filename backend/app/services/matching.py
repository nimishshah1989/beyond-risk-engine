"""
Product Matching Engine — compares investor behavioral profile against product demands.

Key principle: ASYMMETRIC SCORING
- When a product demands MORE of a trait than the investor has → 1.5x penalty
  (under-prepared investor in demanding product = dangerous)
- When investor has MORE than product demands → 0.7x penalty
  (over-prepared investor in simple product = suboptimal but safe)
"""
from typing import Dict, List, Optional


def match_investor_to_products(
    investor_traits: Dict[str, int],
    products: List[dict],
    financial_capacity: Optional[float] = None,
    ci_widths: Optional[Dict[str, float]] = None,
) -> List[dict]:
    """
    Compute behavioral fit scores for all products.
    Returns products sorted by fit score (best first).
    """
    results = []

    for product in products:
        risk_vector = product.get("risk_vector", {})
        if not risk_vector:
            continue

        total_distance = 0
        dimensions = 0
        trait_breakdown = {}

        for trait_id, product_demand in risk_vector.items():
            investor_score = investor_traits.get(trait_id)
            if investor_score is None:
                continue

            # Asymmetric distance calculation
            if product_demand > investor_score:
                # Product demands more than investor has → DANGEROUS → 1.5x penalty
                gap = (product_demand - investor_score) * 1.5
                direction = "under"
            else:
                # Investor has more than product needs → suboptimal but safe → 0.7x
                gap = (investor_score - product_demand) * 0.7
                direction = "over"

            trait_breakdown[trait_id] = {
                "investor": investor_score,
                "product_demands": product_demand,
                "gap": round(gap, 1),
                "direction": direction,
            }
            total_distance += gap
            dimensions += 1

        if dimensions == 0:
            continue

        avg_distance = total_distance / dimensions
        fit_score = max(0, min(100, round(100 - avg_distance)))

        # Component fit scores
        liquidity_fit = max(0, round(100 - abs(
            investor_traits.get("liquidity_sensitivity", 50) -
            risk_vector.get("liquidity_sensitivity", 50)
        )))
        complexity_match = max(0, round(100 - abs(
            investor_traits.get("ambiguity_tolerance", 50) -
            risk_vector.get("ambiguity_tolerance", 50)
        )))
        emotional_fit = max(0, round(100 - abs(
            investor_traits.get("emotional_volatility", 50) -
            risk_vector.get("emotional_volatility", 50)
        )))
        horizon_fit = max(0, round(100 - abs(
            investor_traits.get("horizon_tolerance", 50) -
            risk_vector.get("horizon_tolerance", 50)
        )))

        # Match confidence from CI widths (narrower CI = higher confidence)
        match_confidence = 100.0
        if ci_widths:
            relevant_widths = [ci_widths.get(t, 50) for t in risk_vector if t in ci_widths]
            if relevant_widths:
                avg_width = sum(relevant_widths) / len(relevant_widths)
                match_confidence = round(max(0, 100 - avg_width), 1)

        # Determine recommendation
        if fit_score >= 75:
            recommendation = "RECOMMENDED"
        elif fit_score >= 55:
            # Wide CI + product demands > investor = extra caution
            if match_confidence < 50:
                recommendation = "REVIEW_WITH_ADVISOR"
            else:
                recommendation = "CONDITIONAL"
        else:
            recommendation = "CAUTION"

        # Financial capacity constraint
        if financial_capacity is not None and financial_capacity < 40:
            if risk_vector.get("loss_aversion", 0) > 60 or risk_vector.get("emotional_volatility", 0) > 60:
                recommendation = "CAUTION"
                fit_score = min(fit_score, 50)

        results.append({
            "product_id": product.get("id"),
            "product_code": product.get("code"),
            "product_name": product.get("name"),
            "category": product.get("category"),
            "subcategory": product.get("subcategory"),
            "description": product.get("description"),
            "min_investment": product.get("min_investment"),
            "lock_in_years": product.get("lock_in_years"),
            "expected_return_range": product.get("expected_return_range"),
            "risk_label": product.get("risk_label"),
            "liquidity": product.get("liquidity"),
            "fit_score": fit_score,
            "liquidity_fit": liquidity_fit,
            "complexity_match": complexity_match,
            "emotional_fit": emotional_fit,
            "horizon_fit": horizon_fit,
            "recommendation": recommendation,
            "match_confidence": match_confidence,
            "trait_breakdown": trait_breakdown,
        })

    results.sort(key=lambda x: -x["fit_score"])
    return results
