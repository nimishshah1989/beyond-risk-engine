import { useState, useEffect } from 'react'
import { Card, Badge, Btn, Bar, LoadingSpinner } from '../components/UI'
import { getProducts, getCategories, matchProducts } from '../services/api'

export default function Products({ investorTraits }) {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filter, setFilter] = useState('all');
  const [matches, setMatches] = useState(null);
  const [loading, setLoading] = useState(true);
  const [matchLoading, setMatchLoading] = useState(false);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    Promise.all([getProducts(), getCategories()]).then(([p, c]) => {
      setProducts(p); setCategories(c); setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (investorTraits) {
      setMatchLoading(true);
      matchProducts(investorTraits).then(m => { setMatches(m); setMatchLoading(false); }).catch(() => setMatchLoading(false));
    }
  }, [investorTraits]);

  const filtered = filter === 'all' ? products : products.filter(p => p.category === filter);
  const recColor = (label) => label === 'RECOMMENDED' ? '#059669' : label === 'CONDITIONAL' ? '#d97706' : '#dc2626';

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      {/* Match banner */}
      {investorTraits && matches && !matchLoading && (
        <Card className="mb-5 bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
          <div className="flex items-center justify-between mb-3">
            <div><h3 className="text-sm font-bold text-green-900">🎯 Product Matching Active</h3>
              <p className="text-[10.5px] text-green-700">Products ranked by behavioral fit with investor profile</p></div>
            <Badge color="#059669">{matches.filter(m => m.recommendation === 'RECOMMENDED').length} Recommended</Badge>
          </div>
          <div className="flex gap-3 text-xs">
            <span className="text-green-700 font-bold">✅ {matches.filter(m => m.recommendation === 'RECOMMENDED').length} Recommended</span>
            <span className="text-amber-700 font-bold">⚡ {matches.filter(m => m.recommendation === 'CONDITIONAL').length} Conditional</span>
            <span className="text-red-700 font-bold">⚠ {matches.filter(m => m.recommendation === 'CAUTION').length} Caution</span>
          </div>
        </Card>
      )}

      {matchLoading && <div className="bg-blue-50 p-4 rounded-xl mb-5 text-xs text-blue-700 font-bold text-center">⏳ Computing behavioral fit scores...</div>}

      {/* Category filter */}
      <div className="flex gap-2 mb-5 flex-wrap">
        <button onClick={() => setFilter('all')}
          className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${filter === 'all' ? 'bg-blue-800 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
          All ({products.length})
        </button>
        {categories.map(c => (
          <button key={c} onClick={() => setFilter(c)}
            className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${filter === c ? 'bg-blue-800 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
            {c} ({products.filter(p => p.category === c).length})
          </button>
        ))}
      </div>

      {/* Products list */}
      {matches && investorTraits ? (
        /* Matched view */
        <div className="space-y-3">
          {matches.filter(m => filter === 'all' || m.product_category === filter).map((m, i) => (
            <div key={i} onClick={() => setExpanded(expanded === i ? null : i)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                m.recommendation === 'RECOMMENDED' ? 'bg-green-50/50 border-green-200 hover:bg-green-50' :
                m.recommendation === 'CONDITIONAL' ? 'bg-amber-50/50 border-amber-200 hover:bg-amber-50' :
                'bg-red-50/30 border-red-200 hover:bg-red-50'}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-2xl font-black w-10 text-center" style={{color: recColor(m.recommendation)}}>
                    {m.fit_score}
                  </div>
                  <div>
                    <div className="text-sm font-bold text-gray-900">{m.product_name}</div>
                    <div className="text-[11px] text-gray-500">{m.product_category} · {m.product_code}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge color={recColor(m.recommendation)}>{m.recommendation}</Badge>
                  <div className="w-24"><Bar value={m.fit_score} max={100} color={recColor(m.recommendation)} h={6} /></div>
                </div>
              </div>
              {expanded === i && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="grid grid-cols-4 gap-3 mb-3">
                    <div className="bg-white p-2 rounded-lg text-center"><div className="text-[10px] text-gray-400">Emotional Fit</div><div className="text-sm font-bold">{m.component_scores?.emotional_fit || '—'}%</div></div>
                    <div className="bg-white p-2 rounded-lg text-center"><div className="text-[10px] text-gray-400">Liquidity Fit</div><div className="text-sm font-bold">{m.component_scores?.liquidity_fit || '—'}%</div></div>
                    <div className="bg-white p-2 rounded-lg text-center"><div className="text-[10px] text-gray-400">Complexity Match</div><div className="text-sm font-bold">{m.component_scores?.complexity_match || '—'}%</div></div>
                    <div className="bg-white p-2 rounded-lg text-center"><div className="text-[10px] text-gray-400">Horizon Fit</div><div className="text-sm font-bold">{m.component_scores?.horizon_fit || '—'}%</div></div>
                  </div>
                  {m.trait_breakdown && (
                    <div className="space-y-1.5">
                      <div className="text-[10px] font-bold text-gray-400 uppercase">Trait-by-Trait Breakdown</div>
                      {Object.entries(m.trait_breakdown).map(([trait, info]) => (
                        <div key={trait} className="flex items-center gap-2 text-xs">
                          <span className="w-32 text-gray-500 truncate">{trait.replace(/_/g, ' ')}</span>
                          <span className="w-8 text-right font-bold">{info.investor}</span>
                          <div className="flex-1 flex items-center gap-1">
                            <div className="flex-1 h-1.5 bg-gray-100 rounded relative">
                              <div className="absolute h-full rounded bg-blue-600" style={{width: `${info.investor}%`}} />
                            </div>
                            <div className="flex-1 h-1.5 bg-gray-100 rounded relative">
                              <div className="absolute h-full rounded bg-orange-500" style={{width: `${info.product_demand}%`}} />
                            </div>
                          </div>
                          <span className="w-8 font-bold text-orange-600">{info.product_demand}</span>
                          <span className={`w-14 text-right font-bold ${info.gap_direction === 'under-prepared' ? 'text-red-600' : 'text-green-600'}`}>
                            {info.gap > 0 ? '+' : ''}{info.gap}
                          </span>
                        </div>
                      ))}
                      <div className="flex gap-3 mt-1 text-[9px] text-gray-400">
                        <span>■ Blue = Investor Score</span><span>■ Orange = Product Demand</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        /* Plain product list */
        <div className="grid grid-cols-2 gap-3">
          {filtered.map(p => (
            <Card key={p.id}>
              <div className="flex items-start justify-between mb-2">
                <div><div className="text-sm font-bold">{p.name}</div><div className="text-[11px] text-gray-400">{p.code} · {p.category}</div></div>
                <Badge color={p.vector_source === 'ai_analyzed' ? '#d97706' : '#1746a2'}>{p.vector_source === 'ai_analyzed' ? '🤖 AI' : 'Manual'}</Badge>
              </div>
              {p.description && <p className="text-[11px] text-gray-500 mb-2">{p.description}</p>}
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-gray-500">
                {p.risk_label && <span>Risk: <strong>{p.risk_label}</strong></span>}
                {p.min_investment && <span>Min: <strong>₹{p.min_investment >= 10000000 ? (p.min_investment/10000000).toFixed(0) + 'Cr' : (p.min_investment/100000).toFixed(0) + 'L'}</strong></span>}
                {p.lock_in_years > 0 && <span>Lock-in: <strong>{p.lock_in_years}Y</strong></span>}
                {p.expected_return_range && <span>Returns: <strong>{p.expected_return_range}</strong></span>}
                {p.liquidity && <span>Liquidity: <strong>{p.liquidity}</strong></span>}
              </div>
            </Card>
          ))}
        </div>
      )}

      {!investorTraits && (
        <div className="mt-6 bg-blue-50 p-5 rounded-xl text-center">
          <p className="text-sm text-blue-800 font-bold">💡 Run an assessment first to see behavioral fit matching</p>
          <p className="text-xs text-blue-600 mt-1">Products will be ranked by how well they match the investor's behavioral profile</p>
        </div>
      )}
    </div>
  );
}
