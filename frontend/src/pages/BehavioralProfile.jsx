import { useState, useEffect } from 'react';
import { Card, KPICard, Badge, Btn, Bar, RadarChart } from '../components/UI';
import { getProfile, recalculateProfile, getProfileHistory } from '../services/api';
import { TRAITS, TRAIT_IDS } from '../data/traits';

const SRC_COLORS = { FUSED: '#0d9488', PSYCHOMETRIC_ONLY: '#2563eb', TRANSACTION_ONLY: '#d97706', NONE: '#94a3b8' };
const REGIME_COLORS = { CRISIS: '#dc2626', EUPHORIA: '#d97706', ELEVATED: '#ea580c', ATTRACTIVE: '#059669', MID: '#2563eb' };
const REALISM_COLORS = { ACHIEVABLE: '#059669', STRETCH: '#d97706', UNREALISTIC: '#dc2626', HIGH_RISK: '#dc2626' };
const FLAG_COLORS = { critical: '#dc2626', warning: '#d97706', info: '#2563eb' };

// Risk traits: high = red. Capacity/stability traits: high = green (inverted).
const INVERTED = new Set(['horizon_tolerance', 'behavioral_stability', 'ambiguity_tolerance', 'decision_confidence']);
const scoreColor = (v, trait) => {
  const inv = INVERTED.has(trait);
  if (v >= 61) return inv ? '#059669' : '#dc2626';
  if (v >= 31) return '#d97706';
  return inv ? '#dc2626' : '#059669';
};

const fmt = (d) => d ? new Date(d).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '---';

function Skeleton({ className = '' }) {
  return <div className={`bg-slate-100 animate-pulse rounded ${className}`} />;
}

export default function BehavioralProfile({ investorId, investorName }) {
  const [profile, setProfile] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [recalcing, setRecalcing] = useState(false);
  const [error, setError] = useState(null);

  const load = () => {
    if (!investorId) return;
    setLoading(true);
    setError(null);
    Promise.all([getProfile(investorId), getProfileHistory(investorId)])
      .then(([p, h]) => { setProfile(p.data); setHistory((h.data || []).slice(0, 5)); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [investorId]);

  const handleRecalc = () => {
    setRecalcing(true);
    recalculateProfile(investorId)
      .then(p => { setProfile(p.data); load(); })
      .catch(e => setError(e.message))
      .finally(() => setRecalcing(false));
  };

  if (!investorId) return <div className="text-center py-20"><p className="text-gray-400 text-sm">Select an investor to view their behavioral profile.</p></div>;

  if (loading) return (
    <div className="space-y-4">
      <Skeleton className="h-10 w-1/3" />
      <div className="grid grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)}</div>
      <div className="grid grid-cols-2 gap-4"><Skeleton className="h-72" /><Skeleton className="h-72" /></div>
    </div>
  );

  if (error) return <div className="text-center py-20"><p className="text-red-600 text-sm font-bold">Error: {error}</p><Btn primary onClick={load} className="mt-3">Retry</Btn></div>;

  const d = profile;
  if (!d) return <div className="text-center py-20"><p className="text-gray-400 text-sm">No profile data found for this investor.</p></div>;

  const tsRaw = d.trait_scores || {};
  // Flatten trait_scores for RadarChart: {trait: score_number}
  const ts = {};
  Object.entries(tsRaw).forEach(([k, v]) => { ts[k] = typeof v === 'object' && v !== null ? v.score : v; });
  const cyc = d.cycle_adjusted_risk || {};
  const mr = d.market_regime || {};
  const asp = d.aspiration_check;
  const sdDetails = d.say_do_details || {};
  const flags = d.behavioral_flags || [];

  return (
    <div>
      {/* 1. Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-extrabold text-gray-900">{investorName || `Investor ${investorId}`}</h2>
          <Badge color={SRC_COLORS[d.data_sources] || '#94a3b8'}>{d.data_sources?.replace(/_/g, ' ') || 'UNKNOWN'}</Badge>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[11px] text-gray-400">Updated {fmt(d.updated_at)}</span>
          <Btn primary small onClick={handleRecalc} disabled={recalcing}>{recalcing ? 'Recalculating...' : 'Recalculate'}</Btn>
        </div>
      </div>

      {/* 2. KPI Row */}
      <div className="grid grid-cols-4 gap-4 mb-5">
        <KPICard label="Composite Risk Score" value={d.composite_risk_score ?? '---'} sub="0 = low risk, 100 = high risk" color={scoreColor(d.composite_risk_score, 'loss_aversion')} />
        <KPICard label="Financial Capacity" value={d.financial_capacity ?? '---'} sub="Ability to absorb losses" color={scoreColor(d.financial_capacity, 'behavioral_stability')} />
        <KPICard label="Cycle-Adjusted Risk" value={cyc.adjusted_risk_score ?? '---'} sub={cyc.cycle_note || 'Market-adjusted view'} color={scoreColor(cyc.adjusted_risk_score, 'loss_aversion')} />
        <KPICard label="Say-Do Gap" value={d.say_do_gap != null ? d.say_do_gap.toFixed(1) : '---'} sub={d.say_do_gap > 15 ? 'Warning: significant gap' : 'Gap within norms'} color={d.say_do_gap > 15 ? '#dc2626' : '#059669'} />
      </div>

      {/* 3. Main Content */}
      <div className="grid grid-cols-2 gap-5 mb-5">
        {/* Left Column */}
        <div className="space-y-5">
          {/* Radar */}
          <Card>
            <h3 className="text-sm font-bold text-gray-900 mb-2">Behavioral Radar</h3>
            {Object.keys(ts).length > 0 && <RadarChart traits={ts} size={260} />}
            <div className="flex flex-wrap gap-1 mt-3 justify-center">
              {TRAIT_IDS.map(id => ts[id] != null && (
                <span key={id} className="text-[9px] font-mono px-1.5 py-0.5 rounded" style={{ background: scoreColor(ts[id], id) + '15', color: scoreColor(ts[id], id) }}>
                  {id.split('_').map(w => w[0].toUpperCase()).join('')}: {ts[id]}
                </span>
              ))}
            </div>
          </Card>

          {/* Say-Do Gap Analysis (FUSED only) */}
          {d.data_sources === 'FUSED' && Object.keys(sdDetails).length > 0 && (
            <Card>
              <h3 className="text-sm font-bold text-gray-900 mb-3">Say-Do Gap Analysis</h3>
              <div className="space-y-3">
                {Object.entries(sdDetails).map(([tid, v]) => {
                  const gap = Math.abs((v.stated ?? 0) - (v.revealed ?? 0));
                  const gc = gap > 20 ? '#dc2626' : gap >= 10 ? '#d97706' : '#059669';
                  return (
                    <div key={tid}>
                      <div className="text-[11px] font-bold text-gray-700 mb-1">{TRAITS[tid]?.name || tid}</div>
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-[10px] text-blue-600 w-14">Stated</span>
                        <div className="flex-1"><Bar value={v.stated || 0} max={100} color="#2563eb" h={5} /></div>
                        <span className="text-[10px] font-mono w-7 text-right">{v.stated}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-amber-600 w-14">Revealed</span>
                        <div className="flex-1"><Bar value={v.revealed || 0} max={100} color="#d97706" h={5} /></div>
                        <span className="text-[10px] font-mono w-7 text-right">{v.revealed}</span>
                      </div>
                      <div className="text-right"><span className="text-[10px] font-bold" style={{ color: gc }}>Gap: {gap.toFixed(0)}</span></div>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}
        </div>

        {/* Right Column */}
        <div className="space-y-5">
          {/* Market Cycle Context */}
          <Card>
            <h3 className="text-sm font-bold text-gray-900 mb-3">Market Cycle Context</h3>
            <div className="flex items-center gap-2 mb-3">
              <Badge color={REGIME_COLORS[(mr.regime || '').split('_')[0]] || '#64748b'}>{(mr.regime || 'UNKNOWN').replace(/_/g, ' ')}</Badge>
              {mr.expected_forward_return && <span className="text-[10px] text-gray-500">Forward est: {mr.expected_forward_return}</span>}
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              {[['NIFTY 50', mr.nifty_current], ['Vol 30D', mr.vol_30d != null && `${Number(mr.vol_30d).toFixed(1)}%`], ['Drawdown', mr.drawdown_from_peak != null && `${Number(mr.drawdown_from_peak).toFixed(1)}%`], ['Risk Premium', mr.risk_premium]].map(([l, v]) => v ? (
                <div key={l}><span className="text-gray-400">{l}</span><span className="ml-2 font-mono font-bold text-gray-900">{v}</span></div>
              ) : null)}
            </div>
            {cyc.cycle_note && <p className="text-[11px] text-gray-500 mt-3 italic">{cyc.cycle_note}</p>}
          </Card>

          {/* Aspiration Reality Check */}
          {asp && (
            <Card>
              <h3 className="text-sm font-bold text-gray-900 mb-3">Aspiration Reality Check</h3>
              <div className="flex items-center gap-2 mb-3">
                <Badge color={REALISM_COLORS[asp.realism] || '#64748b'}>{asp.realism}</Badge>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs mb-2">
                <div><span className="text-gray-400">Target Return</span><span className="ml-2 font-mono font-bold text-gray-900">{asp.aspiration}%</span></div>
                <div><span className="text-gray-400">Market Est.</span><span className="ml-2 font-mono font-bold text-gray-900">{asp.market_forward_estimate}</span></div>
                {asp.equity_allocation_needed != null && <div><span className="text-gray-400">Equity Needed</span><span className="ml-2 font-mono font-bold text-gray-900">{asp.equity_allocation_needed}%</span></div>}
                {asp.gap != null && <div><span className="text-gray-400">Gap</span><span className="ml-2 font-mono font-bold" style={{color: asp.gap > 4 ? '#dc2626' : asp.gap > 0 ? '#d97706' : '#059669'}}>{asp.gap > 0 ? '+' : ''}{asp.gap}pp</span></div>}
              </div>
              {asp.message && <p className="text-[11px] text-gray-600 mt-2">{asp.message}</p>}
            </Card>
          )}

          {/* Trait Scores Table */}
          <Card noPad>
            <div className="px-5 pt-5 pb-2"><h3 className="text-sm font-bold text-gray-900">Trait Scores</h3></div>
            <table className="w-full text-xs">
              <thead><tr className="border-b border-gray-200">
                <th className="text-left px-5 py-2 text-[10px] font-semibold text-gray-400 uppercase">Trait</th>
                <th className="px-2 py-2 text-[10px] font-semibold text-gray-400 uppercase w-28">Score</th>
                <th className="px-2 py-2 text-[10px] font-semibold text-gray-400 uppercase text-right">CI Range</th>
              </tr></thead>
              <tbody>
                {TRAIT_IDS.map(id => {
                  const v = ts[id]; if (v == null) return null;
                  const raw = tsRaw[id] || {};
                  return (
                    <tr key={id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="px-5 py-1.5 font-medium text-gray-800">{TRAITS[id]?.icon} {TRAITS[id]?.name}</td>
                      <td className="px-2 py-1.5">
                        <div className="flex items-center gap-2">
                          <div className="flex-1"><Bar value={v} max={100} color={scoreColor(v, id)} h={4} /></div>
                          <span className="font-mono font-bold w-6 text-right" style={{ color: scoreColor(v, id) }}>{v}</span>
                        </div>
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono text-gray-400">{raw.ci_lower != null ? `${raw.ci_lower}–${raw.ci_upper}` : '---'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        </div>
      </div>

      {/* 4. Bottom Section */}
      <div className="grid grid-cols-2 gap-5">
        {/* Behavioral Flags */}
        <Card>
          <h3 className="text-sm font-bold text-gray-900 mb-3">Behavioral Flags</h3>
          {flags.length === 0 ? (
            <div className="bg-emerald-50 p-4 rounded-lg text-center"><span className="text-emerald-700 text-xs font-bold">No flags detected</span></div>
          ) : flags.map((f, i) => (
            <div key={i} className="p-3 rounded-lg border mb-2" style={{ borderColor: (FLAG_COLORS[f.type] || '#94a3b8') + '30', background: (FLAG_COLORS[f.type] || '#94a3b8') + '08' }}>
              <div className="flex items-center gap-2 mb-1">
                <Badge color={FLAG_COLORS[f.type] || '#94a3b8'}>{f.type}</Badge>
                <span className="text-xs font-bold text-gray-900">{f.title}</span>
              </div>
              <p className="text-[11px] text-gray-600">{f.msg}</p>
              {f.action && <p className="text-[11px] font-semibold text-teal-700 mt-1">Action: {f.action}</p>}
            </div>
          ))}
        </Card>

        {/* Profile History */}
        <Card>
          <h3 className="text-sm font-bold text-gray-900 mb-3">Profile History</h3>
          {history.length === 0 ? (
            <p className="text-xs text-gray-400">No history available yet.</p>
          ) : (
            <div className="space-y-2">
              {history.map((h, i) => {
                const snap = h.profile_snapshot || {};
                return (
                  <div key={h.id || i} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                    <div>
                      <Badge color="#64748b">{h.trigger || 'manual'}</Badge>
                      <span className="text-[11px] text-gray-400 ml-2">{fmt(h.created_at)}</span>
                    </div>
                    <span className="font-mono font-bold text-sm" style={{ color: scoreColor(snap.composite ?? snap.composite_risk_score, 'loss_aversion') }}>
                      {snap.composite ?? snap.composite_risk_score ?? '---'}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
