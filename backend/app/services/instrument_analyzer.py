"""
AI Instrument Analyzer — parses product factsheets/documents and 
auto-computes the 10-trait behavioral demand vector.

Uses Anthropic Claude API to:
1. Extract structured data from PDF/document uploads
2. Analyze investment characteristics
3. Compute behavioral demand scores with reasoning
"""
import os
import json
from typing import Optional, Dict
import httpx
from PyPDF2 import PdfReader
import io

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANALYSIS_MODEL = "claude-sonnet-4-5-20250929"

TRAIT_ANALYSIS_PROMPT = """You are an expert behavioral finance analyst. Given the following investment product documentation, compute the BEHAVIORAL DEMAND VECTOR — the traits an investor NEEDS to hold this product successfully.

For each of the 10 behavioral traits below, assign a score from 0-100 representing HOW MUCH of that trait the investor needs to be comfortable with this product.

**THE 10 TRAITS:**

1. **loss_aversion** (0=no losses possible, 100=extreme loss potential)
   - Consider: maximum drawdown, volatility, capital guarantee, historical worst period
   
2. **horizon_tolerance** (0=instant access, 100=10+ year commitment)
   - Consider: lock-in period, recommended holding period, when returns typically materialize
   
3. **liquidity_sensitivity** (0=instant redemption, 100=fully illiquid)
   - Consider: lock-in periods, exit loads, redemption frequency, notice periods
   
4. **behavioral_stability** (0=no discipline needed, 100=extreme discipline required)
   - Consider: will interim volatility test the investor? Does the strategy require patience during drawdowns?
   
5. **ambiguity_tolerance** (0=fully transparent/proven, 100=new/complex/opaque)
   - Consider: track record length, complexity of strategy, transparency of holdings, regulatory novelty
   
6. **regret_sensitivity** (0=no regret triggers, 100=high regret potential)
   - Consider: concentrated positions, benchmark deviation, opportunity cost visibility
   
7. **leverage_comfort** (0=no leverage, 100=heavily leveraged)
   - Consider: use of leverage, margin, derivatives, structured payoffs
   
8. **goal_rigidity** (0=no goal alignment needed, 100=strongly goal-linked)
   - Consider: is this a goal-specific product? Tax saving? Retirement? Does it have a maturity date?
   
9. **emotional_volatility** (0=no emotional triggers, 100=highly emotional)
   - Consider: daily NAV swings, mark-to-market visibility, news sensitivity
   
10. **decision_confidence** (0=no expertise needed, 100=requires sophisticated understanding)
    - Consider: product complexity, need for independent analysis, minimum ticket size implications

**PRODUCT DOCUMENTATION:**
{document_text}

**RESPOND WITH ONLY A JSON OBJECT IN THIS EXACT FORMAT:**
{{
  "risk_vector": {{
    "loss_aversion": <0-100>,
    "horizon_tolerance": <0-100>,
    "liquidity_sensitivity": <0-100>,
    "behavioral_stability": <0-100>,
    "ambiguity_tolerance": <0-100>,
    "regret_sensitivity": <0-100>,
    "leverage_comfort": <0-100>,
    "goal_rigidity": <0-100>,
    "emotional_volatility": <0-100>,
    "decision_confidence": <0-100>
  }},
  "extracted_info": {{
    "product_name": "<name>",
    "category": "<PMS/AIF/MF/Bond/FD/SIF/Insurance/Other>",
    "subcategory": "<specific type>",
    "min_investment": <in lakhs>,
    "lock_in_years": <number or 0>,
    "expected_return_range": "<X-Y%>",
    "risk_label": "<Very Low/Low/Moderate/Moderately High/High/Very High>",
    "liquidity": "<redemption terms>",
    "description": "<2-3 sentence description>"
  }},
  "reasoning": {{
    "loss_aversion": "<why this score>",
    "horizon_tolerance": "<why this score>",
    "liquidity_sensitivity": "<why this score>",
    "behavioral_stability": "<why this score>",
    "ambiguity_tolerance": "<why this score>",
    "regret_sensitivity": "<why this score>",
    "leverage_comfort": "<why this score>",
    "goal_rigidity": "<why this score>",
    "emotional_volatility": "<why this score>",
    "decision_confidence": "<why this score>"
  }}
}}"""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from uploaded PDF."""
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text[:15000]  # Limit to ~15K chars for API


async def analyze_instrument(
    document_text: str,
    filename: str = "",
) -> Optional[Dict]:
    """
    Use Claude API to analyze an instrument document and compute risk vector.
    Returns structured product data with risk vector and reasoning.
    """
    if not ANTHROPIC_API_KEY:
        return {"error": "ANTHROPIC_API_KEY not configured. Set it in Railway environment variables."}

    prompt = TRAIT_ANALYSIS_PROMPT.format(document_text=document_text[:12000])

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": ANALYSIS_MODEL,
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()

            # Extract text from response
            text_content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    text_content += block.get("text", "")

            # Parse JSON from response
            # Clean potential markdown fences
            clean = text_content.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

            result = json.loads(clean)
            result["source_file"] = filename
            result["analysis_model"] = ANALYSIS_MODEL
            return result

        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse AI response as JSON: {str(e)}", "raw_response": text_content[:500]}
        except httpx.HTTPError as e:
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
