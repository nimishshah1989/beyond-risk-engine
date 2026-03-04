import { useState, useEffect } from 'react'
import { Card, Badge, Bar, RadarChart } from '../components/UI'
import { getComprehensiveReport, getProfile, getProfileHistory, getCommentary } from '../services/api'
import { TRAITS, TRAIT_IDS } from '../data/traits'

const SRC_COLORS = { FUSED: '#0d9488', PSYCHOMETRIC_ONLY: '#2563eb', TRANSACTION_ONLY: '#d97706', NONE: '#94a3b8' };
const INVERTED = new Set(['horizon_tolerance', 'behavioral_stability', 'ambiguity_tolerance', 'decision_confidence']);
const scoreColor = (v, trait) => {
  if (v == null) return '#94a3b8';
  const inv = INVERTED.has(trait);
  if (v >= 61) return inv ? '#059669' : '#dc2626';
  if (v >= 31) return '#d97706';
  return inv ? '#dc2626' : '#059669';
};
const fmt = (d) => d ? new Date(d).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';

function Skeleton({ className = '' }) {
  return <div className={`bg-slate-100 animate-pulse rounded-xl ${className}`} />;
}

function ReportSkeleton() {
  return (
    <div className="max-w-4xl mx-auto space-y-4 mt-4">
      {[1,2,3,4,5].map(i => <Skeleton key={i} className="h-32" />)}
    </div>
  );
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

function AllocationDonut({ equity, fixedIncome, alternatives, cash }) {
  const total = equity + fixedIncome + alternatives + cash;
  if (total === 0) return null;
  const slices = [
    { label: 'Equity', value: equity, color: '#C9A84C' },
    { label: 'Fixed Income', value: fixedIncome, color: '#5DADE2' },
    { label: 'Alternatives', value: alternatives, color: '#E8913A' },
    { label: 'Cash', value: cash, color: '#95A5A6' },
  ].filter(s => s.value > 0);
  const r = 70, cx = 85, cy = 85, strokeWidth = 24;
  const circumference = 2 * Math.PI * r;
  let offset = 0;
  return (
    <div className="flex items-center gap-6">
      <svg width={170} height={170}>
        {slices.map((s, i) => {
          const dashLen = (s.value / total) * circumference;
          const el = <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={s.color} strokeWidth={strokeWidth}
            strokeDasharray={`${dashLen} ${circumference - dashLen}`} strokeDashoffset={-offset} transform={`rotate(-90 ${cx} ${cy})`} />;
          offset += dashLen;
          return el;
        })}
        <text x={cx} y={cy - 4} textAnchor="middle" className="text-xl font-bold font-mono" fill="#1e293b">{equity}%</text>
        <text x={cx} y={cy + 12} textAnchor="middle" className="text-[10px]" fill="#94a3b8">Equity</text>
      </svg>
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

function MatrixGrid({ cell }) {
  const cells = [
    { id: 'HL_HD', row: 0, col: 0, label: 'Liquid Growth' },
    { id: 'HL_LD', row: 1, col: 0, label: 'Capital-Protected Growth' },
    { id: 'LL_HD', row: 0, col: 1, label: 'Patient Capital' },
    { id: 'LL_LD', row: 1, col: 1, label: 'Structured Stability' },
  ];
  return (
    <div className="grid grid-cols-2 gap-2">
      {cells.map(c => (
        <div key={c.id} className={`p-3 border rounded-lg text-center transition-all ${c.id === cell ? 'bg-teal-50 border-teal-400' : 'bg-white border-slate-200 opacity-50'}`}>
          <p className={`text-xs font-bold ${c.id === cell ? 'text-teal-700' : 'text-slate-500'}`}>{c.label}</p>
        </div>
      ))}
    </div>
  );
}

export default function InvestorReport({ investorId, investorName, onViewProducts }) {
  const [report, setReport] = useState(null);
  const [profile, setProfile] = useState(null);
  const [commentary, setCommentary] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [commentaryLoading, setCommentaryLoading] = useState(false);
  const [openApproach, setOpenApproach] = useState(null);

  useEffect(() => {
    if (!investorId) { setLoading(false); return; }
    Promise.all([
      getComprehensiveReport(investorId).catch(() => null),
      getProfile(investorId).catch(() => null),
      getProfileHistory(investorId).catch(() => null),
      getCommentary(investorId).catch(() => null),
    ]).then(([rep, prof, hist, comm]) => {
      setReport(rep?.data || rep);
      setProfile(prof?.data || prof);
      setHistory((hist?.data || []).slice(0, 5));
      setCommentary(comm?.data || null);
    }).catch(e => setError(e.message)).finally(() => setLoading(false));
  }, [investorId]);

  const handleRegenerate = async () => {
    setCommentaryLoading(true);
    try {
      const result = await getCommentary(investorId, true);
      setCommentary(result?.data || null);
    } catch { /* silent */ }
    setCommentaryLoading(false);
  };

  if (loading) return <ReportSkeleton />;
  if (!investorId) return <div className="text-center py-20"><p className="text-sm text-slate-500">Select an investor from the Dashboard to view their report.</p></div>;
  if (error) return <div className="text-center py-20"><p className="text-sm text-slate-500">{error}</p><p className="text-xs text-slate-400 mt-1">Complete the Investor Profile first.</p></div>;

  const r = report || {};
  const p = profile || {};
  const { composite_score, dimensions, allocation, matrix, approaches, flags, wisdom, equity_ceiling } = r;
  const profileLabel = r.profile?.label;
  const profileColor = r.profile?.color || '#0d9488';
  const dataSources = r.data_sources || {};

  // Build trait scores
  const tsRaw = p.trait_scores || {};
  const ts = {};
  Object.entries(tsRaw).forEach(([k, v]) => { ts[k] = typeof v === 'object' && v !== null ? v.score : v; });

  const sdDetails = p.say_do_details || {};

  return (
    <div className="max-w-4xl mx-auto space-y-5">

      {/* 1. Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-800">{investorName || 'Investor'}</h2>
            <div className="flex items-center gap-2 mt-1.5">
              {profileLabel && <span className="text-xs font-bold px-3 py-1 rounded-full text-white" style={{ background: profileColor }}>{profileLabel}</span>}
              <Badge color={SRC_COLORS[p.data_sources] || '#94a3b8'}>{(p.data_sources || 'PENDING').replace(/_/g, ' ')}</Badge>
            </div>
          </div>
          {composite_score != null && (
            <div className="text-right">
              <span className="text-5xl font-bold font-mono" style={{ color: profileColor }}>{Math.round(composite_score)}</span>
              <p className="text-xs text-slate-400 mt-0.5">Composite Risk Score /100</p>
            </div>
          )}
        </div>
        {/* Data source badges */}
        <div className="flex gap-3 mt-4 pt-3 border-t border-slate-100">
          {Object.entries(dataSources).map(([key, src]) => {
            if (!src?.available) return null;
            const labels = { games: 'Games', transactions: 'Transactions', questionnaire: 'Questionnaire', financial_context: 'Financial Context' };
            const details = [];
            if (src.trials) details.push(`${src.trials} trials`);
            if (src.n_transactions) details.push(`${src.n_transactions} txns`);
            if (src.questions) details.push(`${src.questions} Qs`);
            if (src.confidence) details.push(src.confidence);
            return (
              <div key={key} className="flex items-center gap-1.5 text-[10px]">
                <div className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                <span className="font-bold text-slate-600">{labels[key] || key}</span>
                {details.length > 0 && <span className="text-slate-400">{details.join(' / ')}</span>}
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. AI Commentary */}
      <Card>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-slate-800">AI Advisory Briefing</h3>
          <button onClick={handleRegenerate} disabled={commentaryLoading}
            className="text-[10px] font-bold text-teal-600 hover:text-teal-700 disabled:text-slate-400 transition-colors">
            {commentaryLoading ? 'Generating...' : 'Regenerate'}
          </button>
        </div>
        {commentary ? (
          <div className="space-y-4">
            {commentary.one_line_summary && (
              <p className="text-sm font-semibold text-teal-700 bg-teal-50 rounded-lg px-4 py-2 border border-teal-200">
                {commentary.one_line_summary}
              </p>
            )}
            {commentary.behavioral_summary && <p className="text-xs text-slate-600 leading-relaxed">{commentary.behavioral_summary}</p>}
            <div className="grid grid-cols-2 gap-4">
              {commentary.key_risks?.length > 0 && (
                <div>
                  <p className="text-[10px] font-bold text-red-600 uppercase tracking-wider mb-2">Key Risks</p>
                  <ul className="space-y-1">
                    {commentary.key_risks.map((r, i) => <li key={i} className="text-[11px] text-slate-600 flex gap-1.5"><span className="text-red-400 shrink-0">!</span>{r}</li>)}
                  </ul>
                </div>
              )}
              {commentary.conversation_starters?.length > 0 && (
                <div>
                  <p className="text-[10px] font-bold text-blue-600 uppercase tracking-wider mb-2">Conversation Starters</p>
                  <ul className="space-y-1">
                    {commentary.conversation_starters.map((s, i) => <li key={i} className="text-[11px] text-slate-600 italic">&ldquo;{s}&rdquo;</li>)}
                  </ul>
                </div>
              )}
            </div>
            {commentary.investment_guardrails?.length > 0 && (
              <div>
                <p className="text-[10px] font-bold text-amber-600 uppercase tracking-wider mb-2">Investment Guardrails</p>
                <div className="flex flex-wrap gap-2">
                  {commentary.investment_guardrails.map((g, i) => (
                    <span key={i} className="text-[10px] bg-amber-50 text-amber-700 px-2.5 py-1 rounded-lg border border-amber-200">{g}</span>
                  ))}
                </div>
              </div>
            )}
            {commentary.say_do_analysis && (
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Say-Do Analysis</p>
                <p className="text-[11px] text-slate-600 leading-relaxed">{commentary.say_do_analysis}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-6">
            <p className="text-xs text-slate-400">AI commentary not yet generated.</p>
            <button onClick={handleRegenerate} disabled={commentaryLoading}
              className="mt-2 text-xs font-bold text-teal-600 hover:text-teal-700 disabled:text-slate-400">
              {commentaryLoading ? 'Generating...' : 'Generate Now'}
            </button>
          </div>
        )}
      </Card>

      {/* 3. Score Breakdown — 6 dimensions */}
      {dimensions?.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-slate-800 mb-3">Score Breakdown</h3>
          <div>
            {dimensions.map((d, i) => (
              <DimensionBar key={d.label} label={d.label} score={d.score} weight={d.weight} delay={i * 120} />
            ))}
          </div>
          {equity_ceiling?.constraints?.length > 0 && (
            <div className="mt-4 bg-amber-50 rounded-lg p-3 border border-amber-200">
              <p className="text-xs font-bold text-amber-700 mb-1">Hard Constraints</p>
              {equity_ceiling.constraints.map((c, i) => <p key={i} className="text-[10px] text-amber-600">{c}</p>)}
            </div>
          )}
        </Card>
      )}

      {/* 4. Radar + Trait Scores */}
      {Object.keys(ts).length > 0 && (
        <div className="grid grid-cols-2 gap-5">
          <Card>
            <h3 className="text-sm font-bold text-slate-800 mb-2">Behavioral Radar</h3>
            <RadarChart traits={ts} size={260} />
            <p className="text-[10px] text-slate-400 text-center mt-2">Data: {p.data_sources || 'Pending'}</p>
          </Card>
          <Card className="overflow-hidden p-0">
            <div className="px-5 pt-5 pb-2"><h3 className="text-sm font-bold text-slate-800">Trait Scores</h3></div>
            <table className="w-full text-xs">
              <thead><tr className="border-b border-slate-200">
                <th className="text-left px-5 py-2 text-[10px] font-semibold text-slate-400 uppercase">Trait</th>
                <th className="px-2 py-2 text-[10px] font-semibold text-slate-400 uppercase w-28">Score</th>
                <th className="px-2 py-2 text-[10px] font-semibold text-slate-400 uppercase text-right">CI</th>
              </tr></thead>
              <tbody>
                {TRAIT_IDS.map(id => {
                  const v = ts[id]; if (v == null) return null;
                  const raw = tsRaw[id] || {};
                  return (
                    <tr key={id} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="px-5 py-1.5 font-medium text-slate-700">{TRAITS[id]?.icon} {TRAITS[id]?.name}</td>
                      <td className="px-2 py-1.5">
                        <div className="flex items-center gap-2">
                          <div className="flex-1"><Bar value={v} max={100} color={scoreColor(v, id)} h={4} /></div>
                          <span className="font-mono font-bold w-6 text-right" style={{ color: scoreColor(v, id) }}>{Math.round(v)}</span>
                        </div>
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono text-slate-400 text-[10px]">{raw.ci_lower != null ? `${raw.ci_lower}\u2013${raw.ci_upper}` : '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* 5. Say-Do Gap */}
      {p.data_sources === 'FUSED' && Object.keys(sdDetails).length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-slate-800 mb-3">Say-Do Gap Analysis</h3>
          <p className="text-xs text-slate-400 mb-4">Comparing stated preferences (games) vs. revealed behavior (transactions)</p>
          <div className="grid grid-cols-2 gap-x-6 gap-y-3">
            {Object.entries(sdDetails).map(([tid, v]) => {
              const gap = Math.abs((v.stated ?? 0) - (v.revealed ?? 0));
              const gc = gap > 20 ? '#dc2626' : gap >= 10 ? '#d97706' : '#059669';
              return (
                <div key={tid}>
                  <div className="text-[11px] font-bold text-slate-700 mb-1">{TRAITS[tid]?.name || tid}</div>
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[10px] text-blue-600 w-14">Stated</span>
                    <div className="flex-1"><Bar value={v.stated || 0} max={100} color="#2563eb" h={4} /></div>
                    <span className="text-[10px] font-mono w-7 text-right">{v.stated}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-amber-600 w-14">Revealed</span>
                    <div className="flex-1"><Bar value={v.revealed || 0} max={100} color="#d97706" h={4} /></div>
                    <span className="text-[10px] font-mono w-7 text-right">{v.revealed}</span>
                  </div>
                  <div className="text-right"><span className="text-[10px] font-bold" style={{ color: gc }}>Gap: {gap.toFixed(0)}</span></div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* 6. Allocation */}
      {allocation && (
        <Card>
          <h3 className="text-sm font-bold text-slate-800 mb-1">Recommended Asset Allocation</h3>
          <p className="text-xs text-slate-400 mb-4">Based on composite score of {composite_score != null ? Math.round(composite_score) : '—'}</p>
          <div className="flex flex-col md:flex-row gap-8 items-start">
            <AllocationDonut equity={allocation.equity} fixedIncome={allocation.fixed_income} alternatives={allocation.alternatives} cash={allocation.cash} />
            {allocation.equity_sub_allocation && (
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

      {/* 7. Matrix */}
      {matrix && (
        <Card>
          <h3 className="text-sm font-bold text-slate-800 mb-1">Liquidity x Drawdown Matrix</h3>
          <p className="text-xs text-slate-400 mb-4">Your position determines the strategy family</p>
          <div className="grid grid-cols-2 gap-5">
            <MatrixGrid cell={matrix.cell} />
            <div className="bg-teal-50 rounded-lg p-4 border border-teal-200">
              <p className="text-sm font-bold text-teal-700">{matrix.label}</p>
              <p className="text-xs text-slate-500 mt-0.5">{matrix.subtitle}</p>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">{matrix.description}</p>
            </div>
          </div>
        </Card>
      )}

      {/* 8. Investment Approaches */}
      {approaches?.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-slate-800 mb-3">Suitable Investment Approaches</h3>
          <div className="space-y-2">
            {approaches.map((a, i) => (
              <div key={i} className="border border-slate-200 rounded-lg overflow-hidden">
                <button onClick={() => setOpenApproach(openApproach === i ? null : i)} className="w-full flex items-center justify-between p-3 text-left hover:bg-slate-50 transition-colors">
                  <div>
                    <p className="text-xs font-bold text-slate-800">{a.name}</p>
                    <div className="flex gap-2 mt-1">
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">{a.risk}</span>
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-teal-50 text-teal-600">{a.allocation_range}</span>
                    </div>
                  </div>
                  <span className="text-slate-400 text-xs">{openApproach === i ? '\u25BC' : '\u25B6'}</span>
                </button>
                {openApproach === i && (
                  <div className="px-3 pb-3 border-t border-slate-100 pt-2">
                    <p className="text-[11px] text-slate-600 leading-relaxed">{a.description}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 9. Behavioral Flags */}
      {flags?.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-slate-800 mb-3">Behavioral Flags</h3>
          <div className="space-y-2">
            {flags.map((f, i) => {
              const styles = { critical: 'bg-red-50 border-red-200 text-red-700', warning: 'bg-amber-50 border-amber-200 text-amber-700', info: 'bg-blue-50 border-blue-200 text-blue-700' };
              return (
                <div key={i} className={`rounded-lg p-3 border ${styles[f.type] || styles.info}`}>
                  <p className="text-xs font-bold">{f.title}</p>
                  <p className="text-[11px] mt-0.5 opacity-80">{f.explanation || f.msg}</p>
                  {f.action && <p className="text-[10px] mt-1 font-semibold opacity-70">Action: {f.action}</p>}
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* 10. History */}
      {history.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-slate-800 mb-3">Assessment History</h3>
          <div className="space-y-2">
            {history.map((h, i) => {
              const snap = h.profile_snapshot || {};
              const comp = snap.composite ?? snap.composite_risk_score;
              return (
                <div key={h.id || i} className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
                  <div className="flex items-center gap-2">
                    <Badge color="#64748b">{h.trigger || 'manual'}</Badge>
                    <span className="text-[10px] text-slate-400">{fmt(h.created_at)}</span>
                  </div>
                  <span className="font-mono font-bold text-sm" style={{ color: comp != null ? scoreColor(comp, 'loss_aversion') : '#94a3b8' }}>
                    {comp ?? '—'}
                  </span>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* 11. Product CTA */}
      <Card>
        <div className="text-center py-4">
          <p className="text-xs text-slate-500 mb-3">Ready to explore products matched to this profile?</p>
          <button onClick={onViewProducts}
            className="bg-teal-600 text-white font-medium px-6 py-2.5 rounded-lg hover:bg-teal-700 transition-colors text-sm">
            Explore Product Universe &rarr;
          </button>
        </div>
      </Card>

    </div>
  );
}
