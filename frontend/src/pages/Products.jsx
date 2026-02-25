import { useState, useEffect } from 'react'
import { Card, Badge, Btn, Bar, LoadingSpinner } from '../components/UI'
import { getProducts, getCategories } from '../services/api'

export default function Products() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    Promise.all([getProducts(), getCategories()]).then(([p, c]) => {
      setProducts(p); setCategories(c); setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const filtered = products.filter(p => {
    const matchesCategory = filter === 'all' || p.category === filter;
    const matchesSearch = !search || p.name?.toLowerCase().includes(search.toLowerCase()) || p.code?.toLowerCase().includes(search.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const riskColor = (label) => {
    if (!label) return '#94a3b8';
    const l = label.toLowerCase();
    if (l.includes('high') || l.includes('very high')) return '#dc2626';
    if (l.includes('moderate') || l.includes('medium')) return '#d97706';
    return '#059669';
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      {/* Header */}
      <Card className="mb-5">
        <div className="flex items-center justify-between mb-1">
          <div>
            <h3 className="text-sm font-bold text-gray-900">Product & Instrument Universe</h3>
            <p className="text-[10.5px] text-gray-400">{products.length} instruments across {categories.length} categories · All pre-scored with 10-trait behavioral demand vectors</p>
          </div>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search products..."
            className="px-3 py-1.5 rounded-lg border border-gray-200 text-xs w-52 focus:outline-none focus:ring-2 focus:ring-blue-200" />
        </div>
      </Card>

      {/* Category filter */}
      <div className="flex gap-2 mb-5 flex-wrap">
        <button onClick={() => setFilter('all')}
          className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${filter === 'all' ? 'bg-blue-800 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
          All ({products.length})
        </button>
        {categories.map(c => {
          const count = products.filter(p => p.category === c).length;
          return (
            <button key={c} onClick={() => setFilter(c)}
              className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${filter === c ? 'bg-blue-800 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
              {c} ({count})
            </button>
          );
        })}
      </div>

      {/* Products grid */}
      {filtered.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-400 text-sm">No products found{filter !== 'all' ? ` in "${filter}"` : ''}.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((p, i) => (
            <div key={p.id || i} onClick={() => setExpanded(expanded === p.id ? null : p.id)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${expanded === p.id ? 'border-blue-200 bg-blue-50/30' : 'bg-white border-gray-100 hover:bg-gray-50'}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div>
                    <div className="text-sm font-bold text-gray-900">{p.name}</div>
                    <div className="text-[11px] text-gray-400">{p.code} · {p.category}{p.subcategory ? ` · ${p.subcategory}` : ''}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {p.risk_label && <Badge color={riskColor(p.risk_label)}>{p.risk_label}</Badge>}
                  <Badge color={p.vector_source === 'ai_analyzed' ? '#d97706' : '#1746a2'}>{p.vector_source === 'ai_analyzed' ? '🤖 AI' : 'Scored'}</Badge>
                </div>
              </div>

              {p.description && <p className="text-[11px] text-gray-500 mt-2">{p.description}</p>}

              <div className="flex flex-wrap gap-x-5 gap-y-1 mt-2 text-[11px] text-gray-500">
                {p.min_investment && <span>Min Investment: <strong>₹{p.min_investment >= 10000000 ? (p.min_investment/10000000).toFixed(0) + 'Cr' : p.min_investment >= 100000 ? (p.min_investment/100000).toFixed(0) + 'L' : p.min_investment.toLocaleString()}</strong></span>}
                {p.lock_in_years > 0 && <span>Lock-in: <strong>{p.lock_in_years} years</strong></span>}
                {p.expected_return_range && <span>Expected Returns: <strong>{p.expected_return_range}</strong></span>}
                {p.liquidity && <span>Liquidity: <strong>{p.liquidity}</strong></span>}
                {p.taxation && <span>Taxation: <strong>{p.taxation}</strong></span>}
              </div>

              {expanded === p.id && p.risk_vector && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="text-[10px] font-bold text-gray-400 uppercase mb-3">Behavioral Demand Vector</div>
                  <p className="text-[10px] text-gray-400 mb-3">How much of each behavioral trait an investor needs to comfortably hold this product (0-100)</p>
                  <div className="grid grid-cols-2 gap-x-6 gap-y-2">
                    {Object.entries(p.risk_vector).map(([trait, demand]) => {
                      const c = demand >= 70 ? '#dc2626' : demand >= 40 ? '#d97706' : '#059669';
                      return (
                        <div key={trait} className="flex items-center gap-2">
                          <span className="text-[10px] text-gray-500 w-32 truncate capitalize">{trait.replace(/_/g, ' ')}</span>
                          <div className="flex-1"><Bar value={demand} max={100} color={c} h={5} /></div>
                          <span className="text-[10px] font-bold w-6 text-right" style={{ color: c }}>{demand}</span>
                        </div>
                      );
                    })}
                  </div>
                  <div className="mt-3 p-2.5 bg-blue-50 rounded-lg text-[10px] text-blue-700">
                    <strong>Reading this vector:</strong> A score of 70+ means the product demands high tolerance in that trait.
                    For example, high "loss aversion demand" means an investor needs to be comfortable with potential losses to hold this product.
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
