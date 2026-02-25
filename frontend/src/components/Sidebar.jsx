import { useState } from 'react'

export default function Sidebar({ pages, current, onNav }) {
  const [open, setOpen] = useState(true);
  return (
    <div className={`${open ? 'w-56' : 'w-14'} min-h-screen flex flex-col transition-all duration-200`}
         style={{ background: '#0c1425' }}>
      <div className="flex items-center gap-2.5 px-3.5 py-4 border-b border-gray-700/40">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-700 to-blue-500 flex items-center justify-center text-white font-black text-sm shrink-0">B</div>
        {open && <div><div className="text-white font-extrabold text-sm tracking-tight">BEYOND</div><div className="text-gray-500 text-[8px] tracking-[2px] uppercase">Risk Engine</div></div>}
      </div>
      <nav className="flex-1 p-1.5 space-y-0.5">
        {pages.map(p => (
          <button key={p.id} onClick={() => onNav(p.id)}
            className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-[12.5px] transition-all ${
              current === p.id ? 'bg-gradient-to-r from-blue-700 to-blue-600 text-white font-bold' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'}`}>
            <span className="text-sm w-5 text-center shrink-0">{p.icon}</span>
            {open && <span className="whitespace-nowrap">{p.label}</span>}
          </button>
        ))}
      </nav>
      <button onClick={() => setOpen(!open)} className="p-2.5 border-t border-gray-700/40 text-gray-500 text-center hover:text-gray-300">
        {open ? '◂' : '▸'}
      </button>
    </div>
  );
}
