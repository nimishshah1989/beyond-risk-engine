import { useState } from 'react'

const ICONS = {
  grid: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
    </svg>
  ),
  compass: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
    </svg>
  ),
  chart: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  building: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  ),
  book: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
    </svg>
  ),
};

export default function Sidebar({ pages, current, onNav }) {
  const [open, setOpen] = useState(true);
  return (
    <div className={`${open ? 'w-52' : 'w-14'} min-h-screen flex flex-col bg-white border-r border-slate-200 transition-all duration-200`}>
      <div className="flex items-center gap-2.5 px-3.5 py-4 border-b border-slate-100">
        <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-black text-sm shrink-0">B</div>
        {open && (
          <div>
            <div className="text-slate-900 font-extrabold text-sm tracking-tight">BEYOND</div>
            <div className="text-slate-400 text-[8px] tracking-[2px] uppercase">Risk Engine</div>
          </div>
        )}
      </div>
      <nav className="flex-1 p-2 space-y-0.5">
        {pages.map(p => (
          <button key={p.id} onClick={() => onNav(p.id)}
            className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[12.5px] transition-all ${
              current === p.id
                ? 'bg-teal-50 text-teal-700 font-bold border border-teal-200'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
            }`}>
            <span className="w-5 flex items-center justify-center shrink-0">
              {ICONS[p.icon] || <span className="text-sm">{p.icon}</span>}
            </span>
            {open && <span className="whitespace-nowrap">{p.label}</span>}
          </button>
        ))}
      </nav>
      <button onClick={() => setOpen(!open)} className="p-2.5 border-t border-slate-100 text-slate-400 text-center hover:text-slate-600 text-xs">
        {open ? '\u25C2' : '\u25B8'}
      </button>
    </div>
  );
}
