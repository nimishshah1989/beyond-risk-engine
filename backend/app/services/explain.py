"""
Explanation Engine — generates advisor-facing insights, talking points,
conversation guides, and investor-facing plain-language explanations.
"""
from typing import Dict, List


def generate_advisor_insights(traits: Dict[str, int]) -> List[Dict]:
    """Generate detailed behavioral insights with recommendations."""
    insights = []

    la = traits.get("loss_aversion", 50)
    ht = traits.get("horizon_tolerance", 50)
    ls = traits.get("liquidity_sensitivity", 50)
    bs = traits.get("behavioral_stability", 50)
    at = traits.get("ambiguity_tolerance", 50)
    rs = traits.get("regret_sensitivity", 50)
    lc = traits.get("leverage_comfort", 50)
    gr = traits.get("goal_rigidity", 50)
    ev = traits.get("emotional_volatility", 50)
    dc = traits.get("decision_confidence", 50)

    if la > 70:
        insights.append({"trait": "Loss Aversion", "level": "High", "score": la,
            "insight": "This investor feels losses approximately 2-3x more intensely than equivalent gains. Recommendation framing should emphasize protection over growth.",
            "recommendation": "Use balanced/hybrid funds as core holding. Monthly or quarterly reporting only. Frame everything as capital protection first.",
            "investor_explanation": "You naturally feel the pain of losing money more than the joy of making money. This is completely normal — research shows most people do. Your portfolio is designed to protect what you've built while still growing over time."})
    elif la < 30:
        insights.append({"trait": "Loss Aversion", "level": "Low", "score": la,
            "insight": "Comfortable with volatility and drawdowns. Can access strategies with higher return potential.",
            "recommendation": "Can handle small cap, sectoral, and concentrated strategies. Frame opportunity cost of safety as a loss.",
            "investor_explanation": "You have an unusual ability to see market drops as opportunities rather than threats. This opens up higher-potential investments that most people can't handle emotionally."})

    if ht > 70:
        insights.append({"trait": "Horizon Tolerance", "level": "High", "score": ht,
            "insight": "Patient investor who understands compounding. Can access illiquid opportunities.",
            "recommendation": "Ideal for PMS, AIF, pre-IPO, and 5+ year strategies. Time is this investor's greatest asset.",
            "investor_explanation": "Your patience is a genuine competitive advantage. Most investors can't commit money for 5-7 years, which means you can access opportunities with higher potential that others miss."})
    elif ht < 35:
        insights.append({"trait": "Horizon Tolerance", "level": "Low", "score": ht,
            "insight": "Needs to see results within 1-2 years. Long lock-ins create significant anxiety.",
            "recommendation": "Open-ended funds only. Show performance frequently. Use monthly SIP statements as reinforcement.",
            "investor_explanation": "You prefer investments where you can see results relatively quickly. That's perfectly valid — your portfolio is built with accessible, liquid instruments that let you track progress regularly."})

    if bs > 70:
        insights.append({"trait": "Behavioral Stability", "level": "High", "score": bs,
            "insight": "Consistent decision-maker who won't panic-sell. A rare and valuable trait.",
            "recommendation": "Can use more aggressive strategies because behavior won't undermine them. Reduce touchpoints.",
            "investor_explanation": "You make consistently good decisions even when markets are volatile. This stability means your investments can compound without being interrupted by emotional reactions."})
    elif bs < 35:
        insights.append({"trait": "Behavioral Stability", "level": "Low", "score": bs,
            "insight": "Decisions change frequently based on recent events. Strategy quality matters less than ability to stick with it.",
            "recommendation": "Automated SIPs over lumpsum. Build 'cooling off' periods into any change request.",
            "investor_explanation": "You tend to react to recent market news, which can sometimes lead to changes that hurt long-term returns. We've built in systematic processes (like SIPs) that help remove emotion from the equation."})

    if ev > 70:
        insights.append({"trait": "Emotional Volatility", "level": "High (Critical)", "score": ev,
            "insight": "Strong emotional reactions to market events. #1 predictor of panic selling.",
            "recommendation": "PROACTIVE communication during every market event. Reduce portfolio visibility. Pre-agree on 'call before selling' protocol.",
            "investor_explanation": "Market movements affect your emotions significantly — this is very common and nothing to be concerned about. What matters is that your portfolio is designed so that even in a bad quarter, you can sleep well. And I'll always reach out to you proactively when markets move."})

    if rs > 65:
        insights.append({"trait": "Regret Sensitivity", "level": "Elevated", "score": rs,
            "insight": "Prone to disposition effect — holding losers too long, selling winners too early.",
            "recommendation": "Systematic rebalancing with pre-agreed rules. Never present multiple similar options.",
            "investor_explanation": "You sometimes worry about whether you made the 'right' investment choice. To help with this, we use systematic rules for when to buy and sell — taking the guesswork out of individual decisions."})

    if gr > 70:
        insights.append({"trait": "Goal Rigidity", "level": "High", "score": gr,
            "insight": "Investment decisions deeply tied to specific life goals. Each rupee has a purpose.",
            "recommendation": "Structure portfolio as goal-based buckets. Reference goal progress in every communication.",
            "investor_explanation": "Your investments are clearly linked to specific goals — your child's education, retirement, etc. We track each goal separately so you can see exactly how much progress you've making toward each one."})

    if dc > 75:
        insights.append({"trait": "Decision Confidence", "level": "High", "score": dc,
            "insight": "Values autonomy and trusts own analysis. Will push back on recommendations.",
            "recommendation": "Present options with analysis, not directives. They want a partner, not a prescriber.",
            "investor_explanation": "You have a strong analytical approach and trust your own research. I'll share my analysis and data with you, and we'll make decisions together."})
    elif dc < 30:
        insights.append({"trait": "Decision Confidence", "level": "Low", "score": dc,
            "insight": "Needs strong advisor guidance. Multiple options create paralysis.",
            "recommendation": "Give clear singular recommendations with confidence. Follow up to reinforce decisions were correct.",
            "investor_explanation": "I'll always give you a clear recommendation with my reasoning. You don't need to worry about comparing multiple options — I've done that analysis for you."})

    return insights


def generate_conversation_guide(traits: Dict[str, int]) -> Dict:
    """Generate communication style recommendations for the advisor."""
    dc = traits.get("decision_confidence", 50)
    ev = traits.get("emotional_volatility", 50)
    la = traits.get("loss_aversion", 50)
    gr = traits.get("goal_rigidity", 50)
    rs = traits.get("regret_sensitivity", 50)
    ls = traits.get("liquidity_sensitivity", 50)

    # Overall style
    if dc > 65:
        style = {
            "tone": "Collaborative & data-driven",
            "approach": "Present analysis and options. Let them feel ownership. Use 'the data suggests...' not 'you should...'",
            "avoid": "Being prescriptive or paternalistic. Don't over-explain basics.",
            "opening": "I've been analyzing your portfolio and found some interesting patterns. Let me share what the numbers are telling us..."
        }
    else:
        style = {
            "tone": "Warm, reassuring & directive",
            "approach": "Give clear singular recommendations with confidence. Use 'I recommend...' and 'Here's what I think is best...'",
            "avoid": "Presenting multiple options or complex trade-offs. This creates anxiety, not empowerment.",
            "opening": "I've done a thorough review and I have a clear recommendation I'm confident about..."
        }

    # Situational talking points
    points = []

    if ev > 65:
        points.append({"category": "Opening", "text": "Always start with what's going WELL. Lead with gains, stability, and goal progress before any recommendation involving risk."})
        points.append({"category": "Language", "text": "Use: 'protecting,' 'securing,' 'safeguarding.' Avoid: 'risk,' 'volatility,' 'potential loss.' Replace 'downside risk' with 'temporary price movement.'"})
    else:
        points.append({"category": "Opening", "text": "Can lead with the opportunity or analysis. This investor appreciates directness and isn't scared by honest risk discussion."})

    if la > 65:
        points.append({"category": "Framing", "text": "Frame ALL recommendations as capital protection first. Instead of 'this fund returned 22%,' say 'this fund protected capital in every major correction while still delivering strong returns.'"})
        points.append({"category": "Numbers", "text": "Lead with downside limits: 'Maximum historical drawdown was X%, recovery took Y months.' Give worst case first."})
    else:
        points.append({"category": "Framing", "text": "Frame around growth potential and opportunity cost. This investor responds to upside narrative."})

    if gr > 65:
        points.append({"category": "Structure", "text": "Connect every recommendation to a specific goal: 'This change moves your education fund from 68% to 74% of target.'"})

    if rs > 65:
        points.append({"category": "Decisions", "text": "Give ONE clear recommendation, not options. Say 'Based on my analysis, the best step is...' not 'You could do A or B.'"})
        points.append({"category": "Follow-up", "text": "After any action, proactively confirm: 'Good decision — here's why this was the right move.' Reduces post-decision anxiety."})

    if ls > 65:
        points.append({"category": "Safety Net", "text": "Before any investment discussion, acknowledge liquid reserves: 'Your emergency fund of ₹X is intact. Now, with the surplus...'"})

    return {"style": style, "points": points}
