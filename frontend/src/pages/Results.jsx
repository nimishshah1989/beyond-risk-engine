import { useState, useEffect } from 'react'
import { Card, Badge, Btn, Bar, RadarChart, LoadingSpinner } from '../components/UI'
import { getFullReport, getMarketRegime } from '../services/api'
import { TRAITS } from '../data/traits'

export default function Results({ assessmentId, traits: propTraits, onViewStrategy }) {
  const [report, setReport] = useState(null);
  const [traits, setTraits] = useState(propTraits);
  const [regime, setRegime] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedTrait, setExpandedTrait] = useState(null);

  useEffect(() => {
    if (assessmentId) {
      setLoading(true);
      Promise.all([
        getFullReport(assessmentId),
        getMarketRegime().catch(() => ({ data: null })),
      ]).then(([r, mr]) => {
        setReport(r);
        setTraits(r.assessment?.trait_scores || propTraits);
        setRegime(mr.data);
        setLoading(false);
      }).catch(() => setLoading(false));
    }
  }, [assessmentId]);

  if (!traits && !loading) {
    return (
      <div className="text-center py-20">
        <div className="text-4xl mb-3">📊</div>
        <p className="text-gray-500 text-sm">No assessment results to display.</p>
        <p className="text-gray-400 text-xs mt-1">Run an assessment first to see the behavioral risk profile.</p>
      </div>
    );
  }

  if (loading) return <LoadingSpinner />;

  const a = report?.assessment;
  const insights = report?.insights || [];
  const guide = report?.conversation_guide || a?.conversation_guide;
  const flags = a?.behavioral_flags || [];
  const stress = a?.stress_prediction;

  const traitLevel = (v) => v >= 70 ? 'High' : v >= 40 ? 'Moderate' : 'Low';
  const traitColor = (v) => v >= 70 ? '#dc2626' : v >= 40 ? '#d97706' : '#059669';

  return (
    <div>
      {/* Header KPIs */}
      <div className="grid grid-cols-5 gap-3 mb-5">
        <Card><div className="text-[11px] text-gray-400">Questions</div><div className="text-xl font-extrabold">{a?.total_questions || '—'}</div></Card>
        <Card><div className="text-[11px] text-gray-400">Drawdown Tolerance</div><div className="text-xl font-extrabold" style={{color: '#dc2626'}}>{a?.drawdown_tolerance ? `${a.drawdown_tolerance}%` : '—'}</div></Card>
        <Card><div className="text-[11px] text-gray-400">Liquidity Buffer</div><div className="text-xl font-extrabold text-amber-600">{a?.liquidity_buffer || '—'}</div></Card>
        <Card><div className="text-[11px] text-gray-400">Stress Label</div><div className="text-lg font-extrabold text-red-600">{stress?.label || '—'}</div></Card>
        <Card><div className="text-[11px] text-gray-400">Flags</div><div className="text-xl font-extrabold" style={{color: flags.length > 0 ? '#dc2626' : '#059669'}}>{flags.length} ⚠️</div></Card>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-5">
        {/* Radar Chart */}
        <Card>
          <h3 className="text-sm font-bold mb-2">Behavioral Radar</h3>
          <p className="text-[10.5px] text-gray-400 mb-3">10-trait investor DNA fingerprint</p>
          {traits && <RadarChart traits={traits} size={240} />}
          <div className="flex flex-wrap gap-1 mt-3 justify-center">
            {traits && Object.entries(traits).map(([k, v]) => (
              <span key={k} className="text-[9px] px-1.5 py-0.5 rounded" style={{ background: traitColor(v) + '15', color: traitColor(v) }}>
                {k.split('_').map(w=>w[0].toUpperCase()).join('')}: {v}
              </span>
            ))}
          </div>
        </Card>

        {/* Trait Scores Table */}
        <Card className="col-span-2">
          <h3 className="text-sm font-bold mb-3">Trait Scores & Insights</h3>
          <p className="text-[10.5px] text-gray-400 mb-4">Click any trait for detailed explanation and advisor guidance</p>
          <div className="space-y-2">
            {traits && Object.entries(traits).map(([id, val]) => {
              const t = TRAITS[id];
              const isOpen = expandedTrait === id;
              const insight = insights.find(i => i.trait === id);
              return (
                <div key={id} onClick={() => setExpandedTrait(isOpen ? null : id)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${isOpen ? 'border-blue-200 bg-blue-50/50' : 'border-gray-100 hover:bg-gray-50'}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-base">{t?.icon}</span>
                      <span className="text-xs font-bold text-gray-900">{t?.name || id}</span>
                      <Badge color={traitColor(val)}>{traitLevel(val)}</Badge>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-24"><Bar value={val} max={100} color={traitColor(val)} h={5} /></div>
                      <span className="text-sm font-extrabold w-8 text-right" style={{color: traitColor(val)}}>{val}</span>
                    </div>
                  </div>
                  {isOpen && t && (
                    <div className="mt-3 space-y-2 text-xs">
                      <div className="bg-white p-3 rounded-lg border border-gray-100">
                        <div className="font-bold text-gray-700 mb-1">What this means</div>
                        <p className="text-gray-500">{t.description}</p>
                        <p className="mt-2 font-semibold" style={{color: traitColor(val)}}>
                          {val >= 70 ? t.high : val >= 40 ? t.mid : t.low}
                        </p>
                      </div>
                      {insight && (
                        <div className="bg-amber-50 p-3 rounded-lg border border-amber-100">
                          <div className="font-bold text-amber-700 mb-1">💡 Advisor Insight</div>
                          <p className="text-amber-800">{insight.insight}</p>
                          {insight.recommendation && <p className="mt-1 text-amber-700 font-semibold">→ {insight.recommendation}</p>}
                        </div>
                      )}
                      {t.advisor_tip && (
                        <div className="bg-purple-50 p-3 rounded-lg border border-purple-100">
                          <div className="font-bold text-purple-700 mb-1">🎯 Communication Tip</div>
                          <p className="text-purple-800">{t.advisor_tip}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* Behavioral Flags + Stress */}
      <div className="grid grid-cols-2 gap-4 mb-5">
        <Card>
          <h3 className="text-sm font-bold mb-3">⚠️ Behavioral Flags</h3>
          {flags.length === 0 ? (
            <div className="bg-green-50 p-4 rounded-lg text-center"><span className="text-green-700 text-xs font-bold">✅ No behavioral flags detected — profile is consistent</span></div>
          ) : flags.map((f, i) => (
            <div key={i} className="p-3 bg-red-50 rounded-xl border border-red-100 mb-2">
              <div className="flex items-center gap-2 mb-1">
                <Badge color="#dc2626">{f.type?.replace(/_/g, ' ')}</Badge>
              </div>
              <div className="text-xs font-bold text-red-900">{f.title}</div>
              <div className="text-[11px] text-red-700 mt-0.5">{f.msg}</div>
              {f.action && <div className="text-[11px] text-red-800 mt-1 font-semibold">→ {f.action}</div>}
            </div>
          ))}
        </Card>

        <Card>
          <h3 className="text-sm font-bold mb-3">🌊 Stress Test Prediction</h3>
          <p className="text-[10.5px] text-gray-400 mb-3">Predicted behavior during a 20%+ market correction</p>
          {stress ? (
            <>
              <div className={`p-4 rounded-xl mb-3 ${stress.severity === 'high' ? 'bg-red-50 border border-red-200' : stress.severity === 'medium' ? 'bg-amber-50 border border-amber-200' : 'bg-green-50 border border-green-200'}`}>
                <div className="text-lg font-extrabold" style={{color: stress.severity === 'high' ? '#dc2626' : stress.severity === 'medium' ? '#d97706' : '#059669'}}>{stress.label}</div>
                <p className="text-xs text-gray-600 mt-1">{stress.text}</p>
              </div>
              {stress.scenarios && (
                <div className="space-y-2">
                  {Object.entries(stress.scenarios).map(([k, v]) => (
                    <div key={k} className="flex items-center justify-between">
                      <span className="text-xs text-gray-600 capitalize">{k.replace(/_/g, ' ')}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-20"><Bar value={v} max={100} color={k === 'panic_sell' ? '#dc2626' : k === 'buy_more' ? '#059669' : '#d97706'} h={5} /></div>
                        <span className="text-xs font-bold w-8 text-right">{v}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : <p className="text-xs text-gray-400">No stress prediction available</p>}
        </Card>
      </div>

      {/* Market Cycle Context */}
      {regime && (
        <Card className="mb-5">
          <h3 className="text-sm font-bold mb-3">📈 Market Cycle Context</h3>
          <div className="flex items-center gap-3 mb-3">
            <Badge color={regime.regime?.includes('CRISIS') ? '#dc2626' : regime.regime?.includes('EUPHORIA') ? '#d97706' : regime.regime?.includes('ELEVATED') ? '#ea580c' : regime.regime?.includes('ATTRACTIVE') ? '#059669' : '#2563eb'}>
              {(regime.regime || 'UNKNOWN').replace(/_/g, ' ')}
            </Badge>
            <span className="text-xs text-gray-500">Forward estimate: <span className="font-mono font-bold">{regime.expected_forward_return || '---'}</span></span>
            <span className="text-xs text-gray-500">Risk premium: <span className="font-bold">{regime.risk_premium || '---'}</span></span>
          </div>
          <div className="grid grid-cols-4 gap-4 text-xs">
            <div><span className="text-gray-400">NIFTY 50</span><span className="ml-2 font-mono font-bold">{regime.nifty_current || '---'}</span></div>
            <div><span className="text-gray-400">Vol 30D</span><span className="ml-2 font-mono font-bold">{regime.vol_30d ? `${regime.vol_30d}%` : '---'}</span></div>
            <div><span className="text-gray-400">Drawdown</span><span className="ml-2 font-mono font-bold">{regime.drawdown_from_peak ? `${regime.drawdown_from_peak}%` : '---'}</span></div>
            <div><span className="text-gray-400">Valuation</span><span className="ml-2 font-mono font-bold">{regime.valuation_ratio || '---'}x</span></div>
          </div>
          <p className="text-[11px] text-gray-500 mt-3 italic">
            {regime.risk_per_return === 'POOR' ? 'Current risk-reward is unfavorable — consider defensive positioning.' :
             regime.risk_per_return === 'EXCELLENT' ? 'Risk premiums expanded — favorable environment for risk-tolerant investors.' :
             'Market conditions are within normal range.'}
          </p>
        </Card>
      )}

      {/* Conversation Guide */}
      {guide && (
        <Card className="mb-5">
          <h3 className="text-sm font-bold mb-3">💬 Advisor Conversation Guide</h3>
          <p className="text-[10.5px] text-gray-400 mb-4">AI-generated talking points tailored to this investor's behavioral profile</p>
          {guide.style && (
            <div className="bg-blue-50 p-4 rounded-xl mb-4 border border-blue-100">
              <div className="grid grid-cols-4 gap-4">
                <div><div className="text-[10px] text-blue-600 font-bold uppercase">Tone</div><div className="text-xs font-bold text-blue-900">{guide.style.tone}</div></div>
                <div><div className="text-[10px] text-blue-600 font-bold uppercase">Approach</div><div className="text-xs text-blue-800">{guide.style.approach}</div></div>
                <div><div className="text-[10px] text-blue-600 font-bold uppercase">Avoid</div><div className="text-xs text-red-700">{guide.style.avoid}</div></div>
                <div><div className="text-[10px] text-blue-600 font-bold uppercase">Opening Line</div><div className="text-xs text-blue-800 italic">{guide.style.opening}</div></div>
              </div>
            </div>
          )}
          {guide.talking_points && (
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(guide.talking_points).map(([category, points]) => (
                <div key={category} className="bg-gray-50 p-3 rounded-xl">
                  <div className="text-[10px] font-bold text-gray-500 uppercase mb-2">{category}</div>
                  {(Array.isArray(points) ? points : [points]).map((pt, j) => (
                    <div key={j} className="text-xs text-gray-700 flex gap-2 mb-1.5">
                      <span className="text-amber-500 font-bold">→</span><span>{pt}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Match Products CTA */}
      <Card className="bg-gradient-to-r from-blue-800 to-blue-600 text-white border-0">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-extrabold">Ready for Recommendations?</h3>
            <p className="text-blue-200 text-xs mt-1">See AI-recommended asset allocation and top product picks based on this behavioral profile</p>
          </div>
          <Btn onClick={onViewStrategy} className="!bg-white !text-blue-800 hover:!bg-blue-50">View Recommended Strategy →</Btn>
        </div>
      </Card>
    </div>
  );
}
