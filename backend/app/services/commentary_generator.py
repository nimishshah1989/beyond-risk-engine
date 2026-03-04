"""AI Commentary Generator — narrative behavioral briefing for wealth managers.

Uses Anthropic Claude API to generate actionable, human-readable commentary
from quantitative behavioral profile data. Cached in BehavioralProfile.conversation_guide.
"""
import os
import json
import logging
from typing import Optional, Dict

import httpx

logger = logging.getLogger("beyond_risk.commentary_generator")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
COMMENTARY_MODEL = "claude-sonnet-4-5-20250929"
API_URL = "https://api.anthropic.com/v1/messages"

COMMENTARY_PROMPT = """You are a senior behavioral finance advisor at an Indian wealth management firm. Given the investor's complete behavioral profile data below, generate a structured advisory briefing.

INVESTOR DATA:
{investor_data}

Generate a JSON response with EXACTLY these keys:
{{
  "behavioral_summary": "2-3 sentence summary of who this investor is behaviorally. What drives them, what scares them, how they make decisions. Write in third person.",
  "key_risks": ["3-4 specific behavioral risks this advisor should watch for. Be concrete, not generic."],
  "conversation_starters": ["3-4 specific opening lines the advisor can use in the next meeting. Reference actual data points."],
  "investment_guardrails": ["3-4 hard rules for this investor's portfolio. E.g. 'Never exceed 60% equity' or 'Always maintain 6 months emergency fund visible'."],
  "say_do_analysis": "If FUSED data exists, explain the gap between what they say and what they do. Otherwise say 'Insufficient data for say-do analysis.'",
  "one_line_summary": "One punchy sentence capturing this investor's behavioral DNA. Think Bloomberg-style."
}}

RULES:
- Use Indian financial context (SIPs, NIFTY, AMCs, PMS, AIFs, etc.)
- Reference specific scores when relevant
- Be direct and actionable — this is for a professional advisor, not the investor
- All monetary references in INR with lakh/crore formatting
- If data is sparse, acknowledge it and give conservative recommendations
- Return ONLY valid JSON, no markdown formatting"""


async def generate_commentary(investor_data: Dict) -> Optional[Dict]:
    """Call Claude API to generate behavioral commentary from profile data."""
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set — skipping commentary generation")
        return None

    prompt = COMMENTARY_PROMPT.format(investor_data=json.dumps(investor_data, indent=2, default=str))

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                API_URL,
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": COMMENTARY_MODEL,
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()

        content = data.get("content", [{}])[0].get("text", "")
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        result = json.loads(content)
        logger.info("Commentary generated successfully (%d chars)", len(content))
        return result

    except httpx.HTTPStatusError as e:
        logger.error("Claude API HTTP error %d: %s", e.response.status_code, e.response.text[:200])
        return None
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Claude response as JSON: %s", str(e)[:200])
        return None
    except Exception as e:
        logger.error("Commentary generation failed: %s", str(e)[:200])
        return None


def build_commentary_input(profile, context, transaction_score, game_session) -> Dict:
    """Assemble all investor data into a single dict for the commentary prompt."""
    data = {
        "composite_risk_score": profile.composite_risk_score,
        "data_sources": profile.data_sources,
        "say_do_gap": profile.say_do_gap,
        "say_do_details": profile.say_do_details,
    }

    # Trait scores
    from app.services.bayesian_fusion import TRAIT_IDS
    traits = {}
    for t in TRAIT_IDS:
        score = getattr(profile, t, None)
        if score is not None:
            traits[t] = round(score, 1)
    data["trait_scores"] = traits

    # Financial context summary
    if context:
        data["financial_context"] = {
            "annual_income_lakhs": context.annual_income,
            "total_investable_assets_lakhs": context.total_investable_assets,
            "income_stability": context.income_stability,
            "years_to_retirement": context.years_to_retirement,
            "knowledge_level": context.knowledge_level,
            "money_meaning": context.money_meaning,
            "worst_fear": context.worst_fear,
            "target_return_pct": context.target_return_annual_pct,
            "time_horizon_years": context.time_horizon_years,
            "decision_maker": context.decision_maker,
            "has_experienced_real_loss": context.has_experienced_real_loss,
            "behavior_during_loss": context.behavior_during_loss,
        }

    # Transaction scores
    if transaction_score:
        data["transaction_scores"] = {
            "n_transactions": transaction_score.n_transactions,
            "date_range_months": transaction_score.date_range_months,
            "disposition_effect": transaction_score.disposition_effect,
            "sip_discipline": transaction_score.sip_discipline,
            "panic_score": transaction_score.panic_score,
            "diversification": transaction_score.diversification,
            "overtrading": transaction_score.overtrading,
        }

    # Game session summary
    if game_session:
        data["game_scores"] = {
            "risk_tolerance": game_session.risk_tolerance_score,
            "loss_aversion_lambda": game_session.loss_aversion_lambda,
            "time_preference_k_short": getattr(game_session, 'time_preference_k_short', None),
            "time_preference_k_long": getattr(game_session, 'time_preference_k_long', None),
            "herding_index": game_session.herding_index,
            "session_quality": game_session.consistency_score,
        }

    return data
