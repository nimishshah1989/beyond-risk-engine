import { useState, useEffect } from 'react'
import { Card, Badge, Btn, Bar, LoadingSpinner } from '../components/UI'
import { matchProducts } from '../services/api'
import { TRAITS } from '../data/traits'

// Asset class allocation logic based on behavioral profile
function computeAllocation(traits) {
  if (!traits) return null;
  const la = traits.loss_aversion || 50;
  const ht = traits.horizon_tolerance || 50;
  const ls = traits.liquidity_sensitivity || 50;
  const bs = traits.behavioral_stability || 50;
  const at = traits.ambiguity_tolerance || 50;
  const ev = traits.emotional_volatility || 50;
  const lc = traits.leverage_comfort || 50;
  const dc = traits.decision_confidence || 50;

  // Risk appetite composite (0-100, higher = more aggressive)
  const riskAppetite = Math.round(
    (100 - la) * 0.20 + ht * 0.20 + (100 - ls) * 0.10 +
    bs * 0.15 + at * 0.15 + (100 - ev) * 0.10 + lc * 0.05 + dc * 0.05
  );

  // Derive allocations
  let equity, debt, hybrid, alternatives, liquid;
  if (riskAppetite >= 70) {
    equity = { min: 55, max: 70, target: 62 };
    debt = { min: 10, max: 20, target: 15 };
    hybrid = { min: 5, max: 15, target: 8 };
    alternatives = { min: 5, max: 15, target: 10 };
    liquid = { min: 3, max: 8, target: 5 };
  } else if (riskAppetite >= 50) {
    equity = { min: 35, max: 50, target: 42 };
    debt = { min: 20, max: 30, target: 25 };
    hybrid = { min: 10, max: 20, target: 15 };
    alternatives = { min: 3, max: 10, target: 8 };
    liquid = { min: 5, max: 15, target: 10 };
  } else if (riskAppetite >= 30) {
    equity = { min: 20, max: 35, target: 28 };
    debt = { min: 30, max: 45, target: 35 };
    hybrid = { min: 15, max: 25, target: 20 };
    alternatives = { min: 0, max: 5, target: 2 };
    liquid = { min: 10, max: 20, target: 15 };
  } else {
    equity = { min: 5, max: 20, target: 12 };
    debt = { min: 40, max: 55, target: 48 };
    hybrid = { min: 15, max: 25, target: 20 };
    alternatives = { min: 0, max: 3, target: 0 };
    liquid = { min: 15, max: 25, target: 20 };
  }

  const riskLabel = riskAppetite >= 70 ? 'Aggressive' : riskAppetite >= 50 ? 'Moderate Growth' : riskAppetite >= 30 ? 'Conservative Growth' : 'Conservative';
  const riskColor = riskAppetite >= 70 ? '#dc2626' : riskAppetite >= 50 ? '#d97706' : riskAppetite >= 30 ? '#059669' : '#1746a2';

  return {
    riskAppetite, riskLabel, riskColor,
    classes: [
      { name: 'Equity', icon: '📈', target: equity.target, min: equity.min, max: equity.max, color: '#1746a2', categories: ['Equity MF', 'PMS'], desc: 'Growth engine — long-term capital appreciation through diversified equity exposure' },
      { name: 'Debt', icon: '🏛', target: debt.target, min: debt.min, max: debt.max, color: '#059669', categories: ['Debt MF', 'Bonds', 'Fixed Deposit'], desc: 'Stability anchor — regular income with capital preservation focus' },
      { name: 'Hybrid', icon: '⚖', target: hybrid.target, min: hybrid.min, max: hybrid.max, color: '#d97706', categories: ['Hybrid MF'], desc: 'Balance layer — dynamic equity-debt mix adjusts with market conditions' },
      { name: 'Alternatives', icon: '💎', target: alternatives.target, min: alternatives.min, max: alternatives.max, color: '#7c3aed', categories: ['AIF', 'GIFT City', 'NPS'], desc: 'Diversification — uncorrelated returns through alternative strategies' },
      { name: 'Liquid/Cash', icon: '💧', target: liquid.target, min: liquid.min, max: liquid.max, color: '#0891b2', categories: ['SIF', 'Insurance'], desc: 'Safety buffer — immediate accessibility for emergencies and opportunities' },
    ]
  };
}

function getRationale(traits, allocation) {
  if (!traits || !allocation) return [];
  const points = [];
  const la = traits.loss_aversion || 50;
  const ev = traits.emotional_volatility || 50;
  const ht = traits.horizon_tolerance || 50;
  const ls = traits.liquidity_sensitivity || 50;
  const bs = traits.behavioral_stability || 50;

  if (la > 65) points.push({ type: 'protection', text: `High loss aversion (${la}/100) — equity allocation capped at ${allocation.classes[0].max}% to reduce drawdown anxiety. Debt & hybrid form the core.` });
  else if (la < 35) points.push({ type: 'growth', text: `Low loss aversion (${la}/100) — comfortable with volatility, enabling higher equity allocation of ${allocation.classes[0].target}%.` });

  if (ev > 65) points.push({ type: 'caution', text: `High emotional volatility (${ev}/100) — recommending balanced/hybrid funds as primary vehicles to reduce portfolio visibility stress.` });

  if (ht > 65) points.push({ type: 'opportunity', text: `High horizon tolerance (${ht}/100) — can access longer lock-in products (PMS, AIF) with higher potential returns.` });
  else if (ht < 35) points.push({ type: 'constraint', text: `Low horizon tolerance (${ht}/100) — all recommended products are open-ended with no lock-in.` });

  if (ls > 65) points.push({ type: 'liquidity', text: `High liquidity sensitivity (${ls}/100) — maintaining ${allocation.classes[4].target}% in liquid/cash for psychological comfort.` });

  if (bs < 40) points.push({ type: 'guardrail', text: `Low behavioral stability (${bs}/100) — SIP-based deployment recommended over lumpsum to prevent timing-based decisions.` });

  points.push({ type: 'composite', text: `Overall risk appetite score: ${allocation.riskAppetite}/100 → ${allocation.riskLabel} profile. Allocation designed to maximize returns within the investor's behavioral comfort zone.` });

  return points;
}

export default function Strategy({ investorTraits, investorName, onViewProducts }) {
  const [matches, setMatches] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedClass, setExpandedClass] = useState(null);

  const allocation = computeAllocation(investorTraits);

  useEffect(() => {
    if (investorTraits) {
      setLoading(true);
      matchProducts(investorTraits).then(m => { setMatches(m); setLoading(false); }).catch(() => setLoading(false));
    }
  }, [investorTraits]);

  if (!investorTraits) {
    return (
      <div className="text-center py-20">
        <div className="text-4xl mb-3">🎯</div>
        <p className="text-gray-500 text-sm">No investor profile available.</p>
        <p className="text-gray-400 text-xs mt-1">Run a behavioral risk assessment first to generate recommendations.</p>
      </div>
    );
  }

  if (loading) return <LoadingSpinner />;

  const rationale = getRationale(investorTraits, allocation);

  // Group matched products by asset class
  const getTopProducts = (categories, n = 5) => {
    if (!matches) return [];
    return matches
      .filter(m => categories.some(c => m.category?.toLowerCase().includes(c.toLowerCase()) || m.subcategory?.toLowerCase().includes(c.toLowerCase())))
      .filter(m => m.recommendation === 'RECOMMENDED' || m.recommendation === 'CONDITIONAL')
      .slice(0, n);
  };

  const recColor = (label) => label === 'RECOMMENDED' ? '#059669' : label === 'CONDITIONAL' ? '#d97706' : '#dc2626';

  return (
    <div>
      {/* Header */}
      <Card className="mb-5 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-extrabold text-gray-900">Recommended Investment Strategy</h2>
            <p className="text-xs text-gray-500 mt-1">
              {investorName ? `For ${investorName} · ` : ''}Behavioral risk profile → Asset allocation → Best-fit products
            </p>
          </div>
          <div className="text-right">
            <div className="text-[10px] text-gray-400 uppercase font-bold">Risk Profile</div>
            <div className="text-lg font-extrabold" style={{ color: allocation.riskColor }}>{allocation.riskLabel}</div>
            <div className="text-[10px] text-gray-400">Score: {allocation.riskAppetite}/100</div>
          </div>
        </div>
      </Card>

      {/* Allocation donut + breakdown */}
      <div className="grid grid-cols-3 gap-4 mb-5">
        <Card className="col-span-2">
          <h3 className="text-sm font-bold mb-4">Target Asset Allocation</h3>
          <div className="space-y-3">
            {allocation.classes.map((ac, i) => (
              <div key={i} className="p-3 rounded-xl border border-gray-100 hover:bg-gray-50 transition-all cursor-pointer"
                onClick={() => setExpandedClass(expandedClass === i ? null : i)}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{ac.icon}</span>
                    <span className="text-sm font-bold text-gray-900">{ac.name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] text-gray-400">{ac.min}% – {ac.max}%</span>
                    <span className="text-lg font-extrabold" style={{ color: ac.color }}>{ac.target}%</span>
                  </div>
                </div>
                <Bar value={ac.target} max={100} color={ac.color} h={8} />
                <p className="text-[10.5px] text-gray-400 mt-1.5">{ac.desc}</p>

                {expandedClass === i && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="text-[10px] font-bold text-gray-400 uppercase mb-2">Top Recommended Products</div>
                    {getTopProducts(ac.categories).length > 0 ? (
                      <div className="space-y-2">
                        {getTopProducts(ac.categories).map((m, j) => (
                          <div key={j} className="flex items-center justify-between p-2.5 rounded-lg bg-white border border-gray-100">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-extrabold w-8" style={{ color: recColor(m.recommendation) }}>{m.fit_score}</span>
                              <div>
                                <div className="text-xs font-bold text-gray-900">{m.product_name}</div>
                                <div className="text-[10px] text-gray-400">{m.category} · {m.product_code}</div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge color={recColor(m.recommendation)}>{m.recommendation}</Badge>
                              {m.risk_label && <span className="text-[10px] text-gray-400">{m.risk_label}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 text-center py-2">No matched products in this category yet</p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>

        {/* Rationale */}
        <div className="space-y-4">
          <Card>
            <h3 className="text-sm font-bold mb-3">💡 Why This Allocation</h3>
            <p className="text-[10.5px] text-gray-400 mb-3">Each allocation decision is driven by your specific behavioral profile</p>
            <div className="space-y-2">
              {rationale.map((r, i) => {
                const icons = { protection: '🛡', growth: '📈', caution: '⚠️', opportunity: '💎', constraint: '🔒', liquidity: '💧', guardrail: '🚧', composite: '🎯' };
                const colors = { protection: '#1746a2', growth: '#059669', caution: '#d97706', opportunity: '#7c3aed', constraint: '#dc2626', liquidity: '#0891b2', guardrail: '#d97706', composite: '#1746a2' };
                return (
                  <div key={i} className="p-2.5 rounded-lg text-[11px] leading-relaxed" style={{ background: colors[r.type] + '08', border: `1px solid ${colors[r.type]}20` }}>
                    <span className="mr-1">{icons[r.type]}</span>
                    <span style={{ color: colors[r.type] }}>{r.text}</span>
                  </div>
                );
              })}
            </div>
          </Card>

          <Card>
            <h3 className="text-sm font-bold mb-3">📐 Behavioral Inputs</h3>
            <div className="space-y-2">
              {Object.entries(investorTraits).slice(0, 10).map(([k, v]) => {
                const t = TRAITS[k];
                const c = v >= 70 ? '#dc2626' : v >= 40 ? '#d97706' : '#059669';
                return (
                  <div key={k} className="flex items-center justify-between">
                    <span className="text-[10.5px] text-gray-500 truncate flex-1">{t?.name || k.replace(/_/g, ' ')}</span>
                    <div className="flex items-center gap-2 ml-2">
                      <div className="w-16"><Bar value={v} max={100} color={c} h={4} /></div>
                      <span className="text-[11px] font-bold w-6 text-right" style={{ color: c }}>{v}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      </div>

      {/* Deployment guidance */}
      <Card className="mb-5">
        <h3 className="text-sm font-bold mb-3">📋 Implementation Guidance</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="p-3 bg-blue-50 rounded-xl">
            <div className="text-[10px] font-bold text-blue-700 uppercase mb-1">Deployment Method</div>
            <div className="text-xs font-bold text-blue-900">
              {investorTraits.behavioral_stability < 40 ? 'SIP / Staggered (3 tranches over 3 months)' :
               investorTraits.loss_aversion > 65 ? 'Staggered (2 tranches over 2 months)' : 'Lumpsum + SIP for ongoing'}
            </div>
            <p className="text-[10px] text-blue-600 mt-1">Based on behavioral stability and loss aversion profile</p>
          </div>
          <div className="p-3 bg-green-50 rounded-xl">
            <div className="text-[10px] font-bold text-green-700 uppercase mb-1">Review Frequency</div>
            <div className="text-xs font-bold text-green-900">
              {investorTraits.emotional_volatility > 65 ? 'Quarterly (proactive calls during market events)' :
               investorTraits.emotional_volatility > 40 ? 'Semi-annual with event-triggered calls' : 'Annual review sufficient'}
            </div>
            <p className="text-[10px] text-green-600 mt-1">Based on emotional volatility and decision confidence</p>
          </div>
          <div className="p-3 bg-amber-50 rounded-xl">
            <div className="text-[10px] font-bold text-amber-700 uppercase mb-1">Communication Style</div>
            <div className="text-xs font-bold text-amber-900">
              {investorTraits.decision_confidence > 65 ? 'Collaborative — present data and options' : 'Directive — give clear recommendations'}
            </div>
            <p className="text-[10px] text-amber-600 mt-1">Based on decision confidence and regret sensitivity</p>
          </div>
        </div>
      </Card>

      {/* CTA */}
      <div className="flex gap-3">
        <Btn onClick={onViewProducts}>Browse Full Product Universe →</Btn>
      </div>
    </div>
  );
}
