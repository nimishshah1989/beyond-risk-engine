export const TRAITS = {
  loss_aversion: {
    name: 'Loss Aversion',
    icon: '🛡',
    description: 'How intensely you feel losses vs. equivalent gains. High = losses hurt much more than gains feel good.',
    low: 'Handles losses well; won\'t panic sell. Comfortable with volatile assets.',
    mid: 'Normal sensitivity to losses. May need reassurance in deep drawdowns.',
    high: 'Losses feel 2-3x more painful than gains. Likely to exit at worst time. Needs capital protection focus.',
    advisor_tip: 'For high scorers: frame gains as "protecting what you\'ve built" not "maximizing returns".'
  },
  horizon_tolerance: {
    name: 'Horizon Tolerance',
    icon: '⏳',
    description: 'Willingness to wait for long-term outcomes without needing interim results.',
    low: 'Needs frequent visible progress. Dislikes lock-ins. Wants quarterly milestones.',
    mid: 'Can wait 3-5 years with periodic check-ins and milestone tracking.',
    high: 'True long-term thinker. Comfortable with 7-10yr lock-ins. Rare and valuable trait.',
    advisor_tip: 'Low scorers need quarterly review calls showing progress, even if small.'
  },
  liquidity_sensitivity: {
    name: 'Liquidity Sensitivity',
    icon: '💧',
    description: 'How much comfort you derive from being able to access your money quickly.',
    low: 'Comfortable locking money away. Fine with PMS/AIF structures.',
    mid: 'Wants some liquidity buffer but can tolerate partial lock-ins.',
    high: 'Needs to know money is accessible. Will sacrifice returns for liquidity. FD-heavy mindset.',
    advisor_tip: 'High scorers: always maintain a visible "emergency fund" before locking anything.'
  },
  behavioral_stability: {
    name: 'Behavioral Stability',
    icon: '⚖',
    description: 'Consistency of financial decisions across market conditions and emotional states.',
    low: 'Decisions change with market mood. May chase trends or panic. Needs guardrails.',
    mid: 'Generally steady but may waver during extreme events.',
    high: 'Rock-solid decision maker. Sticks to plan regardless of noise. Ideal for systematic strategies.',
    advisor_tip: 'Low stability + high AUM = flight risk. Schedule proactive calls before market events.'
  },
  ambiguity_tolerance: {
    name: 'Ambiguity Tolerance',
    icon: '🌫',
    description: 'Comfort with uncertain outcomes and products that don\'t have guaranteed returns.',
    low: 'Wants certainty. Prefers FDs, guaranteed products. Dislikes "it depends" answers.',
    mid: 'Can handle moderate uncertainty with proper framing and range estimates.',
    high: 'Comfortable with uncertain outcomes. Fine with venture-style risk/reward profiles.',
    advisor_tip: 'Low tolerance: always present scenarios with numbers. Never say "market will decide".'
  },
  regret_sensitivity: {
    name: 'Regret Sensitivity',
    icon: '😰',
    description: 'How much you dwell on "what if I had done X instead" after making a decision.',
    low: 'Makes decisions and moves on. Doesn\'t second-guess.',
    mid: 'Occasional regret but manageable. Prefers having 2-3 options to choose from.',
    high: 'Agonizes over decisions. Paralyzed by FOMO. May delay action indefinitely.',
    advisor_tip: 'High regret: give exactly 2 options (not 5). Reduce choice paralysis.'
  },
  leverage_comfort: {
    name: 'Leverage Comfort',
    icon: '📊',
    description: 'Willingness to use borrowed money or amplified strategies for higher returns.',
    low: 'Debt-averse. Won\'t touch leveraged products. Conservative capital structure.',
    mid: 'Moderate comfort. May accept leverage in real estate but not in financial products.',
    high: 'Comfortable with margin, leverage, and amplified bets. Understands asymmetric outcomes.',
    advisor_tip: 'Even high-comfort clients: never recommend leverage above 40% without stress testing.'
  },
  goal_rigidity: {
    name: 'Goal Rigidity',
    icon: '🎯',
    description: 'How fixed your financial goals are vs. willingness to adjust them based on conditions.',
    low: 'Flexible goals. "I\'ll figure it out." May lack motivation for disciplined investing.',
    mid: 'Has clear goals but can adjust timelines if markets underperform.',
    high: 'Non-negotiable goals. "My daughter\'s education in 2028 — no delays." Very specific targets.',
    advisor_tip: 'High rigidity: ensure portfolio ALWAYS has a path to goals. Shortfall = trust erosion.'
  },
  emotional_volatility: {
    name: 'Emotional Volatility',
    icon: '🎢',
    description: 'How much your emotional state swings in response to portfolio changes.',
    low: 'Calm and composed. Barely notices 5-10% swings. Ideal for volatile allocations.',
    mid: 'Notices market moves but doesn\'t overreact. May call during significant events.',
    high: 'Emotional rollercoaster. Excited in bull runs, terrified in corrections. Needs constant hand-holding.',
    advisor_tip: 'High volatility: reduce portfolio visibility frequency. Monthly statements, not daily apps.'
  },
  decision_confidence: {
    name: 'Decision Confidence',
    icon: '💪',
    description: 'How much you trust your own financial judgment vs. relying on advisor guidance.',
    low: 'Fully dependent on advisor. Won\'t act without explicit recommendation. Delegation mindset.',
    mid: 'Trusts advisor but wants to understand rationale. Collaborative decision-making.',
    high: 'Self-assured. May override advisor advice. Researches independently. Needs to feel in control.',
    advisor_tip: 'Low confidence: be directive ("I recommend X"). High: be consultative ("Here are the options").'
  }
};

export const TRAIT_IDS = Object.keys(TRAITS);

export const RISK_LABELS = {
  conservative: { color: '#059669', bg: '#ecfdf5', label: 'Conservative' },
  moderate: { color: '#d97706', bg: '#fffbeb', label: 'Moderate' },
  aggressive: { color: '#dc2626', bg: '#fef2f2', label: 'Aggressive' },
};

export function getOverallRiskLabel(traits) {
  const risky = (traits.loss_aversion || 50) + (traits.emotional_volatility || 50) + (traits.liquidity_sensitivity || 50);
  const tolerant = (traits.horizon_tolerance || 50) + (traits.ambiguity_tolerance || 50) + (traits.leverage_comfort || 50);
  const ratio = risky / (tolerant + 1);
  if (ratio > 2) return 'conservative';
  if (ratio > 1.2) return 'moderate';
  return 'aggressive';
}
