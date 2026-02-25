"""
Seed data for Beyond Risk Engine.
- 25 questions (5 anchor, 15 diagnostic, 5 calibration)
- 35 investment instruments across all categories
"""
from app.models.database import (
    SessionLocal, QuestionItem, Product, QuestionTier, init_db
)


SEED_QUESTIONS = [
    # ═══ ANCHOR ITEMS (always asked) ═══
    {
        "code": "A01", "tier": QuestionTier.ANCHOR, "difficulty": 0.5, "discrimination": 1.8,
        "text": "Your portfolio drops 20% in one month. Markets haven't crashed — it's sector-specific. What do you do?",
        "rationale": "Tests immediate loss response in a non-systemic scenario. Separates genuine loss aversion from general market panic.",
        "trait_weights": {"loss_aversion": 0.85, "emotional_volatility": 0.4},
        "options": [
            {"text": "Sell immediately to prevent further losses", "scores": {"loss_aversion": 90, "emotional_volatility": 85}},
            {"text": "Reduce position by half", "scores": {"loss_aversion": 70, "emotional_volatility": 60}},
            {"text": "Hold and monitor closely", "scores": {"loss_aversion": 40, "emotional_volatility": 35}},
            {"text": "Add more — this is an opportunity", "scores": {"loss_aversion": 15, "emotional_volatility": 15}},
        ]
    },
    {
        "code": "A02", "tier": QuestionTier.ANCHOR, "difficulty": 0.4, "discrimination": 1.7,
        "text": "You're offered an investment that could double in 7 years but can't be touched. Your reaction?",
        "rationale": "Baseline for time preference and liquidity needs. '7 years to double' (~10% CAGR) is realistic.",
        "trait_weights": {"horizon_tolerance": 0.9, "liquidity_sensitivity": 0.3},
        "options": [
            {"text": "7 years locked? Absolutely not.", "scores": {"horizon_tolerance": 10, "liquidity_sensitivity": 95}},
            {"text": "Only if it's a small portion of my wealth", "scores": {"horizon_tolerance": 40, "liquidity_sensitivity": 65}},
            {"text": "Interesting — I can wait if the returns justify it", "scores": {"horizon_tolerance": 70, "liquidity_sensitivity": 35}},
            {"text": "Perfect. My best investments are the ones I forget about.", "scores": {"horizon_tolerance": 95, "liquidity_sensitivity": 10}},
        ]
    },
    {
        "code": "A03", "tier": QuestionTier.ANCHOR, "difficulty": 0.5, "discrimination": 1.6,
        "text": "A friend made 3x returns on a stock you passed on. How does this affect your next decision?",
        "rationale": "Measures social comparison regret and strategy consistency.",
        "trait_weights": {"behavioral_stability": 0.8, "regret_sensitivity": 0.5},
        "options": [
            {"text": "I feel terrible and would jump on the next similar opportunity", "scores": {"behavioral_stability": 15, "regret_sensitivity": 90}},
            {"text": "It stings, and I'd probably adjust my approach", "scores": {"behavioral_stability": 35, "regret_sensitivity": 70}},
            {"text": "I'd note it but stick to my strategy", "scores": {"behavioral_stability": 70, "regret_sensitivity": 35}},
            {"text": "Good for them. My strategy is my strategy.", "scores": {"behavioral_stability": 95, "regret_sensitivity": 10}},
        ]
    },
    {
        "code": "A04", "tier": QuestionTier.ANCHOR, "difficulty": 0.5, "discrimination": 1.5,
        "text": "An advisor recommends an emerging market fund. You can't find much data. Your comfort level?",
        "rationale": "Tests comfort with unknown/unproven investment categories.",
        "trait_weights": {"ambiguity_tolerance": 0.85, "decision_confidence": 0.4},
        "options": [
            {"text": "No data, no investment. Period.", "scores": {"ambiguity_tolerance": 10, "decision_confidence": 70}},
            {"text": "I'd need significantly more research before committing", "scores": {"ambiguity_tolerance": 35, "decision_confidence": 55}},
            {"text": "If the thesis makes sense, limited data is acceptable", "scores": {"ambiguity_tolerance": 70, "decision_confidence": 45}},
            {"text": "Some of the best opportunities are in uncharted territory", "scores": {"ambiguity_tolerance": 92, "decision_confidence": 80}},
        ]
    },
    {
        "code": "A05", "tier": QuestionTier.ANCHOR, "difficulty": 0.4, "discrimination": 1.7,
        "text": "You have a child's education fund and a general wealth fund. Markets crash 30%. Which do you protect first?",
        "rationale": "Tests whether money is mentally bucketed by goal.",
        "trait_weights": {"goal_rigidity": 0.9, "leverage_comfort": 0.2},
        "options": [
            {"text": "Education fund — that money has a non-negotiable deadline", "scores": {"goal_rigidity": 95, "leverage_comfort": 20}},
            {"text": "Both equally — all money matters the same", "scores": {"goal_rigidity": 20, "leverage_comfort": 50}},
            {"text": "Neither — ride it out. Markets recover.", "scores": {"goal_rigidity": 30, "leverage_comfort": 40}},
            {"text": "I'd actually borrow to buy more in the general fund", "scores": {"goal_rigidity": 40, "leverage_comfort": 90}},
        ]
    },

    # ═══ DIAGNOSTIC ITEMS (adaptively selected) ═══
    {
        "code": "D01", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.7, "discrimination": 2.0,
        "text": "You check your portfolio and see a ₹15L unrealized loss. How often do you check it this week?",
        "rationale": "Portfolio monitoring frequency during loss periods is a strong behavioral indicator.",
        "trait_weights": {"loss_aversion": 0.9, "behavioral_stability": 0.3},
        "options": [
            {"text": "Multiple times daily", "scores": {"loss_aversion": 92, "behavioral_stability": 10}},
            {"text": "Once daily", "scores": {"loss_aversion": 70, "behavioral_stability": 35}},
            {"text": "A couple of times", "scores": {"loss_aversion": 45, "behavioral_stability": 60}},
            {"text": "Same as usual — weekly or less", "scores": {"loss_aversion": 15, "behavioral_stability": 90}},
        ]
    },
    {
        "code": "D02", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.6, "discrimination": 1.9,
        "text": "What percentage of your investable wealth would you lock in a 5-year instrument?",
        "rationale": "Direct quantitative measure of liquidity comfort.",
        "trait_weights": {"liquidity_sensitivity": 0.85, "goal_rigidity": 0.3},
        "options": [
            {"text": "0% — I need full access always", "scores": {"liquidity_sensitivity": 95, "goal_rigidity": 30}},
            {"text": "Up to 15%", "scores": {"liquidity_sensitivity": 70, "goal_rigidity": 45}},
            {"text": "25-40% if the returns are compelling", "scores": {"liquidity_sensitivity": 40, "goal_rigidity": 60}},
            {"text": "50%+ — my liquid needs are well covered elsewhere", "scores": {"liquidity_sensitivity": 12, "goal_rigidity": 75}},
        ]
    },
    {
        "code": "D03", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.6, "discrimination": 1.8,
        "text": "After a major market event, how long does it take for your emotional response to subside?",
        "rationale": "Duration of emotional response is more diagnostic than intensity.",
        "trait_weights": {"emotional_volatility": 0.9, "loss_aversion": 0.4},
        "options": [
            {"text": "Days or weeks — significantly affects my sleep/mood", "scores": {"emotional_volatility": 95, "loss_aversion": 75}},
            {"text": "A day or two of heightened attention", "scores": {"emotional_volatility": 65, "loss_aversion": 55}},
            {"text": "A few hours — then analytical again", "scores": {"emotional_volatility": 35, "loss_aversion": 35}},
            {"text": "I barely notice unless it's truly catastrophic", "scores": {"emotional_volatility": 10, "loss_aversion": 15}},
        ]
    },
    {
        "code": "D04", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.5, "discrimination": 1.7,
        "text": "When making a ₹50L+ investment decision, how many people do you consult?",
        "rationale": "Consultation count maps to decision confidence.",
        "trait_weights": {"decision_confidence": 0.85, "ambiguity_tolerance": 0.35},
        "options": [
            {"text": "I won't move without at least 3-4 opinions", "scores": {"decision_confidence": 15, "ambiguity_tolerance": 25}},
            {"text": "My advisor and one trusted person", "scores": {"decision_confidence": 45, "ambiguity_tolerance": 45}},
            {"text": "I discuss with my advisor but decide myself", "scores": {"decision_confidence": 72, "ambiguity_tolerance": 60}},
            {"text": "I do my own research and decide independently", "scores": {"decision_confidence": 92, "ambiguity_tolerance": 75}},
        ]
    },
    {
        "code": "D05", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.7, "discrimination": 2.1,
        "text": "Markets are at an all-time low. You can borrow at 9% to invest. Your response?",
        "rationale": "Combines leverage comfort with contrarian behavior.",
        "trait_weights": {"leverage_comfort": 0.9, "loss_aversion": 0.35},
        "options": [
            {"text": "Borrowing to invest? Never.", "scores": {"leverage_comfort": 5, "loss_aversion": 60}},
            {"text": "Too risky — what if it falls further?", "scores": {"leverage_comfort": 20, "loss_aversion": 50}},
            {"text": "I'd consider a small leveraged position", "scores": {"leverage_comfort": 65, "loss_aversion": 30}},
            {"text": "This is exactly when leverage makes sense", "scores": {"leverage_comfort": 95, "loss_aversion": 12}},
        ]
    },
    {
        "code": "D06", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.6, "discrimination": 1.8,
        "text": "You sold an investment that then doubled in value. How does this affect your future selling decisions?",
        "rationale": "Tests how past regret modifies future behavior.",
        "trait_weights": {"regret_sensitivity": 0.88, "behavioral_stability": 0.4},
        "options": [
            {"text": "I now hold everything too long — can't face selling again", "scores": {"regret_sensitivity": 92, "behavioral_stability": 12}},
            {"text": "I second-guess my sell decisions more often", "scores": {"regret_sensitivity": 70, "behavioral_stability": 35}},
            {"text": "I've added trailing stop-losses to my process", "scores": {"regret_sensitivity": 40, "behavioral_stability": 70}},
            {"text": "Every sell decision is independent — past outcomes don't matter", "scores": {"regret_sensitivity": 10, "behavioral_stability": 92}},
        ]
    },
    {
        "code": "D07", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.65, "discrimination": 1.9,
        "text": "Your 10-year investment is down 15% in year 3. Advisor says thesis is intact. What now?",
        "rationale": "Tests patience under adverse interim conditions.",
        "trait_weights": {"horizon_tolerance": 0.85, "emotional_volatility": 0.4},
        "options": [
            {"text": "Exit — 3 years is enough patience", "scores": {"horizon_tolerance": 12, "emotional_volatility": 70}},
            {"text": "Reduce to a token holding", "scores": {"horizon_tolerance": 30, "emotional_volatility": 55}},
            {"text": "Hold as planned", "scores": {"horizon_tolerance": 72, "emotional_volatility": 30}},
            {"text": "Increase my position while it's down", "scores": {"horizon_tolerance": 92, "emotional_volatility": 12}},
        ]
    },
    {
        "code": "D08", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.55, "discrimination": 1.7,
        "text": "Your retirement corpus hits its target 5 years early. What do you do?",
        "rationale": "Reveals whether goals are absolute targets or moving goalposts.",
        "trait_weights": {"goal_rigidity": 0.88, "liquidity_sensitivity": 0.3},
        "options": [
            {"text": "Lock it in safe instruments — goal achieved", "scores": {"goal_rigidity": 95, "liquidity_sensitivity": 40}},
            {"text": "Shift 70% to safe, keep 30% growing", "scores": {"goal_rigidity": 70, "liquidity_sensitivity": 35}},
            {"text": "Keep investing — why stop when it's working?", "scores": {"goal_rigidity": 25, "liquidity_sensitivity": 20}},
            {"text": "Reassign it to a bigger goal", "scores": {"goal_rigidity": 15, "liquidity_sensitivity": 15}},
        ]
    },
    {
        "code": "D09", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.7, "discrimination": 2.0,
        "text": "A new asset class emerges (like crypto in 2015). No track record, strong proponents. Your move?",
        "rationale": "Tests response to radical uncertainty with social proof.",
        "trait_weights": {"ambiguity_tolerance": 0.9, "decision_confidence": 0.35},
        "options": [
            {"text": "Wait 5+ years for proven track record", "scores": {"ambiguity_tolerance": 10, "decision_confidence": 40}},
            {"text": "Wait for regulatory clarity", "scores": {"ambiguity_tolerance": 30, "decision_confidence": 45}},
            {"text": "Small exploratory allocation (1-3%)", "scores": {"ambiguity_tolerance": 70, "decision_confidence": 65}},
            {"text": "Meaningful allocation if my research supports it", "scores": {"ambiguity_tolerance": 92, "decision_confidence": 85}},
        ]
    },
    {
        "code": "D10", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.6, "discrimination": 1.8,
        "text": "In the last market crash, what did you actually do (or would have done)?",
        "rationale": "Actual behavior during stress is the gold standard.",
        "trait_weights": {"behavioral_stability": 0.85, "emotional_volatility": 0.5},
        "options": [
            {"text": "Panicked and sold most positions", "scores": {"behavioral_stability": 8, "emotional_volatility": 92}},
            {"text": "Sold some positions I was worried about", "scores": {"behavioral_stability": 30, "emotional_volatility": 65}},
            {"text": "Held everything but was very anxious", "scores": {"behavioral_stability": 55, "emotional_volatility": 50}},
            {"text": "Held or bought more — stayed disciplined", "scores": {"behavioral_stability": 92, "emotional_volatility": 12}},
        ]
    },
    {
        "code": "D11", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.7, "discrimination": 1.8,
        "text": "Would you rather: A) Guaranteed ₹8L return, or B) 50% chance of ₹20L, 50% chance of ₹0?",
        "rationale": "Classic Prospect Theory test. EV of B (₹10L) is higher but most choose A.",
        "trait_weights": {"loss_aversion": 0.75, "ambiguity_tolerance": 0.5},
        "options": [
            {"text": "A — guaranteed every time", "scores": {"loss_aversion": 88, "ambiguity_tolerance": 15}},
            {"text": "A — but I'm tempted by B", "scores": {"loss_aversion": 65, "ambiguity_tolerance": 35}},
            {"text": "B — expected value is higher", "scores": {"loss_aversion": 25, "ambiguity_tolerance": 72}},
            {"text": "B — and I'd want even higher variance", "scores": {"loss_aversion": 8, "ambiguity_tolerance": 92}},
        ]
    },
    {
        "code": "D12", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.75, "discrimination": 2.1,
        "text": "You have a home loan at 8.5%. Markets return 14%. Invest instead of prepaying?",
        "rationale": "Real-world leverage decision familiar to Indian investors.",
        "trait_weights": {"leverage_comfort": 0.85, "horizon_tolerance": 0.3},
        "options": [
            {"text": "Always prepay — I hate debt", "scores": {"leverage_comfort": 8, "horizon_tolerance": 35}},
            {"text": "Prepay mostly, invest a little", "scores": {"leverage_comfort": 30, "horizon_tolerance": 45}},
            {"text": "Split 50/50", "scores": {"leverage_comfort": 60, "horizon_tolerance": 60}},
            {"text": "Invest everything — the math clearly favors it", "scores": {"leverage_comfort": 90, "horizon_tolerance": 75}},
        ]
    },
    {
        "code": "D13", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.65, "discrimination": 1.7,
        "text": "Breaking news: 'Markets to crash 25% says top analyst.' Your immediate reaction?",
        "rationale": "Tests reactivity to media predictions.",
        "trait_weights": {"emotional_volatility": 0.8, "decision_confidence": 0.4},
        "options": [
            {"text": "Panic — start looking at what to sell", "scores": {"emotional_volatility": 90, "decision_confidence": 15}},
            {"text": "Worried — call my advisor immediately", "scores": {"emotional_volatility": 65, "decision_confidence": 30}},
            {"text": "Note it, but analysts are often wrong", "scores": {"emotional_volatility": 30, "decision_confidence": 65}},
            {"text": "Ignore it — predictions are noise", "scores": {"emotional_volatility": 10, "decision_confidence": 85}},
        ]
    },
    {
        "code": "D14", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.6, "discrimination": 1.9,
        "text": "A stock you've been watching doubles overnight. You never bought it. What happens next?",
        "rationale": "Tests inaction regret — powerful driver of impulsive investing.",
        "trait_weights": {"regret_sensitivity": 0.85, "goal_rigidity": 0.35},
        "options": [
            {"text": "Can't stop thinking about the missed gain for days", "scores": {"regret_sensitivity": 92, "goal_rigidity": 20}},
            {"text": "Frustrating, but I look for the next opportunity", "scores": {"regret_sensitivity": 60, "goal_rigidity": 35}},
            {"text": "It wasn't in my plan, so it doesn't matter", "scores": {"regret_sensitivity": 20, "goal_rigidity": 80}},
            {"text": "I celebrate my discipline in not chasing it", "scores": {"regret_sensitivity": 8, "goal_rigidity": 90}},
        ]
    },
    {
        "code": "D15", "tier": QuestionTier.DIAGNOSTIC, "difficulty": 0.75, "discrimination": 2.0,
        "text": "Your advisor suggests a structured product with 1.5x leverage on Nifty. 3-year lock-in. Reaction?",
        "rationale": "Combines leverage and lock-in — both anxiety triggers.",
        "trait_weights": {"leverage_comfort": 0.85, "behavioral_stability": 0.3},
        "options": [
            {"text": "Leverage + lock-in = absolutely not", "scores": {"leverage_comfort": 5, "behavioral_stability": 60}},
            {"text": "Explain it 3 times, maybe 5% allocation", "scores": {"leverage_comfort": 30, "behavioral_stability": 45}},
            {"text": "If risk-reward makes sense, I'm open", "scores": {"leverage_comfort": 65, "behavioral_stability": 55}},
            {"text": "I actively seek leveraged opportunities", "scores": {"leverage_comfort": 92, "behavioral_stability": 50}},
        ]
    },

    # ═══ CALIBRATION ITEMS (consistency checks) ═══
    {
        "code": "C01", "tier": QuestionTier.CALIBRATION, "difficulty": 0.5, "discrimination": 1.5,
        "text": "Quick scenario: You gain ₹5L then lose ₹5L — back to even. How do you feel?",
        "rationale": "Cross-checks loss aversion. If low LA earlier but 'devastated' here, earlier answers may be aspirational.",
        "trait_weights": {"loss_aversion": 0.7, "behavioral_stability": 0.7},
        "calibrates": "loss_aversion",
        "options": [
            {"text": "Devastated — the loss overshadows the gain completely", "scores": {"loss_aversion": 95, "behavioral_stability": 15}},
            {"text": "Net negative — the loss feels worse", "scores": {"loss_aversion": 72, "behavioral_stability": 40}},
            {"text": "Neutral — back to zero means zero", "scores": {"loss_aversion": 35, "behavioral_stability": 70}},
            {"text": "Relieved — at least I didn't end up in loss", "scores": {"loss_aversion": 55, "behavioral_stability": 55}},
        ]
    },
    {
        "code": "C02", "tier": QuestionTier.CALIBRATION, "difficulty": 0.5, "discrimination": 1.5,
        "text": "Rank these: which makes you most uncomfortable?",
        "rationale": "Forces trade-off between time lock-in and volatility.",
        "trait_weights": {"horizon_tolerance": 0.7, "liquidity_sensitivity": 0.7},
        "calibrates": "horizon_tolerance",
        "options": [
            {"text": "Money locked for 10 years", "scores": {"horizon_tolerance": 10, "liquidity_sensitivity": 90}},
            {"text": "High daily volatility but liquid", "scores": {"horizon_tolerance": 50, "liquidity_sensitivity": 20}},
            {"text": "Slow returns but accessible anytime", "scores": {"horizon_tolerance": 70, "liquidity_sensitivity": 10}},
            {"text": "Moderate returns locked for 3 years", "scores": {"horizon_tolerance": 55, "liquidity_sensitivity": 50}},
        ]
    },
    {
        "code": "C03", "tier": QuestionTier.CALIBRATION, "difficulty": 0.5, "discrimination": 1.4,
        "text": "How would your spouse/family describe your reaction to financial news?",
        "rationale": "Third-party perspective check. People understate their emotional volatility.",
        "trait_weights": {"emotional_volatility": 0.75, "regret_sensitivity": 0.6},
        "calibrates": "emotional_volatility",
        "options": [
            {"text": "Very reactive — they can tell from my mood", "scores": {"emotional_volatility": 92, "regret_sensitivity": 65}},
            {"text": "Noticeably affected but I manage it", "scores": {"emotional_volatility": 65, "regret_sensitivity": 50}},
            {"text": "They probably wouldn't know unless I mentioned it", "scores": {"emotional_volatility": 30, "regret_sensitivity": 25}},
            {"text": "I rarely react visibly to market news", "scores": {"emotional_volatility": 10, "regret_sensitivity": 15}},
        ]
    },
    {
        "code": "C04", "tier": QuestionTier.CALIBRATION, "difficulty": 0.5, "discrimination": 1.5,
        "text": "After making a major investment decision, do you feel:",
        "rationale": "Post-decision state reveals true confidence level.",
        "trait_weights": {"decision_confidence": 0.7, "ambiguity_tolerance": 0.6},
        "calibrates": "decision_confidence",
        "options": [
            {"text": "Anxious — constantly wondering if I made the right call", "scores": {"decision_confidence": 10, "ambiguity_tolerance": 15}},
            {"text": "Somewhat uneasy for a few days", "scores": {"decision_confidence": 35, "ambiguity_tolerance": 35}},
            {"text": "Confident but open to revisiting if data changes", "scores": {"decision_confidence": 72, "ambiguity_tolerance": 65}},
            {"text": "Fully committed — I rarely look back", "scores": {"decision_confidence": 92, "ambiguity_tolerance": 80}},
        ]
    },
    {
        "code": "C05", "tier": QuestionTier.CALIBRATION, "difficulty": 0.5, "discrimination": 1.5,
        "text": "In the last 2 years, how many times have you significantly changed your investment strategy?",
        "rationale": "Objective behavioral measure cross-checks self-reported stability.",
        "trait_weights": {"behavioral_stability": 0.8, "loss_aversion": 0.5},
        "calibrates": "behavioral_stability",
        "options": [
            {"text": "5+ times — I adapt to what's happening", "scores": {"behavioral_stability": 8, "loss_aversion": 55}},
            {"text": "3-4 times — when circumstances demanded it", "scores": {"behavioral_stability": 30, "loss_aversion": 45}},
            {"text": "Once or twice — thoughtful adjustments", "scores": {"behavioral_stability": 70, "loss_aversion": 30}},
            {"text": "Zero — my strategy hasn't changed", "scores": {"behavioral_stability": 95, "loss_aversion": 20}},
        ]
    },
]


SEED_PRODUCTS = [
    # ═══ EQUITY MUTUAL FUNDS ═══
    {"code": "MF-EQ-01", "name": "HDFC Flexi Cap Fund - Growth", "category": "Equity MF", "subcategory": "Flexi Cap",
     "description": "Multi-cap equity fund with flexible allocation. Can shift between large, mid, and small caps based on opportunity.",
     "min_investment": 5, "lock_in_years": 0, "expected_return_range": "12-18%", "risk_label": "High", "liquidity": "T+3 redemption",
     "risk_vector": {"loss_aversion": 65, "horizon_tolerance": 60, "liquidity_sensitivity": 25, "behavioral_stability": 55, "ambiguity_tolerance": 45, "regret_sensitivity": 45, "leverage_comfort": 10, "goal_rigidity": 30, "emotional_volatility": 55, "decision_confidence": 45}},

    {"code": "MF-EQ-02", "name": "SBI Small Cap Fund - Growth", "category": "Equity MF", "subcategory": "Small Cap",
     "description": "High-growth small cap fund. Expect 30-40% drawdowns during corrections. Requires 7+ year commitment.",
     "min_investment": 5, "lock_in_years": 0, "expected_return_range": "15-25%", "risk_label": "Very High", "liquidity": "T+3 (but exit load 1Y)",
     "risk_vector": {"loss_aversion": 85, "horizon_tolerance": 80, "liquidity_sensitivity": 45, "behavioral_stability": 70, "ambiguity_tolerance": 65, "regret_sensitivity": 60, "leverage_comfort": 20, "goal_rigidity": 25, "emotional_volatility": 75, "decision_confidence": 60}},

    {"code": "MF-EQ-03", "name": "Axis Bluechip Fund - Growth", "category": "Equity MF", "subcategory": "Large Cap",
     "description": "Large cap focused fund investing in top 100 companies. Lower volatility than broader market.",
     "min_investment": 5, "lock_in_years": 0, "expected_return_range": "10-15%", "risk_label": "Moderately High", "liquidity": "T+3",
     "risk_vector": {"loss_aversion": 50, "horizon_tolerance": 50, "liquidity_sensitivity": 20, "behavioral_stability": 40, "ambiguity_tolerance": 30, "regret_sensitivity": 35, "leverage_comfort": 5, "goal_rigidity": 35, "emotional_volatility": 40, "decision_confidence": 35}},

    {"code": "MF-EQ-04", "name": "Motilal Oswal Midcap Fund", "category": "Equity MF", "subcategory": "Mid Cap",
     "description": "Concentrated mid-cap portfolio of 25-30 stocks. Higher alpha potential but also higher tracking error.",
     "min_investment": 5, "lock_in_years": 0, "expected_return_range": "14-22%", "risk_label": "High", "liquidity": "T+3",
     "risk_vector": {"loss_aversion": 72, "horizon_tolerance": 68, "liquidity_sensitivity": 30, "behavioral_stability": 60, "ambiguity_tolerance": 55, "regret_sensitivity": 50, "leverage_comfort": 12, "goal_rigidity": 28, "emotional_volatility": 62, "decision_confidence": 55}},

    {"code": "MF-EQ-05", "name": "Axis ELSS Tax Saver", "category": "Equity MF", "subcategory": "ELSS",
     "description": "Tax-saving equity fund with mandatory 3-year lock-in under Section 80C.",
     "min_investment": 0.05, "lock_in_years": 3, "expected_return_range": "12-18%", "risk_label": "High", "liquidity": "3-year lock-in",
     "risk_vector": {"loss_aversion": 55, "horizon_tolerance": 55, "liquidity_sensitivity": 60, "behavioral_stability": 45, "ambiguity_tolerance": 40, "regret_sensitivity": 35, "leverage_comfort": 10, "goal_rigidity": 70, "emotional_volatility": 45, "decision_confidence": 40}},

    {"code": "MF-EQ-06", "name": "Motilal Oswal S&P 500 Index Fund", "category": "Equity MF", "subcategory": "International",
     "description": "Passive US market exposure via S&P 500 tracking. Currency risk adds additional dimension.",
     "min_investment": 5, "lock_in_years": 0, "expected_return_range": "10-14% (INR terms)", "risk_label": "Moderately High", "liquidity": "T+3",
     "risk_vector": {"loss_aversion": 50, "horizon_tolerance": 65, "liquidity_sensitivity": 30, "behavioral_stability": 55, "ambiguity_tolerance": 60, "regret_sensitivity": 35, "leverage_comfort": 10, "goal_rigidity": 35, "emotional_volatility": 50, "decision_confidence": 50}},

    # ═══ HYBRID / BALANCED MUTUAL FUNDS ═══
    {"code": "MF-HY-01", "name": "HDFC Balanced Advantage Fund", "category": "Hybrid MF", "subcategory": "Dynamic Allocation",
     "description": "Auto-rebalances between equity and debt based on market valuations. Reduces need for timing decisions.",
     "min_investment": 5, "lock_in_years": 0, "expected_return_range": "10-14%", "risk_label": "Moderate", "liquidity": "T+3",
     "risk_vector": {"loss_aversion": 45, "horizon_tolerance": 40, "liquidity_sensitivity": 20, "behavioral_stability": 35, "ambiguity_tolerance": 30, "regret_sensitivity": 30, "leverage_comfort": 8, "goal_rigidity": 45, "emotional_volatility": 35, "decision_confidence": 35}},

    {"code": "MF-HY-02", "name": "ICICI Pru Equity & Debt Fund", "category": "Hybrid MF", "subcategory": "Aggressive Hybrid",
     "description": "65-80% equity with debt cushion. Tax-efficient (equity taxation). Moderate volatility.",
     "min_investment": 5, "lock_in_years": 0, "expected_return_range": "11-15%", "risk_label": "Moderately High", "liquidity": "T+3",
     "risk_vector": {"loss_aversion": 52, "horizon_tolerance": 48, "liquidity_sensitivity": 22, "behavioral_stability": 40, "ambiguity_tolerance": 35, "regret_sensitivity": 35, "leverage_comfort": 8, "goal_rigidity": 40, "emotional_volatility": 42, "decision_confidence": 38}},

    # ═══ DEBT MUTUAL FUNDS ═══
    {"code": "MF-DT-01", "name": "ICICI Pru Corporate Bond Fund", "category": "Debt MF", "subcategory": "Corporate Bond",
     "description": "AA+ rated corporate bonds. Low volatility, predictable returns. Ideal for capital preservation.",
     "min_investment": 5, "lock_in_years": 0, "expected_return_range": "7-9%", "risk_label": "Low", "liquidity": "T+1",
     "risk_vector": {"loss_aversion": 20, "horizon_tolerance": 30, "liquidity_sensitivity": 15, "behavioral_stability": 20, "ambiguity_tolerance": 15, "regret_sensitivity": 15, "leverage_comfort": 5, "goal_rigidity": 30, "emotional_volatility": 15, "decision_confidence": 25}},

    {"code": "MF-DT-02", "name": "HDFC Short Term Debt Fund", "category": "Debt MF", "subcategory": "Short Duration",
     "description": "Short duration debt with near-zero volatility. High liquidity. The calmest corner of any portfolio.",
     "min_investment": 5, "lock_in_years": 0, "expected_return_range": "6.5-8%", "risk_label": "Low", "liquidity": "T+1",
     "risk_vector": {"loss_aversion": 15, "horizon_tolerance": 20, "liquidity_sensitivity": 10, "behavioral_stability": 15, "ambiguity_tolerance": 10, "regret_sensitivity": 10, "leverage_comfort": 0, "goal_rigidity": 40, "emotional_volatility": 10, "decision_confidence": 20}},

    {"code": "MF-DT-03", "name": "SBI Magnum Gilt Fund", "category": "Debt MF", "subcategory": "Gilt / G-Sec",
     "description": "Government securities fund. Zero credit risk but interest rate sensitive. Benefits from rate cuts.",
     "min_investment": 5, "lock_in_years": 0, "expected_return_range": "7-10%", "risk_label": "Low to Moderate", "liquidity": "T+1",
     "risk_vector": {"loss_aversion": 25, "horizon_tolerance": 40, "liquidity_sensitivity": 18, "behavioral_stability": 25, "ambiguity_tolerance": 20, "regret_sensitivity": 20, "leverage_comfort": 5, "goal_rigidity": 35, "emotional_volatility": 20, "decision_confidence": 28}},

    {"code": "MF-DT-04", "name": "Aditya Birla Sun Life Liquid Fund", "category": "Debt MF", "subcategory": "Liquid",
     "description": "Overnight to 91-day instruments. Near-zero risk. Emergency fund parking. Instant redemption up to ₹50K.",
     "min_investment": 0.5, "lock_in_years": 0, "expected_return_range": "5.5-6.5%", "risk_label": "Very Low", "liquidity": "Instant (up to ₹50K)",
     "risk_vector": {"loss_aversion": 5, "horizon_tolerance": 5, "liquidity_sensitivity": 5, "behavioral_stability": 5, "ambiguity_tolerance": 5, "regret_sensitivity": 5, "leverage_comfort": 0, "goal_rigidity": 20, "emotional_volatility": 5, "decision_confidence": 10}},

    # ═══ FIXED DEPOSITS ═══
    {"code": "FD-01", "name": "HDFC Bank FD — 7.25% (3Y)", "category": "Fixed Deposit", "subcategory": "Bank FD",
     "description": "Guaranteed returns. Zero market risk. 3-year tenure. Premature withdrawal penalty applies.",
     "min_investment": 1, "lock_in_years": 3, "expected_return_range": "7.25% guaranteed", "risk_label": "Zero", "liquidity": "Premature withdrawal with penalty",
     "risk_vector": {"loss_aversion": 5, "horizon_tolerance": 30, "liquidity_sensitivity": 55, "behavioral_stability": 10, "ambiguity_tolerance": 5, "regret_sensitivity": 10, "leverage_comfort": 0, "goal_rigidity": 60, "emotional_volatility": 5, "decision_confidence": 15}},

    {"code": "FD-02", "name": "SBI FD — 6.8% (1Y)", "category": "Fixed Deposit", "subcategory": "Bank FD",
     "description": "1-year fixed deposit. Maximum safety. Fully taxable interest.",
     "min_investment": 1, "lock_in_years": 1, "expected_return_range": "6.8% guaranteed", "risk_label": "Zero", "liquidity": "1-year lock",
     "risk_vector": {"loss_aversion": 3, "horizon_tolerance": 15, "liquidity_sensitivity": 40, "behavioral_stability": 5, "ambiguity_tolerance": 3, "regret_sensitivity": 5, "leverage_comfort": 0, "goal_rigidity": 50, "emotional_volatility": 3, "decision_confidence": 10}},

    {"code": "FD-03", "name": "Bajaj Finance FD — 8.25% (3Y)", "category": "Fixed Deposit", "subcategory": "Corporate FD",
     "description": "Higher rate corporate FD. AAA rated. Slightly higher risk than bank FD but still very safe.",
     "min_investment": 0.25, "lock_in_years": 3, "expected_return_range": "8.25% guaranteed", "risk_label": "Very Low", "liquidity": "Premature withdrawal with penalty",
     "risk_vector": {"loss_aversion": 10, "horizon_tolerance": 32, "liquidity_sensitivity": 55, "behavioral_stability": 12, "ambiguity_tolerance": 10, "regret_sensitivity": 12, "leverage_comfort": 0, "goal_rigidity": 58, "emotional_volatility": 8, "decision_confidence": 18}},

    # ═══ PMS (Portfolio Management Services) ═══
    {"code": "PMS-01", "name": "Invesco India PMS - Growth", "category": "PMS", "subcategory": "Multi-cap",
     "description": "Concentrated portfolio of 15-20 high-conviction stocks. ₹50L minimum. Active stock picking.",
     "min_investment": 50, "lock_in_years": 0, "expected_return_range": "15-22%", "risk_label": "High", "liquidity": "Monthly redemption, 30-day notice",
     "risk_vector": {"loss_aversion": 72, "horizon_tolerance": 75, "liquidity_sensitivity": 65, "behavioral_stability": 65, "ambiguity_tolerance": 55, "regret_sensitivity": 50, "leverage_comfort": 25, "goal_rigidity": 30, "emotional_volatility": 60, "decision_confidence": 65}},

    {"code": "PMS-02", "name": "Marcellus Consistent Compounders PMS", "category": "PMS", "subcategory": "Large Cap Quality",
     "description": "10-15 clean, high-quality large caps with consistent earnings growth. Buy-and-hold philosophy.",
     "min_investment": 50, "lock_in_years": 0, "expected_return_range": "14-20%", "risk_label": "Moderately High", "liquidity": "Monthly redemption",
     "risk_vector": {"loss_aversion": 58, "horizon_tolerance": 72, "liquidity_sensitivity": 60, "behavioral_stability": 70, "ambiguity_tolerance": 45, "regret_sensitivity": 40, "leverage_comfort": 15, "goal_rigidity": 35, "emotional_volatility": 48, "decision_confidence": 62}},

    {"code": "PMS-03", "name": "Alchemy Capital High Growth PMS", "category": "PMS", "subcategory": "Mid & Small Cap",
     "description": "High-conviction mid and small cap PMS. Concentrated 12-15 stock portfolio. Higher volatility, higher potential.",
     "min_investment": 50, "lock_in_years": 0, "expected_return_range": "18-28%", "risk_label": "Very High", "liquidity": "Monthly, 30-day notice",
     "risk_vector": {"loss_aversion": 82, "horizon_tolerance": 80, "liquidity_sensitivity": 68, "behavioral_stability": 72, "ambiguity_tolerance": 62, "regret_sensitivity": 55, "leverage_comfort": 22, "goal_rigidity": 25, "emotional_volatility": 72, "decision_confidence": 68}},

    {"code": "PMS-04", "name": "ASK Indian Entrepreneur PMS", "category": "PMS", "subcategory": "Large Cap",
     "description": "Focus on owner-operated businesses. 15-20 stocks. Proven track record with established PMS house.",
     "min_investment": 50, "lock_in_years": 0, "expected_return_range": "14-18%", "risk_label": "High", "liquidity": "Monthly redemption",
     "risk_vector": {"loss_aversion": 62, "horizon_tolerance": 70, "liquidity_sensitivity": 62, "behavioral_stability": 62, "ambiguity_tolerance": 48, "regret_sensitivity": 42, "leverage_comfort": 18, "goal_rigidity": 32, "emotional_volatility": 52, "decision_confidence": 60}},

    # ═══ AIFs (Alternative Investment Funds) ═══
    {"code": "AIF-01", "name": "Edelweiss Crossover Opportunities AIF", "category": "AIF", "subcategory": "Category II - Pre-IPO",
     "description": "Pre-IPO and crossover fund. 5+ year commitment. ₹1Cr minimum. Limited liquidity. High return potential.",
     "min_investment": 100, "lock_in_years": 5, "expected_return_range": "18-30%", "risk_label": "Very High", "liquidity": "5-year lock, no interim liquidity",
     "risk_vector": {"loss_aversion": 80, "horizon_tolerance": 88, "liquidity_sensitivity": 88, "behavioral_stability": 75, "ambiguity_tolerance": 82, "regret_sensitivity": 55, "leverage_comfort": 50, "goal_rigidity": 18, "emotional_volatility": 70, "decision_confidence": 78}},

    {"code": "AIF-02", "name": "Kotak Pre-IPO Opportunities Fund", "category": "AIF", "subcategory": "Category II - Pre-IPO",
     "description": "Late-stage pre-IPO investments. ₹1Cr minimum. 3-5 year horizon. Strong due diligence process.",
     "min_investment": 100, "lock_in_years": 4, "expected_return_range": "20-35%", "risk_label": "Very High", "liquidity": "No interim liquidity",
     "risk_vector": {"loss_aversion": 78, "horizon_tolerance": 85, "liquidity_sensitivity": 85, "behavioral_stability": 72, "ambiguity_tolerance": 78, "regret_sensitivity": 52, "leverage_comfort": 45, "goal_rigidity": 20, "emotional_volatility": 68, "decision_confidence": 75}},

    {"code": "AIF-03", "name": "IIFL One Private Equity Fund", "category": "AIF", "subcategory": "Category II - PE",
     "description": "Private equity fund investing in unlisted growth companies. 7-year fund life. Quarterly NAV updates only.",
     "min_investment": 100, "lock_in_years": 7, "expected_return_range": "20-40%", "risk_label": "Very High", "liquidity": "7-year lock, quarterly updates",
     "risk_vector": {"loss_aversion": 85, "horizon_tolerance": 92, "liquidity_sensitivity": 92, "behavioral_stability": 80, "ambiguity_tolerance": 88, "regret_sensitivity": 58, "leverage_comfort": 55, "goal_rigidity": 15, "emotional_volatility": 72, "decision_confidence": 82}},

    {"code": "AIF-04", "name": "True Beacon One", "category": "AIF", "subcategory": "Category III - Long-Short",
     "description": "Hedged long-short equity fund. Lower drawdowns than pure equity. Absolute return focus.",
     "min_investment": 100, "lock_in_years": 1, "expected_return_range": "12-18%", "risk_label": "High", "liquidity": "Quarterly redemption",
     "risk_vector": {"loss_aversion": 55, "horizon_tolerance": 55, "liquidity_sensitivity": 60, "behavioral_stability": 58, "ambiguity_tolerance": 68, "regret_sensitivity": 42, "leverage_comfort": 60, "goal_rigidity": 28, "emotional_volatility": 48, "decision_confidence": 65}},

    # ═══ SIF (Specialized Investment Funds) ═══
    {"code": "SIF-01", "name": "SIF — Balanced Multi-Asset Allocation", "category": "SIF", "subcategory": "Balanced",
     "description": "SEBI's new Specialized Investment Fund. Balanced allocation across equity, debt, and alternatives. ₹10L minimum.",
     "min_investment": 10, "lock_in_years": 0, "expected_return_range": "10-15%", "risk_label": "Moderate", "liquidity": "Monthly",
     "risk_vector": {"loss_aversion": 45, "horizon_tolerance": 55, "liquidity_sensitivity": 50, "behavioral_stability": 50, "ambiguity_tolerance": 45, "regret_sensitivity": 35, "leverage_comfort": 15, "goal_rigidity": 45, "emotional_volatility": 40, "decision_confidence": 45}},

    {"code": "SIF-02", "name": "SIF — Aggressive Growth", "category": "SIF", "subcategory": "Growth",
     "description": "Growth-oriented SIF with 70%+ equity allocation. Active management with concentrated bets.",
     "min_investment": 10, "lock_in_years": 0, "expected_return_range": "14-22%", "risk_label": "High", "liquidity": "Monthly",
     "risk_vector": {"loss_aversion": 68, "horizon_tolerance": 68, "liquidity_sensitivity": 52, "behavioral_stability": 60, "ambiguity_tolerance": 55, "regret_sensitivity": 48, "leverage_comfort": 20, "goal_rigidity": 30, "emotional_volatility": 58, "decision_confidence": 55}},

    # ═══ BONDS / NCDs ═══
    {"code": "BOND-01", "name": "NHAI 54EC Capital Gains Bond", "category": "Bonds", "subcategory": "Tax-Free Bond",
     "description": "Section 54EC bond for capital gains tax exemption. 5-year lock-in. Low coupon but tax-free.",
     "min_investment": 0.5, "lock_in_years": 5, "expected_return_range": "5.25% tax-free", "risk_label": "Very Low", "liquidity": "5-year lock, no exit",
     "risk_vector": {"loss_aversion": 8, "horizon_tolerance": 50, "liquidity_sensitivity": 65, "behavioral_stability": 15, "ambiguity_tolerance": 8, "regret_sensitivity": 12, "leverage_comfort": 0, "goal_rigidity": 85, "emotional_volatility": 8, "decision_confidence": 20}},

    {"code": "BOND-02", "name": "Muthoot Finance NCD — 9.25%", "category": "Bonds", "subcategory": "Corporate NCD",
     "description": "Secured NCD from gold NBFC. Higher yield than bank FD. AA+ rated. 3-year maturity.",
     "min_investment": 1, "lock_in_years": 3, "expected_return_range": "9.25%", "risk_label": "Low to Moderate", "liquidity": "Listed on exchange but low volume",
     "risk_vector": {"loss_aversion": 18, "horizon_tolerance": 38, "liquidity_sensitivity": 50, "behavioral_stability": 18, "ambiguity_tolerance": 22, "regret_sensitivity": 18, "leverage_comfort": 5, "goal_rigidity": 55, "emotional_volatility": 15, "decision_confidence": 25}},

    {"code": "BOND-03", "name": "REC Tax-Free Bond (Secondary Market)", "category": "Bonds", "subcategory": "Tax-Free Bond",
     "description": "Government-backed REC tax-free bond. Available in secondary market. Long maturity (10-15Y remaining).",
     "min_investment": 1, "lock_in_years": 0, "expected_return_range": "5.5-6% tax-free", "risk_label": "Very Low", "liquidity": "Tradeable on exchange",
     "risk_vector": {"loss_aversion": 12, "horizon_tolerance": 60, "liquidity_sensitivity": 35, "behavioral_stability": 18, "ambiguity_tolerance": 15, "regret_sensitivity": 15, "leverage_comfort": 0, "goal_rigidity": 50, "emotional_volatility": 10, "decision_confidence": 22}},

    # ═══ INSURANCE-LINKED ═══
    {"code": "INS-01", "name": "HDFC Life Sanchay Plus — Guaranteed Income", "category": "Insurance", "subcategory": "Guaranteed Return Plan",
     "description": "Non-linked guaranteed income plan. Fixed payouts over 15-25 years. No market risk. Low returns.",
     "min_investment": 2, "lock_in_years": 10, "expected_return_range": "5-6% effective", "risk_label": "Zero (guaranteed)", "liquidity": "Surrender with heavy penalty",
     "risk_vector": {"loss_aversion": 3, "horizon_tolerance": 70, "liquidity_sensitivity": 80, "behavioral_stability": 8, "ambiguity_tolerance": 3, "regret_sensitivity": 8, "leverage_comfort": 0, "goal_rigidity": 90, "emotional_volatility": 3, "decision_confidence": 12}},

    {"code": "INS-02", "name": "Bajaj Allianz Life Goal Assure", "category": "Insurance", "subcategory": "ULIP",
     "description": "Unit-linked insurance plan with equity/debt fund options. 5-year lock-in. Insurance + investment combo.",
     "min_investment": 1, "lock_in_years": 5, "expected_return_range": "8-14%", "risk_label": "Moderate to High", "liquidity": "5-year mandatory lock",
     "risk_vector": {"loss_aversion": 40, "horizon_tolerance": 55, "liquidity_sensitivity": 65, "behavioral_stability": 38, "ambiguity_tolerance": 35, "regret_sensitivity": 32, "leverage_comfort": 5, "goal_rigidity": 72, "emotional_volatility": 35, "decision_confidence": 32}},

    # ═══ GIFT CITY / INTERNATIONAL ═══
    {"code": "GIFT-01", "name": "GIFT City International Bond Fund", "category": "GIFT City", "subcategory": "International Debt",
     "description": "USD-denominated bond fund domiciled in GIFT IFSC. Dollar returns + potential INR depreciation benefit.",
     "min_investment": 25, "lock_in_years": 0, "expected_return_range": "5-7% (USD)", "risk_label": "Moderate", "liquidity": "Monthly",
     "risk_vector": {"loss_aversion": 35, "horizon_tolerance": 50, "liquidity_sensitivity": 45, "behavioral_stability": 40, "ambiguity_tolerance": 58, "regret_sensitivity": 30, "leverage_comfort": 10, "goal_rigidity": 35, "emotional_volatility": 30, "decision_confidence": 48}},

    {"code": "GIFT-02", "name": "GIFT City Global Equity Feeder Fund", "category": "GIFT City", "subcategory": "International Equity",
     "description": "Global equity exposure through GIFT IFSC structure. Diversification beyond India.",
     "min_investment": 25, "lock_in_years": 0, "expected_return_range": "10-15% (USD)", "risk_label": "High", "liquidity": "Monthly",
     "risk_vector": {"loss_aversion": 55, "horizon_tolerance": 65, "liquidity_sensitivity": 48, "behavioral_stability": 55, "ambiguity_tolerance": 65, "regret_sensitivity": 38, "leverage_comfort": 12, "goal_rigidity": 30, "emotional_volatility": 50, "decision_confidence": 55}},

    # ═══ NPS ═══
    {"code": "NPS-01", "name": "NPS — Aggressive (Equity 75%)", "category": "NPS", "subcategory": "Active Choice",
     "description": "National Pension System with 75% equity allocation. Very long horizon (till 60). Tax benefits under 80CCD.",
     "min_investment": 0.01, "lock_in_years": 25, "expected_return_range": "10-14%", "risk_label": "Moderately High", "liquidity": "Locked till age 60 (partial withdrawal allowed)",
     "risk_vector": {"loss_aversion": 45, "horizon_tolerance": 90, "liquidity_sensitivity": 85, "behavioral_stability": 55, "ambiguity_tolerance": 35, "regret_sensitivity": 30, "leverage_comfort": 5, "goal_rigidity": 92, "emotional_volatility": 40, "decision_confidence": 35}},
]


def seed_database():
    """Seed the database with initial questions and products."""
    init_db()
    db = SessionLocal()

    try:
        # Check if already seeded
        existing_q = db.query(QuestionItem).count()
        if existing_q > 0:
            print(f"Database already has {existing_q} questions. Skipping seed.")
            return

        # Seed questions
        for q_data in SEED_QUESTIONS:
            q = QuestionItem(
                code=q_data["code"],
                tier=q_data["tier"],
                text=q_data["text"],
                rationale=q_data.get("rationale", ""),
                difficulty=q_data["difficulty"],
                discrimination=q_data["discrimination"],
                trait_weights=q_data["trait_weights"],
                options=q_data["options"],
                calibrates=q_data.get("calibrates"),
            )
            db.add(q)

        # Seed products
        for p_data in SEED_PRODUCTS:
            p = Product(
                code=p_data["code"],
                name=p_data["name"],
                category=p_data["category"],
                subcategory=p_data.get("subcategory"),
                description=p_data.get("description"),
                min_investment=p_data.get("min_investment"),
                lock_in_years=p_data.get("lock_in_years", 0),
                expected_return_range=p_data.get("expected_return_range"),
                risk_label=p_data.get("risk_label"),
                liquidity=p_data.get("liquidity"),
                risk_vector=p_data["risk_vector"],
                vector_source="manual",
            )
            db.add(p)

        db.commit()
        print(f"Seeded {len(SEED_QUESTIONS)} questions and {len(SEED_PRODUCTS)} products.")

    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
    finally:
        db.close()
