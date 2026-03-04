import { useState } from 'react'
import { Card, Badge, Bar } from '../components/UI'

const sections = [
  { id: 'overview', label: 'Overview', icon: '🎯' },
  { id: 'journey', label: 'Assessment Journey', icon: '🧭' },
  { id: 'meaning', label: 'Meaning of Money', icon: '💎' },
  { id: 'traits', label: '10-Trait Model', icon: '🧬' },
  { id: 'games', label: 'Behavioral Games', icon: '🎮' },
  { id: 'composite', label: 'Composite Scoring', icon: '📐' },
  { id: 'matrix', label: 'Liquidity x Drawdown Matrix', icon: '📊' },
  { id: 'approaches', label: 'Investment Approaches', icon: '🏛️' },
  { id: 'flags', label: 'Behavioral Flags', icon: '⚠️' },
  { id: 'matching', label: 'Product Matching', icon: '🎯' },
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
                className={`w-full text-left px-2.5 py-2 rounded-lg text-xs transition-all ${active === s.id ? 'bg-teal-700 text-white font-bold' : 'text-gray-500 hover:bg-gray-50'}`}>
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
            Traditional risk profiling asks "How much risk can you take?" — a question most investors answer incorrectly because they confuse risk <em>capacity</em> (financial) with risk <em>tolerance</em> (behavioral). Our engine goes deeper: understanding what money <em>means</em> to you, what you <em>fear</em>, how you've <em>actually behaved</em> under stress, and what your financial reality <em>allows</em>.
          </p>
          <div className="bg-teal-50 p-4 rounded-xl mb-4 border border-teal-200">
            <h4 className="text-xs font-bold text-teal-900 mb-2">The Core Insight</h4>
            <p className="text-xs text-teal-700 leading-relaxed">
              Investment returns are determined more by investor <strong>behavior</strong> than by product selection. A great fund in the hands of a panicky investor will underperform a mediocre fund held by a disciplined one. Our engine measures the behavioral traits that predict how an investor will <em>actually</em> behave — not how they <em>think</em> they'll behave.
            </p>
          </div>
          <h4 className="text-xs font-bold text-gray-900 mb-2">The Assessment Pipeline</h4>
          <div className="grid grid-cols-3 gap-2">
            {[
              { step: '1', title: 'Investor Profile', desc: 'Financial reality, emotional drivers, fears, knowledge, and experience' },
              { step: '2', title: 'Behavioral Games', desc: '4 psychometric games measuring unconscious preferences' },
              { step: '3', title: 'Comprehensive Report', desc: '6-dimension composite score, allocation, and approaches' },
            ].map(s => (
              <div key={s.step} className="p-3 bg-gray-50 rounded-xl text-center border border-gray-100">
                <div className="text-lg font-extrabold text-teal-700 mb-1">{s.step}</div>
                <div className="text-[10px] font-bold text-gray-800">{s.title}</div>
                <div className="text-[9px] text-gray-400 mt-1">{s.desc}</div>
              </div>
            ))}
          </div>
        </Card>)}

        {active === 'journey' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">The Investor Journey</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            A systematic guided flow that takes an investor from raw data to a transparent, actionable assessment report.
          </p>
          <div className="space-y-3">
            {[
              { step: 'Step 1: Investor Profile', desc: 'Nine sections capturing the complete investor picture. Starts with emotional drivers (what money means, deepest fears, regret patterns), moves to knowledge and experience, then financial reality (income, obligations, assets, loss history, aspirations, decision structure). The financial capacity score acts as a HARD CEILING on risk allocation.', badge: '9 Sections' },
              { step: 'Step 2: Behavioral Games', desc: 'Four psychometric games adapted from behavioral economics research. Risk Tolerance (Falk GPS Staircase), Loss Aversion (Adaptive Bisection), Time Preference (Koffarnus Adjusting Delay), and Herding (Social Proof). 19-22 trials in ~2.5 minutes. Measures unconscious preferences — harder to game than questionnaires.', badge: '~2.5 min' },
              { step: 'Step 3: Comprehensive Report', desc: 'All data sources are fused via Bayesian Normal-Normal conjugate updating. The 6-dimension composite score combines financial capacity, behavioral patterns, fear-risk coherence, money meaning, knowledge, and market cycle. The report includes allocation recommendations, investment approaches, and behavioral flags — all in plain language.', badge: 'Transparent' },
            ].map(s => (
              <div key={s.step} className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="text-xs font-bold text-gray-900">{s.step}</h4>
                  {s.badge && <Badge color="#0d9488">{s.badge}</Badge>}
                </div>
                <p className="text-[10.5px] text-gray-600 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </Card>)}

        {active === 'meaning' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Meaning of Money Framework</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Before any numbers, we ask: what does money <em>mean</em> to this person? The answer shapes every recommendation. An investor seeking security needs fundamentally different products than one chasing the game of wealth creation.
          </p>
          <h4 className="text-xs font-bold text-gray-900 mb-2">Five Money Archetypes</h4>
          <div className="space-y-2 mb-4">
            {[
              { icon: '🛡️', label: 'Security', score: 25, desc: 'Money means never worrying. Portfolio must feel safe above all. Conservative allocation, capital protection focus.' },
              { icon: '🌊', label: 'Freedom', score: 45, desc: 'Money means options. Invest to maximize optionality and avoid trapped capital. Balanced approach.' },
              { icon: '✨', label: 'Lifestyle', score: 50, desc: 'Money means living well. Returns must fund experiences and comfort. Goal-linked investing.' },
              { icon: '🏔️', label: 'Legacy', score: 60, desc: 'Money means building something lasting. Multi-generational compounding. Patient, growth-oriented.' },
              { icon: '📈', label: 'The Game', score: 80, desc: 'Money is the score. Enjoys the building process. Aggressive, conviction-driven strategies.' },
            ].map(m => (
              <div key={m.label} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 border border-gray-100">
                <span className="text-xl">{m.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-gray-900">{m.label}</span>
                    <span className="text-[10px] font-mono text-teal-600">Risk Score: {m.score}</span>
                  </div>
                  <p className="text-[10.5px] text-gray-600 mt-0.5">{m.desc}</p>
                </div>
              </div>
            ))}
          </div>
          <h4 className="text-xs font-bold text-gray-900 mb-2">Fear-Risk Coherence</h4>
          <p className="text-xs text-gray-600 leading-relaxed mb-3">
            We measure whether an investor's fears align with their risk tolerance. The most dangerous combination: fear of missing out (FOMO) paired with panic response to drawdowns. This "expectation-fear conflict" is the #1 predictor of buying high and selling low.
          </p>
          <div className="bg-gray-900 p-3 rounded-xl text-xs text-green-400 font-mono leading-relaxed">
            <p className="text-gray-400">// Coherence Score (0-100)</p>
            <p>coherence = fear_score × 0.40</p>
            <p className="ml-10">+ impact_score × 0.35</p>
            <p className="ml-10">+ regret_score × 0.25</p>
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

        {active === 'games' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Behavioral Games — Measuring the Unconscious</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Four adaptive games adapted from behavioral economics research. Unlike questionnaires, games measure <em>revealed preferences</em> through choices — harder to game, more accurate.
          </p>
          <div className="space-y-3">
            {[
              { name: 'Risk Tolerance (Falk GPS Staircase)', trials: 5, desc: 'Binary choice: guaranteed amount vs 50% chance of larger payoff. Adaptive bisection converges to your switching point in 5 trials.', output: 'risk_tolerance_score (0-100)', sigma: '12.0' },
              { name: 'Loss Aversion (Adaptive Bisection)', trials: 6, desc: 'Accept or reject 50/50 gambles with varying gain/loss ratios. Converges to your loss aversion lambda — how much more losses hurt vs gains.', output: 'loss_aversion_lambda (1.0-4.0)', sigma: '10.0' },
              { name: 'Time Preference (Koffarnus Adjusting Delay)', trials: 5, desc: 'Choose between money now vs more money later with varying delays. Measures your discount rate — how much you value present vs future.', output: 'time_preference_k (discount rate)', sigma: '14.0' },
              { name: 'Herding (Social Proof)', trials: 6, desc: 'Make choices with and without social signals ("87% chose X"). Measures whether your decisions shift toward the crowd.', output: 'herding_index (0-1)', sigma: '20.0' },
            ].map(g => (
              <div key={g.name} className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-xs font-bold text-gray-900">{g.name}</h4>
                  <Badge color="#0d9488">{g.trials} trials</Badge>
                </div>
                <p className="text-[10.5px] text-gray-600 leading-relaxed">{g.desc}</p>
                <div className="flex gap-4 mt-2">
                  <span className="text-[10px] font-mono text-teal-600">Output: {g.output}</span>
                  <span className="text-[10px] font-mono text-slate-400">Sigma: {g.sigma}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>)}

        {active === 'composite' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">6-Dimension Composite Scoring</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            The composite risk score combines six independent dimensions, each measuring a different facet of risk capacity and tolerance. This is not a simple average — each dimension is weighted by its predictive importance.
          </p>
          <h4 className="text-xs font-bold text-gray-900 mb-2">The Master Formula</h4>
          <div className="bg-gray-900 p-4 rounded-xl mb-4 text-xs text-green-400 font-mono leading-relaxed">
            <p>Composite Score (0-100) =</p>
            <p className="ml-4">Financial Capacity  × <span className="text-yellow-400">25%</span></p>
            <p className="ml-4">Behavioral Pattern   × <span className="text-yellow-400">25%</span></p>
            <p className="ml-4">Fear-Risk Coherence  × <span className="text-yellow-400">20%</span></p>
            <p className="ml-4">Money Meaning        × <span className="text-yellow-400">15%</span></p>
            <p className="ml-4">Knowledge            × <span className="text-yellow-400">10%</span></p>
            <p className="ml-4">Market Cycle         × <span className="text-yellow-400"> 5%</span></p>
          </div>
          <div className="space-y-2 mb-4">
            {[
              { dim: 'Financial Capacity (25%)', desc: 'Structural ability to bear risk: liquidity runway, obligation coverage, time horizon, income stability, net worth. Acts as HARD CEILING — behavioral willingness cannot exceed structural capacity.' },
              { dim: 'Behavioral Pattern (25%)', desc: 'Actual behavior under stress from games and transaction analysis. Past downturn actions, drop reactions, recovery patterns. Transaction data (narrow CI) overrides stated preferences.' },
              { dim: 'Fear-Risk Coherence (20%)', desc: 'Internal consistency between fears and tolerance. Worst fear mapped to risk score, 30% portfolio drop impact, regret preference. Detects dangerous mismatches like FOMO + panic.' },
              { dim: 'Money Meaning (15%)', desc: 'Emotional driver: Security (25), Freedom (45), Lifestyle (50), Legacy (60), Game (80). Shapes the entire recommendation framework.' },
              { dim: 'Knowledge & Experience (10%)', desc: 'Knowledge level (Basic/Intermediate/Advanced/Expert) + breadth of investment experience across asset classes. 60% knowledge + 40% experience.' },
              { dim: 'Market Cycle (5%)', desc: 'Current market regime adjustment. Expansion, Consolidation, or Contraction affects the recommended risk level slightly.' },
            ].map(d => (
              <div key={d.dim} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                <h5 className="text-xs font-bold text-gray-900">{d.dim}</h5>
                <p className="text-[10.5px] text-gray-600 mt-1">{d.desc}</p>
              </div>
            ))}
          </div>
          <h4 className="text-xs font-bold text-gray-900 mb-2">Hard Constraints (Equity Ceiling)</h4>
          <div className="space-y-1.5 text-[10.5px] text-gray-600">
            <p>Emergency fund {'<'} 3 months → equity capped at 40%</p>
            <p>Time horizon {'<'} 1 year → equity capped at 10%</p>
            <p>Wealth concentration {'>'} 60% → equity reduced by 15%</p>
            <p>Wealth concentration {'>'} 80% → equity reduced by 25%</p>
            <p>No equity experience → composite capped at 60</p>
            <p>Expectation-fear conflict → composite capped at 50</p>
          </div>
        </Card>)}

        {active === 'matrix' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Liquidity x Drawdown Matrix</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Investors are positioned in a 2x2 matrix based on two critical dimensions: how much they need access to their money (liquidity) and how much portfolio volatility they can stomach (drawdown tolerance).
          </p>
          <div className="grid grid-cols-2 gap-3 mb-4">
            {[
              { cell: 'Liquid Growth (HL_HD)', desc: 'Need liquidity + handle volatility. Diversified equity, global allocation, concentrated quality.', color: '#059669' },
              { cell: 'Patient Capital (LL_HD)', desc: 'Can lock money + handle volatility. Private markets, long-horizon compounding, thematic conviction.', color: '#7c3aed' },
              { cell: 'Capital-Protected Growth (HL_LD)', desc: 'Need liquidity + low volatility. Bond strategies, low-vol equity, dynamic allocation.', color: '#0891b2' },
              { cell: 'Structured Stability (LL_LD)', desc: 'Can lock money + low volatility. Structured returns, target-date approaches, defined outcomes.', color: '#d97706' },
            ].map(c => (
              <div key={c.cell} className="p-3 rounded-xl border border-gray-200" style={{ borderLeftWidth: 4, borderLeftColor: c.color }}>
                <h5 className="text-xs font-bold text-gray-900">{c.cell}</h5>
                <p className="text-[10.5px] text-gray-600 mt-1">{c.desc}</p>
              </div>
            ))}
          </div>
          <div className="bg-gray-900 p-3 rounded-xl text-xs text-green-400 font-mono">
            <p>High Liquidity = upcoming obligations {'>'} 0 OR horizon {'<'} 7 years</p>
            <p>High Drawdown OK = behavioral_score {'>'}= 55 AND coherence {'>'}= 50</p>
          </div>
        </Card>)}

        {active === 'approaches' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Investment Approaches — Regulatory-Safe</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Instead of recommending specific products (which requires SEBI RIA registration), we recommend <em>approaches</em> — strategy families suited to the investor's profile. Each approach has a minimum profile tier.
          </p>
          <div className="space-y-2">
            {[
              { tier: 'Tier 0 — All Profiles', approaches: ['Capital Protection Strategy', 'Income Generation Approach', 'Gold & Real Asset Allocation'], color: '#059669' },
              { tier: 'Tier 1 — Moderate-Conservative+', approaches: ['Low-Volatility Equity Strategy', 'Dynamic Asset Allocation'], color: '#0891b2' },
              { tier: 'Tier 2 — Moderate+', approaches: ['Diversified Growth Strategy', 'Global Equity Allocation', 'Concentrated Quality Strategy'], color: '#d97706' },
              { tier: 'Tier 3 — Moderate-Aggressive+', approaches: ['Long-Horizon Compounding', 'Private Markets Access', 'Thematic & Sectoral Conviction'], color: '#dc2626' },
            ].map(t => (
              <div key={t.tier} className="p-3 rounded-xl border border-gray-200" style={{ borderLeftWidth: 4, borderLeftColor: t.color }}>
                <h5 className="text-xs font-bold" style={{ color: t.color }}>{t.tier}</h5>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {t.approaches.map(a => (
                    <span key={a} className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{a}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 bg-amber-50 rounded-xl border border-amber-200">
            <h5 className="text-xs font-bold text-amber-800">Special Approaches</h5>
            <p className="text-[10.5px] text-amber-700 mt-1"><strong>Legacy meaning + intermediate knowledge+:</strong> Intergenerational Wealth Framework — 20+ year multi-generational compounding</p>
            <p className="text-[10.5px] text-amber-700 mt-0.5"><strong>Security meaning:</strong> All-Weather Portfolio — performs adequately in all market regimes</p>
          </div>
        </Card>)}

        {active === 'flags' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Behavioral Flag Detection</h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Dangerous behavioral <em>combinations</em> and structural gaps that predict specific problems. Flags are generated from both the composite analysis and the 10-trait model.
          </p>
          <div className="space-y-2">
            {[
              { flag: '🔴 Expectation-Fear Conflict', cond: 'FOMO fear + panic/anxious impact', danger: '#1 predictor of buying high and selling low. The investor wants returns but cannot handle the volatility required.', action: 'Cap composite at 50. Start conservative, increase only after surviving a real drawdown.' },
              { flag: '🟡 Unproven Under Stress', cond: 'No equity experience', danger: 'Stated risk tolerance is theoretical. Many discover their true tolerance only during their first crash.', action: 'Begin with lower equity than model suggests. Use SIPs. Real profile emerges after first correction.' },
              { flag: '🟡 Over-Concentrated', cond: 'Wealth concentration > 60%', danger: 'A major drawdown here affects entire financial life, not just this portfolio.', action: 'Reduce concentration before increasing risk. Diversify across instruments and asset classes.' },
              { flag: '🔴 Insufficient Safety Net', cond: 'Emergency fund < 6 months', danger: 'Job loss, health crisis, or market downturn could force liquidation at worst time.', action: 'Build emergency fund to 6-12 months before any equity allocation. More important than returns.' },
              { flag: '🔴 Flight Risk', cond: 'LA > 75 AND EV > 65', danger: 'Highest predictor of panic selling at worst time.', action: 'Proactive calls within 24hrs of 5%+ drop. Downside-protected structures.' },
              { flag: '⚠️ Leverage-Loss Contradiction', cond: 'LC > 70 AND LA > 60', danger: 'Comfortable with leverage in theory but panics in leveraged losses.', action: 'Test tiny allocations first. Expect immediate exit demand if losses occur.' },
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
            Each product has a 10-dimensional demand vector. Matching uses asymmetric penalties because under-preparation is dangerous, over-preparation is just suboptimal. Think of it as an investor-product "marriage compatibility" score.
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
            <p>RECOMMENDED {'≥'} 75 | CONDITIONAL {'≥'} 55 | CAUTION {'<'} 55</p>
          </div>
        </Card>)}

        {active === 'references' && (<Card>
          <h2 className="text-base font-extrabold text-gray-900 mb-3">Research Foundations</h2>
          <div className="space-y-3">
            {[
              { title: 'Prospect Theory: An Analysis of Decision under Risk', authors: 'Kahneman & Tversky', year: '1979', journal: 'Econometrica', use: 'Loss aversion scoring, fear-risk coherence' },
              { title: 'Myopic Loss Aversion and the Equity Premium Puzzle', authors: 'Benartzi & Thaler', year: '1995', journal: 'QJE', use: 'Horizon tolerance, time preference games' },
              { title: 'Mental Accounting Matters', authors: 'Thaler', year: '1999', journal: 'J. Behavioral Decision Making', use: 'Goal rigidity, money meaning framework' },
              { title: 'Item Response Theory for Psychologists', authors: 'Embretson & Reise', year: '2000', journal: 'Lawrence Erlbaum', use: 'IRT scoring methodology' },
              { title: 'Trading Is Hazardous to Your Wealth', authors: 'Barber & Odean', year: '2000', journal: 'J. Finance', use: 'Decision confidence, overtrading metrics' },
              { title: 'Regret Theory: An Alternative Theory of Rational Choice', authors: 'Loomes & Sugden', year: '1982', journal: 'Economic Journal', use: 'Regret sensitivity, regret preference scoring' },
              { title: 'Risk as Feelings', authors: 'Loewenstein, Weber, Hsee, Welch', year: '2001', journal: 'Psychological Bulletin', use: 'Emotional volatility, fear landscape design' },
              { title: 'Ambiguity Aversion in the Small and in the Large', authors: 'Ellsberg', year: '1961', journal: 'QJE', use: 'Ambiguity tolerance measurement' },
              { title: 'Disposition to Sell Winners and Ride Losers', authors: 'Shefrin & Statman', year: '1985', journal: 'J. Finance', use: 'Transaction scoring, disposition effect' },
              { title: 'The Most Important Thing', authors: 'Howard Marks', year: '2011', journal: 'Columbia Business School', use: 'Risk management philosophy, wisdom quotes' },
            ].map((r, i) => (
              <div key={i} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                <div className="text-xs font-bold text-gray-900">{r.title}</div>
                <div className="text-[10px] text-gray-500">{r.authors} ({r.year}) — {r.journal}</div>
                <div className="text-[10px] text-teal-600 mt-1">Used for: {r.use}</div>
              </div>
            ))}
          </div>
        </Card>)}

      </div>
    </div>
  );
}
