import { useState, useEffect } from 'react'
import { Card, KPICard, Badge, Btn, Bar } from '../components/UI'
import { getInvestors, getQuestionStats, getProducts } from '../services/api'

export default function Dashboard({ onNav, onViewResults }) {
  const [investors, setInvestors] = useState([]);
  const [stats, setStats] = useState(null);
  const [productCount, setProductCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getInvestors().catch(() => []),
      getQuestionStats().catch(() => null),
      getProducts().catch(() => [])
    ]).then(([inv, st, prod]) => {
      setInvestors(inv);
      setStats(st);
      setProductCount(prod.length);
      setLoading(false);
    });
  }, []);

  return (
    <div>
      <div className="grid grid-cols-5 gap-3 mb-5">
        <KPICard label="Investors" value={investors.length || '—'} sub="Total registered" color="#1746a2" />
        <KPICard label="Questions" value={stats?.total || '—'} sub={`${stats?.anchors || 0}A · ${stats?.diagnostics || 0}D · ${stats?.calibrations || 0}C`} color="#7c3aed" />
        <KPICard label="Products" value={productCount || '—'} sub="Instruments loaded" color="#0891b2" />
        <KPICard label="Assessments" value="—" sub="Run first assessment →" color="#059669" />
        <KPICard label="AI Analyzed" value="—" sub="Upload factsheets →" color="#d97706" />
      </div>

      <div className="grid grid-cols-3 gap-4 mb-5">
        <Card className="col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-gray-900">Registered Investors</h3>
              <p className="text-[11px] text-gray-400">Click to view assessment results</p>
            </div>
            <Btn primary small onClick={() => onNav('assess')}>+ New Assessment</Btn>
          </div>
          {loading ? <p className="text-xs text-gray-400 p-4">Loading...</p> :
           investors.length === 0 ? (
            <div className="text-center py-10">
              <div className="text-3xl mb-2">📋</div>
              <p className="text-sm text-gray-500 mb-3">No investors yet. Start your first assessment.</p>
              <Btn primary onClick={() => onNav('assess')}>Run Assessment →</Btn>
            </div>
           ) : (
            <table className="w-full">
              <thead>
                <tr>{['Name', 'Code', 'Age', 'AUM', 'Segment', ''].map(h => (
                  <th key={h} className="text-left text-[10px] text-gray-400 font-bold uppercase tracking-wider px-3 py-2 border-b-2 border-gray-100">{h}</th>
                ))}</tr>
              </thead>
              <tbody>
                {investors.map(inv => (
                  <tr key={inv.id} className="hover:bg-gray-50 cursor-pointer transition-colors">
                    <td className="px-3 py-2.5 text-xs font-bold">{inv.name}</td>
                    <td className="px-3 py-2.5 text-xs text-gray-500">{inv.code}</td>
                    <td className="px-3 py-2.5 text-xs">{inv.age || '—'}</td>
                    <td className="px-3 py-2.5 text-xs font-bold">{inv.aum ? `₹${inv.aum}Cr` : '—'}</td>
                    <td className="px-3 py-2.5"><Badge>{inv.segment || 'Retail'}</Badge></td>
                    <td className="px-3 py-2.5"><Btn small primary onClick={() => onNav('assess')}>Assess</Btn></td>
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
              <button onClick={() => onNav('assess')} className="w-full text-left p-3 rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors">
                <div className="text-xs font-bold text-blue-800">📋 Run New Assessment</div>
                <div className="text-[10.5px] text-blue-600">Adaptive 12-25 question flow</div>
              </button>
              <button onClick={() => onNav('upload')} className="w-full text-left p-3 rounded-lg bg-amber-50 hover:bg-amber-100 transition-colors">
                <div className="text-xs font-bold text-amber-800">🤖 AI Factsheet Analyzer</div>
                <div className="text-[10.5px] text-amber-600">Upload PDF → auto-compute risk vector</div>
              </button>
              <button onClick={() => onNav('products')} className="w-full text-left p-3 rounded-lg bg-cyan-50 hover:bg-cyan-100 transition-colors">
                <div className="text-xs font-bold text-cyan-800">🏦 Product Universe</div>
                <div className="text-[10.5px] text-cyan-600">{productCount} instruments loaded</div>
              </button>
              <button onClick={() => onNav('questions')} className="w-full text-left p-3 rounded-lg bg-purple-50 hover:bg-purple-100 transition-colors">
                <div className="text-xs font-bold text-purple-800">🧠 Question Bank</div>
                <div className="text-[10.5px] text-purple-600">Manage adaptive question pool</div>
              </button>
            </div>
          </Card>

          <Card>
            <h3 className="text-sm font-bold mb-3">10-Trait Behavioral Model</h3>
            <div className="space-y-1.5">
              {['Loss Aversion', 'Horizon Tolerance', 'Liquidity Sensitivity', 'Behavioral Stability', 'Ambiguity Tolerance',
                'Regret Sensitivity', 'Leverage Comfort', 'Goal Rigidity', 'Emotional Volatility', 'Decision Confidence'
              ].map((t, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-700" />
                  <span className="text-[11px] text-gray-600">{t}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
