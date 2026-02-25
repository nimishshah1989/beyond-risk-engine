import { useState } from 'react'
import { Card, Badge, Bar } from '../components/UI'

const sections = [
  { id: 'overview', label: 'Overview', icon: '🎯' },
  { id: 'traits', label: '10-Trait Model', icon: '🧬' },
  { id: 'questions', label: 'Question Design', icon: '📝' },
  { id: 'adaptive', label: 'Adaptive Testing (CAT)', icon: '🤖' },
  { id: 'scoring', label: 'Scoring & IRT', icon: '📐' },
  { id: 'flags', label: 'Behavioral Flags', icon: '⚠️' },
  { id: 'matching', label: 'Product Matching', icon: '🎯' },
  { id: 'allocation', label: 'Strategy Engine', icon: '📊' },
  { id: 'references', label: 'Research & References', icon: '📚' },
];

export default function Methodology() {
  const [active, setActive] = useState('overview');

  return (
    <div className="grid grid-cols-4 gap-4">
      <div className="col-span-1">
        <Card className="sticky top-20">
          <h3 className="text-xs font-bold text-gray-900 mb-3">Methodology Guide</h3>
          <div className="space-y-0.5">
            {sections.map(s => (
              <button key={s.id} onClick={() => setActive(s.id)}
                className={`w-full text-left px-2.5 py-2 rounded-lg text-xs transition-all ${active === s.id ? 'bg-blue-800 text-white font-bold' : 'text-gray-500 hover:bg-gray-50'}`}>
                <span className="mr-1.5">{s.icon}</span>{s.label}
              </button>
            ))}
          </div>
        </Card>
      </div>

      <div className="col-span-3 space-y-4">

        {active === 'overview' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Beyond Behavioral Risk Engine — How It Works</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Traditional risk profiling asks "How much risk can you take?" — a question most investors answer incorrectly because they confuse risk <em>capacity</em> (financial) with risk <em>tolerance</em> (behavioral). Our engine measures the behavioral dimension: how an investor actually behaves under uncertainty, loss, and complexity.
          </p>
          <div className="bg-blue-50 p-4 rounded-xl mb-4">
            <h4 className="text-xs font-bold text-blue-900 mb-2">The Core Insight</h4>
            <p className="text-xs text-blue-700 leading-relaxed">
              Investment returns are determined more by investor <strong>behavior</strong> than by product selection. A great fund in the hands of a panicky investor will underperform a mediocre fund held by a disciplined one. Our engine measures the behavioral traits that predict how an investor will <em>actually</em> behave — not how they <em>think</em> they'll behave.
            </p>
          </div>
          <h4 className="text-xs font-bold text-gray-900 mb-2">The Pipeline</h4>
          <div className="grid grid-cols-5 gap-2">
            {[
              { step: '1', title: 'Adaptive Assessment', desc: '15-25 scenario-based questions selected by AI' },
              { step: '2', title: '10-Trait Scoring', desc: 'IRT-weighted Bayesian estimation of behavioral traits' },
              { step: '3', title: 'Behavioral Flags', desc: 'Detect contradictions, risk patterns, flight risk' },
              { step: '4', title: 'Product Matching', desc: 'Asymmetric scoring against product demand vectors' },
              { step: '5', title: 'Strategy & Allocation', desc: 'Behavioral-optimal asset mix with rationale' },
            ].map(s => (
              <div key={s.step} className="p-3 bg-gray-50 rounded-xl text-center border border-gray-100">
                <div className="text-lg font-extrabold text-blue-800 mb-1">{s.step}</div>
                <div className="text-[10px] font-bold text-gray-800">{s.title}</div>
                <div className="text-[9px] text-gray-400 mt-1">{s.desc}</div>
              </div>
            ))}
          </div>
        </Card>)}

        {active === 'traits' && (<>
          <Card>
            <h2 className="text-base font-extrabold text-gray-900 mb-3">The 10-Trait Behavioral Model</h2>
            <p className="text-sm text-gray-600 leading-relaxed mb-4">
              Every investor is profiled across 10 behavioral dimensions. These are not personality types — they are measurable behavioral tendencies that directly predict investment behavior. Each trait is scored 0-100.
            </p>
          </Card>
          {[
            { name: 'Loss Aversion', icon: '🛡', science: 'Kahneman & Tversky Prospect Theory (1979). Losses felt 2-2.5x more than gains.', impact: 'High scorers need capital protection focus. Low scorers can access higher volatility.', example: 'Score 75: Portfolio dropping 15% feels like 35-40% emotionally. Downside protection essential.' },
            { name: 'Horizon Tolerance', icon: '⏳', science: 'Measures temporal discounting and myopic loss aversion (Thaler).', impact: 'Low scorers need open-ended liquid instruments. High scorers can access PMS, AIF, pre-IPO.', example: 'Score 25: Needs visible progress in 6-12 months. Monthly SIP statements as reinforcement.' },
            { name: 'Liquidity Sensitivity', icon: '💧', science: 'Security premium on liquid holdings beyond financial rationality.', impact: 'Determines cash/liquid allocation and product lock-in acceptability.', example: 'Score 80: Even 8% guaranteed returns won\'t compensate anxiety of locked capital.' },
            { name: 'Behavioral Stability', icon: '⚖', science: 'Measures recency bias, herding susceptibility. Strongest predictor of strategy execution.', impact: 'Low stability = SIPs and auto-rebalancing essential. Strategy quality matters less.', example: 'Score 30: Will want to change strategy after every market event. Build guardrails.' },
            { name: 'Ambiguity Tolerance', icon: '🌫', science: 'Ellsberg Paradox (1961). Preference for known vs unknown probabilities.', impact: 'Low scorers need FDs, guaranteed products. High scorers handle AIFs.', example: 'Score 20: Present exact scenarios with numbers. Never say "market will decide."' },
            { name: 'Regret Sensitivity', icon: '😰', science: 'Regret Theory (Loomes & Sugden 1982). Creates disposition effect.', impact: 'High scorers need ONE recommendation, not options. Systematic rebalancing.', example: 'Score 78: Offer 3 options and they\'ll pick one then worry about the other two.' },
            { name: 'Leverage Comfort', icon: '📊', science: 'Risk-seeking beyond standard volatility tolerance. Asymmetric payoff comfort.', impact: 'Determines suitability for margin, leveraged funds, concentrated bets.', example: 'Score 70 + LA 65: CONTRADICTION — comfortable in theory, panic when leveraged losses occur.' },
            { name: 'Goal Rigidity', icon: '🎯', science: 'Mental Accounting (Thaler 1985). Each rupee is earmarked.', impact: 'High scorers need goal-based buckets with per-goal progress tracking.', example: 'Score 85: "Daughter\'s education in 2028 — no delays." Portfolio MUST show path to goal.' },
            { name: 'Emotional Volatility', icon: '🎢', science: 'Strongest predictor of panic selling. Affect heuristic + attentional bias.', impact: 'High scorers need reduced visibility, proactive calls, "call before sell" protocol.', example: 'Score 82: CRITICAL. Monthly statements only. Call within 24hrs of 5%+ market drop.' },
            { name: 'Decision Confidence', icon: '💪', science: 'Locus of control. Calibration research (Barber & Odean 2001).', impact: 'Determines communication: directive (low) vs collaborative (high).', example: 'Score 25: Be directive — "I recommend X." This investor needs clear guidance.' },
          ].map((t, i) => (
            <Card key={i}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{t.icon}</span>
                <h3 className="text-sm font-extrabold text-gray-900">{t.name}</h3>
              </div>
              <div className="space-y-1.5">
                <div className="p-2 bg-purple-50 rounded-lg text-[10.5px]"><strong className="text-purple-700">Science:</strong> <span className="text-purple-800">{t.science}</span></div>
                <div className="p-2 bg-blue-50 rounded-lg text-[10.5px]"><strong className="text-blue-700">Impact:</strong> <span className="text-blue-800">{t.impact}</span></div>
                <div className="p-2 bg-amber-50 rounded-lg text-[10.5px]"><strong className="text-amber-700">Example:</strong> <span className="text-amber-800">{t.example}</span></div>
              </div>
            </Card>
          ))}
        </>)}

        {active === 'questions' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Question Design Philosophy</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Every question is a carefully designed behavioral scenario — not a self-report like "How much risk can you handle?" We present realistic financial situations and measure <em>revealed preferences</em>.
          </p>
          <h4 className="text-xs font-bold text-gray-900 mb-2">Three-Tier Architecture</h4>
          <div className="grid grid-cols-3 gap-3 mb-4">
            {[
              { tier: 'Anchor', color: '#1746a2', count: '5', desc: 'Always asked first. Establish baseline. Broad scenarios covering loss, time, uncertainty.' },
              { tier: 'Diagnostic', color: '#0891b2', count: '10-15', desc: 'AI-selected to maximize info gain. Targets traits with highest uncertainty. No two assessments identical.' },
              { tier: 'Calibration', color: '#d97706', count: '3-5', desc: 'Inserted every 3 diagnostics. Rephrase earlier scenarios to detect contradictions or random answers.' },
            ].map(t => (
              <div key={t.tier} className="p-3 rounded-xl" style={{ background: t.color + '08', border: `1px solid ${t.color}25` }}>
                <Badge color={t.color}>{t.tier}</Badge>
                <div className="text-xs font-bold text-gray-900 mt-2">{t.count} Questions</div>
                <p className="text-[10.5px] text-gray-600 mt-1">{t.desc}</p>
              </div>
            ))}
          </div>
          <h4 className="text-xs font-bold text-gray-900 mb-2">Question Properties</h4>
          <div className="space-y-2 text-xs text-gray-600">
            <p><strong>Trait Weights (0-3):</strong> Each question measures 1-3 traits. A "portfolio drops 20%" question has loss_aversion weight=3, emotional_volatility weight=1.5.</p>
            <p><strong>Difficulty (0-1):</strong> Easy questions (0.2) are answered similarly by most. Hard questions (0.8) differentiate moderate from high trait levels.</p>
            <p><strong>Discrimination (0.5-3.0):</strong> How well the question separates high from low. High discrimination = very informative.</p>
            <p><strong>Options:</strong> 4 choices, each assigning 0-100 to each measured trait. Designed as a gradient, not right/wrong.</p>
          </div>
        </Card>)}

        {active === 'adaptive' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Computerized Adaptive Testing (CAT)</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Instead of a fixed questionnaire, the engine uses CAT — the same technology behind GRE/GMAT. Each question is selected in real-time to maximize information gain.
          </p>
          <h4 className="text-xs font-bold text-gray-900 mb-2">The Algorithm</h4>
          <div className="bg-gray-900 p-4 rounded-xl mb-4 text-xs text-green-400 font-mono leading-relaxed">
            <p>1. Ask 5 ANCHOR questions (always the same)</p>
            <p>2. Compute initial trait scores and confidence</p>
            <p>3. Find trait with LOWEST confidence</p>
            <p>4. Select DIAGNOSTIC with highest:</p>
            <p className="ml-4">score = trait_weight × discrimination × (1 - confidence/100)</p>
            <p>5. Every 3 diagnostics → insert CALIBRATION</p>
            <p>6. Re-compute all traits after each answer</p>
            <p>7. STOP when: avg confidence ≥ 72% AND ≥ 15 questions</p>
            <p>8. Hard cap: 25 questions</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-green-50 rounded-lg">
              <div className="text-xs font-bold text-green-800">Fewer Questions, Same Accuracy</div>
              <p className="text-[10.5px] text-green-700 mt-1">Fixed questionnaires need 40+ questions. CAT achieves same accuracy in 15-25 by targeting uncertainty.</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <div className="text-xs font-bold text-green-800">Personalized Paths</div>
              <p className="text-[10.5px] text-green-700 mt-1">A cautious and aggressive investor get different questions, probing their specific patterns.</p>
            </div>
          </div>
        </Card>)}

        {active === 'scoring' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Scoring — IRT-Weighted Bayesian Estimation</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Not a simple average. Questions with higher discrimination and trait relevance count more heavily.
          </p>
          <h4 className="text-xs font-bold text-gray-900 mb-2">The Formula</h4>
          <div className="bg-gray-900 p-4 rounded-xl mb-4 text-xs text-green-400 font-mono leading-relaxed">
            <p className="text-gray-400">// For each trait:</p>
            <p>score = Σ(option_score × trait_weight × discrimination)</p>
            <p className="ml-8">/ Σ(trait_weight × discrimination)</p>
            <p className="mt-2 text-gray-400">// Confidence:</p>
            <p>confidence = min(95, 40 + relevant_question_count × 15)</p>
          </div>
          <h4 className="text-xs font-bold text-gray-900 mb-2">In Plain English</h4>
          <p className="text-xs text-gray-600 leading-relaxed mb-3">
            If you answer 3 questions measuring loss aversion: Q1 (weight 3, discrimination 2.0) counts 6x. Q2 (weight 1, discrimination 1.5) counts 1.5x. Q3 calibration (weight 0.5, discrimination 1.0) counts 0.5x. Final score = weighted average, not simple average.
          </p>
          <p className="text-xs text-gray-600">
            Confidence starts at 10%. After 1 question: ~55%. After 2: ~70%. After 4+: ~95%. Assessment stops at 72% average confidence across all traits.
          </p>
        </Card>)}

        {active === 'flags' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Behavioral Flag Detection</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Dangerous behavioral <em>combinations</em> that predict specific problems. Individual traits aren't "bad" — it's the interactions.
          </p>
          <div className="space-y-2">
            {[
              { flag: '🚨 Flight Risk', cond: 'LA > 75 AND EV > 65', danger: 'Highest predictor of panic selling at worst time.', action: 'Proactive calls within 24hrs of 5%+ drop. Downside-protected structures.' },
              { flag: '⚠️ Leverage-Loss Contradiction', cond: 'LC > 70 AND LA > 60', danger: 'Comfortable with leverage in theory but panics in leveraged losses.', action: 'Test tiny allocations first. Expect immediate exit demand if losses.' },
              { flag: '⚠️ Disposition Effect', cond: 'RS > 75', danger: 'Holds losers too long, sells winners too early.', action: 'Systematic rebalancing with pre-agreed rules. ONE recommendation only.' },
              { flag: '🚨 Extreme Volatility', cond: 'EV > 80', danger: '#1 predictor of permanent capital loss.', action: 'Quarterly visibility only. "Call before sell" protocol.' },
              { flag: 'ℹ️ Rigid Goals + Short Patience', cond: 'GR > 80 AND HT < 40', danger: 'Non-negotiable deadlines but won\'t wait.', action: 'Target-date funds, FMPs, structured maturity products.' },
            ].map((f, i) => (
              <div key={i} className="p-3 rounded-xl bg-gray-50 border border-gray-100">
                <div className="text-xs font-bold text-gray-900">{f.flag}</div>
                <div className="text-[10px] font-mono text-gray-400 mb-1">IF {f.cond}</div>
                <div className="text-[10.5px] text-red-700"><strong>Risk:</strong> {f.danger}</div>
                <div className="text-[10.5px] text-green-700"><strong>Action:</strong> {f.action}</div>
              </div>
            ))}
          </div>
        </Card>)}

        {active === 'matching' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Product Matching — Asymmetric Scoring</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Each product has a 10-dimensional demand vector. Matching uses asymmetric penalties because under-preparation is dangerous, over-preparation is just suboptimal.
          </p>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="p-3 bg-red-50 rounded-xl border border-red-200">
              <div className="text-xs font-bold text-red-800">Product demands MORE → 1.5x penalty</div>
              <p className="text-[10.5px] text-red-700 mt-1">Under-prepared investor in demanding product = panic selling, permanent loss.</p>
            </div>
            <div className="p-3 bg-green-50 rounded-xl border border-green-200">
              <div className="text-xs font-bold text-green-800">Investor has MORE → 0.7x penalty</div>
              <p className="text-[10.5px] text-green-700 mt-1">Over-prepared in simple product = leaving returns on table, but safe.</p>
            </div>
          </div>
          <div className="bg-gray-900 p-3 rounded-xl text-xs text-green-400 font-mono">
            <p>fit_score = 100 - avg(asymmetric_gaps)</p>
            <p>RECOMMENDED ≥ 75 | CONDITIONAL ≥ 55 | CAUTION {'<'} 55</p>
          </div>
        </Card>)}

        {active === 'allocation' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Strategy Engine — Behavioral-Optimal Allocation</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Translates traits into a target allocation designed to maximize what an investor can <em>actually stick with</em>.
          </p>
          <div className="bg-gray-900 p-3 rounded-xl mb-4 text-xs text-green-400 font-mono leading-relaxed">
            <p>risk_appetite = (100-LA)×0.20 + HT×0.20 + (100-LS)×0.10</p>
            <p className="ml-16">+ BS×0.15 + AT×0.15 + (100-EV)×0.10</p>
            <p className="ml-16">+ LC×0.05 + DC×0.05</p>
          </div>
          <div className="space-y-1.5">
            {[
              { label: 'Aggressive (70-100)', eq: '55-70%', debt: '10-20%', hy: '5-15%', alt: '5-15%', liq: '3-8%', color: '#dc2626' },
              { label: 'Moderate Growth (50-69)', eq: '35-50%', debt: '20-30%', hy: '10-20%', alt: '3-10%', liq: '5-15%', color: '#d97706' },
              { label: 'Conservative Growth (30-49)', eq: '20-35%', debt: '30-45%', hy: '15-25%', alt: '0-5%', liq: '10-20%', color: '#059669' },
              { label: 'Conservative (0-29)', eq: '5-20%', debt: '40-55%', hy: '15-25%', alt: '0-3%', liq: '15-25%', color: '#1746a2' },
            ].map(a => (
              <div key={a.label} className="flex items-center gap-2 p-2 rounded bg-gray-50 text-[10.5px]">
                <span className="font-bold w-40" style={{ color: a.color }}>{a.label}</span>
                <span className="w-16">Eq {a.eq}</span>
                <span className="w-16">Debt {a.debt}</span>
                <span className="w-16">Hy {a.hy}</span>
                <span className="w-14">Alt {a.alt}</span>
                <span className="w-14">Liq {a.liq}</span>
              </div>
            ))}
          </div>
        </Card>)}

        {active === 'references' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Research Foundations</h2>
          <div className="space-y-3">
            {[
              { title: 'Prospect Theory: An Analysis of Decision under Risk', authors: 'Kahneman & Tversky', year: '1979', journal: 'Econometrica', use: 'Loss aversion scoring foundation' },
              { title: 'Myopic Loss Aversion and the Equity Premium Puzzle', authors: 'Benartzi & Thaler', year: '1995', journal: 'QJE', use: 'Horizon tolerance measurement' },
              { title: 'Mental Accounting Matters', authors: 'Thaler', year: '1999', journal: 'J. Behavioral Decision Making', use: 'Goal rigidity trait design' },
              { title: 'Item Response Theory for Psychologists', authors: 'Embretson & Reise', year: '2000', journal: 'Lawrence Erlbaum', use: 'IRT scoring methodology' },
              { title: 'Trading Is Hazardous to Your Wealth', authors: 'Barber & Odean', year: '2000', journal: 'J. Finance', use: 'Decision confidence calibration' },
              { title: 'Regret Theory: An Alternative Theory of Rational Choice', authors: 'Loomes & Sugden', year: '1982', journal: 'Economic Journal', use: 'Regret sensitivity measurement' },
              { title: 'Risk as Feelings', authors: 'Loewenstein, Weber, Hsee, Welch', year: '2001', journal: 'Psychological Bulletin', use: 'Emotional volatility framework' },
              { title: 'Computerized Adaptive Testing: A Primer', authors: 'Wainer et al.', year: '2000', journal: 'Lawrence Erlbaum', use: 'CAT algorithm design' },
              { title: 'Ambiguity Aversion in the Small and in the Large', authors: 'Ellsberg', year: '1961', journal: 'QJE', use: 'Ambiguity tolerance measurement' },
              { title: 'Disposition to Sell Winners and Ride Losers', authors: 'Shefrin & Statman', year: '1985', journal: 'J. Finance', use: 'Behavioral flags for disposition effect' },
            ].map((r, i) => (
              <div key={i} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                <div className="text-xs font-bold text-gray-900">{r.title}</div>
                <div className="text-[10px] text-gray-500">{r.authors} ({r.year}) — {r.journal}</div>
                <div className="text-[10px] text-blue-600 mt-1">Used for: {r.use}</div>
              </div>
            ))}
          </div>
        </Card>)}

      </div>
    </div>
  );
}
