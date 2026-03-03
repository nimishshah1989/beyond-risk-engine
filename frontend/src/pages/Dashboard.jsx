import { useState, useEffect } from 'react'
import { Card, KPICard, Badge, Btn, Bar } from '../components/UI'
import { getInvestors, getFullReport } from '../services/api'

export default function Dashboard({ onNav, onOpenContext, onOpenGames, onOpenProfile, onViewResults }) {
  const [investors, setInvestors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getInvestors().then(inv => { setInvestors(inv); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const assessed = investors.filter(i => i.latest_assessment_id);
  const pending = investors.filter(i => !i.latest_assessment_id);

  const handleViewResults = async (inv) => {
    if (inv.latest_assessment_id) {
      try {
        const report = await getFullReport(inv.latest_assessment_id);
        onViewResults(inv.latest_assessment_id, report.assessment?.trait_scores, inv.name, report);
      } catch {
        onViewResults(inv.latest_assessment_id, null, inv.name);
      }
    } else {
      onNav('assess');
    }
  };

  return (
    <div>
      <div className="grid grid-cols-4 gap-3 mb-5">
        <KPICard label="Total Investors" value={investors.length || '—'} sub="Registered on platform" color="#1746a2" />
        <KPICard label="Assessments Completed" value={assessed.length || '—'} sub={`${pending.length} pending`} color="#059669" />
        <KPICard label="Avg Traits Profiled" value="10" sub="Per assessment" color="#7c3aed" />
        <KPICard label="Behavioral Flags" value="—" sub="Across all investors" color="#dc2626" />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card className="col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-gray-900">Investor Registry</h3>
              <p className="text-[11px] text-gray-400">Click any investor to view their behavioral profile</p>
            </div>
            <Btn primary small onClick={() => onNav('assess')}>+ New Assessment</Btn>
          </div>
          {loading ? <p className="text-xs text-gray-400 p-4">Loading...</p> :
           investors.length === 0 ? (
            <div className="text-center py-10">
              <div className="text-3xl mb-2">📋</div>
              <p className="text-sm text-gray-500 mb-3">No investors yet. Start your first behavioral risk assessment.</p>
              <Btn primary onClick={() => onNav('assess')}>Run Assessment →</Btn>
            </div>
           ) : (
            <table className="w-full">
              <thead>
                <tr>{['Name', 'Code', 'AUM', 'Segment', 'Status', ''].map(h => (
                  <th key={h} className="text-left text-[10px] text-gray-400 font-bold uppercase tracking-wider px-3 py-2 border-b-2 border-gray-100">{h}</th>
                ))}</tr>
              </thead>
              <tbody>
                {investors.map(inv => (
                  <tr key={inv.id} className="hover:bg-gray-50 cursor-pointer transition-colors" onClick={() => handleViewResults(inv)}>
                    <td className="px-3 py-2.5 text-xs font-bold">{inv.name}</td>
                    <td className="px-3 py-2.5 text-xs text-gray-500">{inv.code}</td>
                    <td className="px-3 py-2.5 text-xs font-bold">{inv.aum ? `₹${inv.aum}Cr` : '—'}</td>
                    <td className="px-3 py-2.5"><Badge>{inv.segment || 'Retail'}</Badge></td>
                    <td className="px-3 py-2.5">
                      {inv.latest_assessment_id
                        ? <Badge color="#059669">Assessed</Badge>
                        : <Badge color="#d97706">Pending</Badge>}
                    </td>
                    <td className="px-3 py-2.5 flex gap-1.5">
                      <Btn small onClick={(e) => { e.stopPropagation(); onOpenContext(inv.id, inv.name); }}>
                        Context
                      </Btn>
                      <Btn small onClick={(e) => { e.stopPropagation(); onOpenGames(inv.id, inv.name); }}>
                        Games
                      </Btn>
                      <Btn small onClick={(e) => { e.stopPropagation(); onOpenProfile(inv.id, inv.name); }}>
                        Profile
                      </Btn>
                      <Btn small primary onClick={(e) => { e.stopPropagation(); handleViewResults(inv); }}>
                        {inv.latest_assessment_id ? 'Results' : 'Assess'}
                      </Btn>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
           )}
        </Card>

        <div className="space-y-4">
          <Card>
            <h3 className="text-sm font-bold mb-3">Quick Actions</h3>
            <div className="space-y-2">
              <button onClick={() => onNav('games')} className="w-full text-left p-3 rounded-lg bg-teal-50 hover:bg-teal-100 transition-colors">
                <div className="text-xs font-bold text-teal-800">🎮 Play Behavioral Games</div>
                <div className="text-[10.5px] text-teal-600">4 games, 19 trials, ~2.5 minutes</div>
              </button>
              <button onClick={() => onNav('assess')} className="w-full text-left p-3 rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors">
                <div className="text-xs font-bold text-blue-800">📋 Run Question Assessment</div>
                <div className="text-[10.5px] text-blue-600">Adaptive 15-25 question flow</div>
              </button>
              <button onClick={() => onNav('strategy')} className="w-full text-left p-3 rounded-lg bg-green-50 hover:bg-green-100 transition-colors">
                <div className="text-xs font-bold text-green-800">🎯 Recommended Strategy</div>
                <div className="text-[10.5px] text-green-600">AI-powered allocation & product matching</div>
              </button>
              <button onClick={() => onNav('products')} className="w-full text-left p-3 rounded-lg bg-cyan-50 hover:bg-cyan-100 transition-colors">
                <div className="text-xs font-bold text-cyan-800">🏦 Product Universe</div>
                <div className="text-[10.5px] text-cyan-600">Browse all scored instruments</div>
              </button>
              <button onClick={() => onNav('methodology')} className="w-full text-left p-3 rounded-lg bg-purple-50 hover:bg-purple-100 transition-colors">
                <div className="text-xs font-bold text-purple-800">📖 Methodology</div>
                <div className="text-[10.5px] text-purple-600">How the model works — IRT, scoring, logic</div>
              </button>
            </div>
          </Card>

          <Card>
            <h3 className="text-sm font-bold mb-2">10-Trait Behavioral Model</h3>
            <p className="text-[10px] text-gray-400 mb-3">Each investor is profiled across 10 behavioral dimensions</p>
            <div className="space-y-1.5">
              {[
                { t: 'Loss Aversion', d: 'Pain of losses vs joy of gains' },
                { t: 'Horizon Tolerance', d: 'Patience for long-term outcomes' },
                { t: 'Liquidity Sensitivity', d: 'Need for accessible money' },
                { t: 'Behavioral Stability', d: 'Consistency under pressure' },
                { t: 'Ambiguity Tolerance', d: 'Comfort with uncertainty' },
                { t: 'Regret Sensitivity', d: 'Tendency to second-guess' },
                { t: 'Leverage Comfort', d: 'Willingness to use borrowed capital' },
                { t: 'Goal Rigidity', d: 'Fixedness of financial goals' },
                { t: 'Emotional Volatility', d: 'Mood swings from market changes' },
                { t: 'Decision Confidence', d: 'Trust in own judgment' },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-700 mt-1.5 shrink-0" />
                  <div>
                    <span className="text-[11px] font-semibold text-gray-700">{item.t}</span>
                    <span className="text-[10px] text-gray-400 ml-1.5">— {item.d}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
