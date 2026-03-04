import { useState, useEffect } from 'react'
import { getInvestors, createInvestor } from '../services/api'

const fmtScore = (v) => v != null ? Math.round(v) : '—';

function StatusBadge({ label, active }) {
  return (
    <span className={`inline-block w-5 h-5 rounded text-[9px] font-bold flex items-center justify-center ${
      active ? 'bg-teal-100 text-teal-700 border border-teal-200' : 'bg-slate-100 text-slate-400'
    }`}>{label}</span>
  );
}

function InvestorCard({ inv, onStartJourney, onViewReport }) {
  const isComplete = inv.has_financial_context && inv.has_game_session;
  const score = inv.composite_score;
  const scoreColor = score == null ? '#94a3b8' : score <= 35 ? '#059669' : score <= 65 ? '#d97706' : '#dc2626';

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 hover:border-teal-300 transition-colors group">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-800">{inv.name}</h3>
          <p className="text-[10px] text-slate-400 font-mono">{inv.code}</p>
        </div>
        {score != null && (
          <div className="text-right">
            <span className="text-lg font-bold font-mono" style={{ color: scoreColor }}>{Math.round(score)}</span>
            <p className="text-[9px] text-slate-400">/100</p>
          </div>
        )}
      </div>
      <div className="flex items-center gap-3 mb-3">
        {inv.segment && (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 border border-slate-200">
            {inv.segment}
          </span>
        )}
        {inv.profile_source && (
          <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-teal-50 text-teal-600 border border-teal-200">
            {inv.profile_source.replace(/_/g, ' ')}
          </span>
        )}
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1" title="P=Profile G=Games D=Documents">
          <StatusBadge label="P" active={inv.has_financial_context} />
          <StatusBadge label="G" active={inv.has_game_session} />
          <StatusBadge label="D" active={inv.has_documents} />
        </div>
        <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button onClick={() => onStartJourney(inv.id, inv.name)}
            className="text-[10px] font-bold px-2.5 py-1 rounded-lg bg-teal-600 text-white hover:bg-teal-700 transition-colors">
            {isComplete ? 'Resume' : 'Start'}
          </button>
          {isComplete && (
            <button onClick={() => onViewReport(inv.id, inv.name)}
              className="text-[10px] font-bold px-2.5 py-1 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors">
              Report
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Dashboard({ onStartJourney, onViewReport }) {
  const [investors, setInvestors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newCode, setNewCode] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    getInvestors().then(inv => { setInvestors(inv); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const completed = investors.filter(i => i.has_financial_context && i.has_game_session);
  const inProgress = investors.filter(i => (i.has_financial_context || i.has_game_session) && !(i.has_financial_context && i.has_game_session));
  const notStarted = investors.filter(i => !i.has_financial_context && !i.has_game_session);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const code = newCode.trim() || newName.trim().toUpperCase().replace(/\s+/g, '_').slice(0, 10);
      await createInvestor({ name: newName.trim(), code });
      const inv = await getInvestors();
      setInvestors(inv);
      setNewName(''); setNewCode(''); setShowCreate(false);
    } catch (err) { alert(err.message); }
    setCreating(false);
  };

  if (loading) return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-4">{[1,2,3,4].map(i => <div key={i} className="h-24 bg-slate-100 animate-pulse rounded-xl" />)}</div>
      <div className="grid grid-cols-3 gap-4">{[1,2,3].map(i => <div key={i} className="h-40 bg-slate-100 animate-pulse rounded-xl" />)}</div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* KPI Row */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total Investors', value: investors.length, color: '#0d9488' },
          { label: 'Assessments Complete', value: completed.length, color: '#059669' },
          { label: 'In Progress', value: inProgress.length, color: '#d97706' },
          { label: 'With Transaction Data', value: investors.filter(i => i.has_documents).length, color: '#7c3aed' },
        ].map(kpi => (
          <div key={kpi.label} className="bg-white rounded-xl border border-slate-200 p-5">
            <p className="text-[11px] text-slate-400 font-medium">{kpi.label}</p>
            <p className="text-2xl font-bold font-mono mt-1" style={{ color: kpi.color }}>{kpi.value}</p>
          </div>
        ))}
      </div>

      {/* New Investor */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-800">Investor Registry</h2>
          <p className="text-[11px] text-slate-400">Select an investor to start or continue their assessment</p>
        </div>
        <button onClick={() => setShowCreate(true)}
          className="text-xs font-bold px-4 py-2 rounded-lg bg-teal-600 text-white hover:bg-teal-700 transition-colors">
          + New Investor
        </button>
      </div>

      {showCreate && (
        <div className="bg-teal-50 rounded-xl border border-teal-200 p-4">
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="text-[10px] text-slate-500 font-bold block mb-1">Investor Name</label>
              <input type="text" value={newName} onChange={e => setNewName(e.target.value)} placeholder="e.g. Rajesh Mehta"
                className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:ring-2 focus:ring-teal-500 outline-none" />
            </div>
            <div className="w-32">
              <label className="text-[10px] text-slate-500 font-bold block mb-1">Code</label>
              <input type="text" value={newCode} onChange={e => setNewCode(e.target.value)} placeholder="Auto"
                className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:ring-2 focus:ring-teal-500 outline-none" />
            </div>
            <button onClick={handleCreate} disabled={creating || !newName.trim()}
              className="text-xs font-bold px-4 py-2 rounded-lg bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-40 transition-colors">
              {creating ? '...' : 'Create'}
            </button>
            <button onClick={() => setShowCreate(false)}
              className="text-xs font-bold px-4 py-2 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 transition-colors">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Empty state */}
      {investors.length === 0 && (
        <div className="text-center py-16 bg-white rounded-xl border border-slate-200">
          <p className="text-sm text-slate-500 mb-3">No investors yet. Create one to begin.</p>
          <button onClick={() => setShowCreate(true)}
            className="text-xs font-bold px-4 py-2 rounded-lg bg-teal-600 text-white hover:bg-teal-700 transition-colors">
            + Create Investor
          </button>
        </div>
      )}

      {/* Completed Section */}
      {completed.length > 0 && (
        <div>
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
            Completed ({completed.length})
          </h3>
          <div className="grid grid-cols-3 gap-4">
            {completed.map(inv => (
              <InvestorCard key={inv.id} inv={inv} onStartJourney={onStartJourney} onViewReport={onViewReport} />
            ))}
          </div>
        </div>
      )}

      {/* In Progress Section */}
      {inProgress.length > 0 && (
        <div>
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
            In Progress ({inProgress.length})
          </h3>
          <div className="grid grid-cols-3 gap-4">
            {inProgress.map(inv => (
              <InvestorCard key={inv.id} inv={inv} onStartJourney={onStartJourney} onViewReport={onViewReport} />
            ))}
          </div>
        </div>
      )}

      {/* Not Started Section */}
      {notStarted.length > 0 && (
        <div>
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
            Not Started ({notStarted.length})
          </h3>
          <div className="grid grid-cols-3 gap-4">
            {notStarted.map(inv => (
              <InvestorCard key={inv.id} inv={inv} onStartJourney={onStartJourney} onViewReport={onViewReport} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
