import { useState, useEffect } from 'react'
import { Card, RadarChart, Bar } from '../components/UI'
import { getComprehensiveReport } from '../services/api'

const BASE = import.meta.env.VITE_API_URL || '';

// ─── Sub-components ───

function ScoreCounter({ value, color }) {
  const [displayed, setDisplayed] = useState(0);
  useEffect(() => {
    if (!value) return;
    let frame = 0;
    const step = Math.max(1, Math.round(value / 30));
    const timer = setInterval(() => {
      frame += step;
      if (frame >= value) { setDisplayed(value); clearInterval(timer); }
      else setDisplayed(frame);
    }, 30);
    return () => clearInterval(timer);
  }, [value]);
  return <span className="text-6xl font-bold font-mono" style={{ color }}>{displayed}</span>;
}

function DimensionBar({ label, score, weight, delay = 0 }) {
  const pct = Math.min(100, Math.max(0, score || 0));
  const color = pct <= 30 ? '#dc2626' : pct <= 60 ? '#d97706' : '#059669';
  return (
    <div className="flex items-center gap-3 py-2">
      <div className="w-40 text-xs font-semibold text-slate-600 shrink-0">{label}</div>
      <div className="flex-1 bg-slate-100 rounded-full h-5 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: color, transitionDelay: `${delay}ms` }} />
      </div>
      <span className="text-sm font-bold font-mono w-10 text-right" style={{ color }}>{Math.round(pct)}</span>
      <span className="text-[10px] text-slate-400 w-10 text-right">{Math.round(weight * 100)}%</span>
    </div>
  );
}

function MatrixGrid({ cell, highLiquidity, highDrawdown }) {
  const cells = [
    { id: 'HL_HD', row: 0, col: 0, label: 'Liquid Growth' },
    { id: 'HL_LD', row: 1, col: 0, label: 'Capital-Protected Growth' },
    { id: 'LL_HD', row: 0, col: 1, label: 'Patient Capital' },
    { id: 'LL_LD', row: 1, col: 1, label: 'Structured Stability' },
  ];
  return (
    <div className="grid grid-cols-[auto_1fr_1fr] grid-rows-[auto_1fr_1fr] gap-0">
      <div />
      <div className="text-center text-[10px] font-bold text-slate-400 uppercase tracking-wider pb-2">High Liquidity Need</div>
      <div className="text-center text-[10px] font-bold text-slate-400 uppercase tracking-wider pb-2">Low Liquidity Need</div>
      <div className="flex items-center justify-center pr-3"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider" style={{ writingMode: 'vertical-lr', transform: 'rotate(180deg)' }}>High Drawdown OK</span></div>
      {cells.filter(c => c.row === 0).map(c => (
        <div key={c.id} className={`p-4 border rounded-xl text-center transition-all ${c.id === cell ? 'bg-teal-50 border-teal-400 shadow-sm' : 'bg-white border-slate-200 opacity-50'}`}>
          <p className={`text-sm font-bold ${c.id === cell ? 'text-teal-700' : 'text-slate-500'}`}>{c.label}</p>
        </div>
      ))}
      <div className="flex items-center justify-center pr-3"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider" style={{ writingMode: 'vertical-lr', transform: 'rotate(180deg)' }}>Low Drawdown OK</span></div>
      {cells.filter(c => c.row === 1).map(c => (
        <div key={c.id} className={`p-4 border rounded-xl text-center transition-all ${c.id === cell ? 'bg-teal-50 border-teal-400 shadow-sm' : 'bg-white border-slate-200 opacity-50'}`}>
          <p className={`text-sm font-bold ${c.id === cell ? 'text-teal-700' : 'text-slate-500'}`}>{c.label}</p>
        </div>
      ))}
    </div>
  );
}

function AllocationDonut({ equity, fixedIncome, alternatives, cash }) {
  const total = equity + fixedIncome + alternatives + cash;
  if (total === 0) return null;
  const slices = [
    { label: 'Equity', value: equity, color: '#C9A84C' },
    { label: 'Fixed Income', value: fixedIncome, color: '#5DADE2' },
    { label: 'Alternatives', value: alternatives, color: '#E8913A' },
    { label: 'Cash', value: cash, color: '#95A5A6' },
  ].filter(s => s.value > 0);

  const r = 80, cx = 100, cy = 100, strokeWidth = 28;
  const circumference = 2 * Math.PI * r;
  let offset = 0;

  return (
    <div className="flex items-center gap-8">
      <div className="relative">
        <svg width={200} height={200}>
          {slices.map((s, i) => {
            const dashLen = (s.value / total) * circumference;
            const dashStr = `${dashLen} ${circumference - dashLen}`;
            const el = (
              <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={s.color} strokeWidth={strokeWidth}
                strokeDasharray={dashStr} strokeDashoffset={-offset} transform={`rotate(-90 ${cx} ${cy})`} />
            );
            offset += dashLen;
            return el;
          })}
        </svg>
        <div className="absolute inset-0 flex items-center justify-center flex-col">
          <span className="text-2xl font-bold font-mono text-slate-800">{equity}%</span>
          <span className="text-[10px] text-slate-400">Equity</span>
        </div>
      </div>
      <div className="space-y-2">
        {slices.map(s => (
          <div key={s.label} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-sm" style={{ background: s.color }} />
            <span className="text-xs text-slate-600">{s.label}</span>
            <span className="text-xs font-bold font-mono text-slate-800 ml-auto">{s.value}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ApproachCard({ approach, isOpen, onToggle }) {
  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden">
      <button onClick={onToggle} className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-50 transition-colors">
        <div>
          <p className="text-sm font-bold text-slate-800">{approach.name}</p>
          <div className="flex gap-2 mt-1">
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">Risk: {approach.risk}</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-teal-50 text-teal-600">{approach.allocation_range}</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">{approach.horizon}</span>
          </div>
        </div>
        <span className="text-slate-400 text-xs">{isOpen ? '▼' : '▶'}</span>
      </button>
      {isOpen && (
        <div className="px-4 pb-4 border-t border-slate-100 pt-3">
          <p className="text-xs text-slate-600 leading-relaxed">{approach.description}</p>
          <p className="text-[10px] text-slate-400 mt-2">Suitable for: {approach.suitability}</p>
        </div>
      )}
    </div>
  );
}

function FlagCard({ flag }) {
  const styles = {
    critical: { bg: 'bg-red-50', border: 'border-red-200', icon: '🔴', title: 'text-red-700' },
    warning: { bg: 'bg-amber-50', border: 'border-amber-200', icon: '🟡', title: 'text-amber-700' },
    info: { bg: 'bg-blue-50', border: 'border-blue-200', icon: '🔵', title: 'text-blue-700' },
  };
  const s = styles[flag.type] || styles.info;
  return (
    <div className={`${s.bg} border ${s.border} rounded-xl p-4`}>
      <div className="flex items-start gap-2">
        <span>{s.icon}</span>
        <div>
          <p className={`text-sm font-bold ${s.title}`}>{flag.title}</p>
          <p className="text-xs text-slate-600 mt-1 leading-relaxed">{flag.explanation}</p>
          {flag.action && <p className="text-xs text-slate-500 mt-2 italic">Recommendation: {flag.action}</p>}
        </div>
      </div>
    </div>
  );
}

// ─── Skeleton ───

function ReportSkeleton() {
  return (
    <div className="max-w-4xl mx-auto space-y-4 mt-6">
      {[1,2,3,4,5].map(i => <div key={i} className="h-32 bg-slate-100 animate-pulse rounded-xl" />)}
    </div>
  );
}

// ─── Main Component ───

export default function ComprehensiveReport({ investorId, investorName, onViewProducts }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openApproach, setOpenApproach] = useState(null);

  useEffect(() => {
    if (!investorId) { setLoading(false); return; }
    getComprehensiveReport(investorId)
      .then(data => setReport(data?.data || data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [investorId]);

  if (loading) return <ReportSkeleton />;
  if (error) return (
    <div className="max-w-4xl mx-auto mt-10 text-center">
      <div className="text-3xl mb-3">📋</div>
      <p className="text-sm text-slate-500">{error}</p>
      <p className="text-xs text-slate-400 mt-1">Complete the Investor Profile to generate a comprehensive report.</p>
    </div>
  );
  if (!report) return null;

  const { composite_score, profile, dimensions, meaning_reveal, allocation, matrix, approaches, flags, wisdom, equity_ceiling, behavioral_profile } = report;
  const profileColor = profile?.color || '#C9A84C';

  // Build radar trait data from behavioral profile
  const traitData = {};
  if (behavioral_profile?.trait_scores) {
    Object.entries(behavioral_profile.trait_scores).forEach(([key, val]) => {
      traitData[key] = val?.score ?? 50;
    });
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5">

      {/* Header */}
      <div className="text-center py-2">
        <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Beyond &middot; Comprehensive Assessment</p>
        <h2 className="text-xl font-bold text-slate-800 mt-1">{investorName || 'Investor'}'s Wealth Assessment</h2>
      </div>

      {/* 1. Meaning Reveal */}
      {meaning_reveal?.meaning && (
        <Card>
          <div className="text-center py-4">
            <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-1">What money means to you</p>
            <p className="text-2xl font-bold text-teal-700">{meaning_reveal.label}</p>
            <p className="text-sm text-slate-500 mt-2 max-w-lg mx-auto leading-relaxed">{meaning_reveal.description}</p>
          </div>
        </Card>
      )}

      {/* 2. Profile Badge + Composite Score */}
      <Card>
        <div className="flex items-center justify-center gap-8 py-4">
          <div className="text-center">
            <span className="inline-block px-4 py-1.5 rounded-full text-sm font-bold text-white mb-3" style={{ background: profileColor }}>
              {profile?.label}
            </span>
            <div>
              <ScoreCounter value={composite_score} color={profileColor} />
              <p className="text-xl text-slate-400 font-mono">/100</p>
            </div>
            <p className="text-xs text-slate-500 mt-2">Composite Risk Score</p>
          </div>
        </div>
      </Card>

      {/* 3. Score Breakdown — 6 dimensions */}
      <Card>
        <h3 className="text-sm font-bold text-slate-800 mb-3">Score Breakdown</h3>
        <p className="text-xs text-slate-400 mb-4">Six dimensions weighted to produce your composite score</p>
        <div>
          {(dimensions || []).map((d, i) => (
            <DimensionBar key={d.label} label={d.label} score={d.score} weight={d.weight} delay={i * 120} />
          ))}
        </div>
        {equity_ceiling?.constraints?.length > 0 && (
          <div className="mt-4 bg-amber-50 rounded-lg p-3 border border-amber-200">
            <p className="text-xs font-bold text-amber-700 mb-1">Hard Constraints Applied</p>
            {equity_ceiling.constraints.map((c, i) => (
              <p key={i} className="text-[10px] text-amber-600">{c}</p>
            ))}
          </div>
        )}
      </Card>

      {/* 4. Liquidity x Drawdown Matrix */}
      {matrix && (
        <Card>
          <h3 className="text-sm font-bold text-slate-800 mb-1">Your Investment Matrix Position</h3>
          <p className="text-xs text-slate-400 mb-4">Liquidity need vs drawdown tolerance determines your strategy family</p>
          <MatrixGrid cell={matrix.cell} highLiquidity={matrix.high_liquidity} highDrawdown={matrix.high_drawdown} />
          <div className="mt-4 bg-teal-50 rounded-lg p-4 border border-teal-200">
            <p className="text-sm font-bold text-teal-700">{matrix.label}</p>
            <p className="text-xs text-slate-500 mt-0.5">{matrix.subtitle}</p>
            <p className="text-xs text-slate-600 mt-2 leading-relaxed">{matrix.description}</p>
          </div>
        </Card>
      )}

      {/* 5. Behavioral Flags */}
      {flags?.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-slate-800 mb-3">Behavioral Flags</h3>
          <p className="text-xs text-slate-400 mb-4">Important observations about your risk profile</p>
          <div className="space-y-3">
            {flags.map((f, i) => <FlagCard key={i} flag={f} />)}
          </div>
        </Card>
      )}

      {/* 6. Recommended Allocation */}
      {allocation && (
        <Card>
          <h3 className="text-sm font-bold text-slate-800 mb-1">Recommended Asset Allocation</h3>
          <p className="text-xs text-slate-400 mb-4">Based on your composite score of {composite_score}</p>
          <div className="flex flex-col md:flex-row gap-8 items-start">
            <AllocationDonut equity={allocation.equity} fixedIncome={allocation.fixed_income} alternatives={allocation.alternatives} cash={allocation.cash} />
            {allocation.equity > 0 && allocation.equity_sub_allocation && (
              <div className="flex-1">
                <p className="text-xs font-semibold text-slate-500 mb-2">Equity Sub-Allocation</p>
                <table className="w-full">
                  <tbody>
                    {Object.entries(allocation.equity_sub_allocation).map(([key, val]) => (
                      <tr key={key} className="border-b border-slate-100">
                        <td className="py-1.5 text-xs text-slate-600">{key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</td>
                        <td className="py-1.5 text-xs font-bold font-mono text-right text-slate-800">{val}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* 7. Investment Approaches */}
      {approaches?.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-slate-800 mb-1">Suitable Investment Approaches</h3>
          <p className="text-xs text-slate-400 mb-4">Regulatory-safe strategies matched to your profile — not product recommendations</p>
          <div className="space-y-2">
            {approaches.map((a, i) => (
              <ApproachCard key={i} approach={a} isOpen={openApproach === i} onToggle={() => setOpenApproach(openApproach === i ? null : i)} />
            ))}
          </div>
        </Card>
      )}

      {/* 8. Trait Radar */}
      {Object.keys(traitData).length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-slate-800 mb-3">Behavioral Trait Profile</h3>
          <p className="text-xs text-slate-400 mb-2">10-dimensional behavioral fingerprint from games and transaction analysis</p>
          <RadarChart traits={traitData} size={300} />
          <p className="text-[10px] text-slate-400 text-center mt-2">Data source: {behavioral_profile?.data_sources || 'Pending'}</p>
        </Card>
      )}

      {/* 9. Wisdom */}
      {wisdom && (
        <Card>
          <div className="text-center py-4 max-w-lg mx-auto">
            <p className="text-lg text-slate-700 italic leading-relaxed">"{wisdom.quote}"</p>
            <p className="text-xs text-slate-400 mt-2">— {wisdom.author}</p>
            <div className="mt-4 bg-slate-50 rounded-lg p-4">
              <p className="text-xs text-slate-600 leading-relaxed">{wisdom.insight}</p>
            </div>
          </div>
        </Card>
      )}

      {/* 10. Product Matching CTA */}
      <Card>
        <div className="text-center py-6">
          <p className="text-sm text-slate-500 mb-3">Ready to explore products matched to your profile?</p>
          <button onClick={onViewProducts}
            className="bg-teal-600 text-white font-medium px-8 py-3 rounded-lg hover:bg-teal-700 transition-colors text-sm">
            Explore Matching Products →
          </button>
        </div>
      </Card>

    </div>
  );
}
