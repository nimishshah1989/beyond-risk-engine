export function Card({ children, className = '', noPad }) {
  return <div className={`bg-white border border-gray-200 rounded-xl shadow-sm ${noPad ? '' : 'p-5'} ${className}`}>{children}</div>;
}

export function Badge({ children, color = '#1746a2' }) {
  return <span className="inline-block px-2.5 py-0.5 rounded-full text-[10.5px] font-bold tracking-wide uppercase whitespace-nowrap"
    style={{ color, background: color + '14', border: `1px solid ${color}25` }}>{children}</span>;
}

export function Btn({ children, primary, small, onClick, className = '', disabled }) {
  return (
    <button onClick={onClick} disabled={disabled}
      className={`rounded-lg font-bold transition-all ${small ? 'px-3 py-1 text-[10.5px]' : 'px-4 py-1.5 text-xs'} 
        ${primary ? 'bg-blue-800 text-white hover:bg-blue-900' : 'bg-transparent text-gray-500 border border-gray-200 hover:bg-gray-50'}
        ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'} ${className}`}>
      {children}
    </button>
  );
}

export function Bar({ value, max, color = '#1746a2', h = 6 }) {
  return (
    <div className="w-full rounded-full overflow-hidden" style={{ height: h, background: '#f1f5f9' }}>
      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${Math.min((value / max) * 100, 100)}%`, background: color }} />
    </div>
  );
}

export function KPICard({ label, value, sub, color }) {
  return (
    <Card>
      <div className="text-[11px] text-gray-400 mb-1">{label}</div>
      <div className="text-xl font-extrabold" style={{ color: color || '#0f172a' }}>{value}</div>
      <div className="text-[11px] text-gray-500 mt-1">{sub}</div>
    </Card>
  );
}

export function RadarChart({ traits, size = 260 }) {
  const ids = Object.keys(traits);
  const n = ids.length;
  const cx = size / 2, cy = size / 2, r = size / 2 - 40;
  const angleStep = (2 * Math.PI) / n;
  const levels = [20, 40, 60, 80, 100];

  const getPoint = (i, val) => {
    const a = angleStep * i - Math.PI / 2;
    return [cx + (val / 100) * r * Math.cos(a), cy + (val / 100) * r * Math.sin(a)];
  };

  const poly = ids.map((id, i) => getPoint(i, traits[id])).map(p => p.join(',')).join(' ');

  return (
    <svg width={size} height={size} className="mx-auto">
      {levels.map(l => (
        <polygon key={l} points={ids.map((_, i) => getPoint(i, l).join(',')).join(' ')}
          fill="none" stroke="#e2e8f0" strokeWidth="1" />
      ))}
      {ids.map((_, i) => (
        <line key={i} x1={cx} y1={cy} x2={getPoint(i, 100)[0]} y2={getPoint(i, 100)[1]} stroke="#f1f5f9" strokeWidth="1" />
      ))}
      <polygon points={poly} fill="rgba(23,70,162,0.15)" stroke="#1746a2" strokeWidth="2" />
      {ids.map((id, i) => {
        const [x, y] = getPoint(i, 112);
        const val = traits[id];
        const c = val >= 70 ? '#dc2626' : val >= 40 ? '#d97706' : '#059669';
        return (
          <g key={id}>
            <circle cx={getPoint(i, traits[id])[0]} cy={getPoint(i, traits[id])[1]} r="4" fill={c} stroke="#fff" strokeWidth="2" />
            <text x={x} y={y} textAnchor="middle" dominantBaseline="middle" fontSize="9" fontWeight="700" fill="#475569">
              {id.split('_').map(w => w[0].toUpperCase()).join('')}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center p-12">
      <div className="w-8 h-8 border-3 border-blue-200 border-t-blue-700 rounded-full animate-spin" />
    </div>
  );
}
