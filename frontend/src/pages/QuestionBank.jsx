import { useState, useEffect } from 'react'
import { Card, Badge, Btn, Bar, LoadingSpinner } from '../components/UI'
import { getQuestions, getQuestionStats, createQuestion, deleteQuestion } from '../services/api'

export default function QuestionBank() {
  const [questions, setQuestions] = useState([]);
  const [stats, setStats] = useState(null);
  const [filter, setFilter] = useState('all');
  const [expanded, setExpanded] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);

  const load = () => {
    setLoading(true);
    Promise.all([getQuestions(), getQuestionStats()]).then(([q, s]) => {
      setQuestions(q); setStats(s); setLoading(false);
    }).catch(() => setLoading(false));
  };
  useEffect(load, []);

  const filtered = filter === 'all' ? questions : questions.filter(q => q.tier === filter);
  const tierColor = { anchor: '#1746a2', diagnostic: '#0891b2', calibration: '#d97706' };

  const handleDelete = async (code) => {
    if (!confirm(`Deactivate question ${code}?`)) return;
    await deleteQuestion(code);
    load();
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <div className="grid grid-cols-4 gap-3 mb-5">
        <Card><div className="text-[11px] text-gray-400">Total Questions</div><div className="text-2xl font-extrabold">{stats?.total || 0}</div></Card>
        <Card><div className="text-[11px] text-gray-400">Anchors</div><div className="text-2xl font-extrabold text-blue-800">{stats?.anchors || 0}</div><div className="text-[10px] text-gray-400">Baseline comparability</div></Card>
        <Card><div className="text-[11px] text-gray-400">Diagnostics</div><div className="text-2xl font-extrabold text-cyan-700">{stats?.diagnostics || 0}</div><div className="text-[10px] text-gray-400">Adaptive deep-dive</div></Card>
        <Card><div className="text-[11px] text-gray-400">Calibrations</div><div className="text-2xl font-extrabold text-amber-600">{stats?.calibrations || 0}</div><div className="text-[10px] text-gray-400">Consistency checks</div></Card>
      </div>

      <Card>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold">Question Pool</h3>
            <p className="text-[10.5px] text-gray-400">Anchor → Diagnostic (adaptive) → Calibration (consistency)</p>
          </div>
          <div className="flex gap-2">
            {['all', 'anchor', 'diagnostic', 'calibration'].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-3 py-1 rounded-full text-[11px] font-bold ${filter === f ? 'bg-blue-800 text-white' : 'bg-gray-100 text-gray-500'}`}>
                {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          {filtered.map((q, i) => (
            <div key={q.code} onClick={() => setExpanded(expanded === q.code ? null : q.code)}
              className={`p-3 rounded-xl border cursor-pointer transition-all ${expanded === q.code ? 'border-blue-200 bg-blue-50/50' : 'border-gray-100 hover:bg-gray-50'}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono font-bold text-gray-400 w-10">{q.code}</span>
                  <Badge color={tierColor[q.tier] || '#666'}>{q.tier}</Badge>
                  <span className="text-xs text-gray-800 font-semibold line-clamp-1">{q.text}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-gray-400">d={q.discrimination}</span>
                  {!q.is_active && <Badge color="#dc2626">Inactive</Badge>}
                </div>
              </div>

              {expanded === q.code && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  {q.rationale && (
                    <div className="bg-blue-50 p-2 rounded-lg text-[11px] text-blue-700 mb-3">
                      <span className="font-bold">Rationale:</span> {q.rationale}
                    </div>
                  )}

                  <div className="text-[10px] font-bold text-gray-400 uppercase mb-2">Options</div>
                  <div className="space-y-1.5 mb-3">
                    {q.options?.map((opt, j) => (
                      <div key={j} className="flex items-center gap-2 p-2 rounded-lg bg-white border border-gray-100 text-xs">
                        <span className="w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center text-[10px] font-bold text-gray-500">{String.fromCharCode(65+j)}</span>
                        <span className="flex-1">{opt.text}</span>
                        <div className="flex gap-1">
                          {opt.scores && Object.entries(opt.scores).map(([trait, score]) => (
                            <span key={trait} className="text-[9px] px-1.5 py-0.5 rounded bg-gray-50 text-gray-500">
                              {trait.split('_').map(w=>w[0]).join('')}:{score}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="text-[10px] font-bold text-gray-400 uppercase mb-2">Trait Weights</div>
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {q.trait_weights && Object.entries(q.trait_weights).filter(([,v]) => v > 0).map(([k, v]) => (
                      <span key={k} className="text-[10px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-bold">
                        {k.replace(/_/g, ' ')}: {v}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-gray-400">
                    <div className="flex gap-4">
                      <span>Difficulty: <strong>{q.difficulty}</strong></span>
                      <span>Discrimination: <strong>{q.discrimination}</strong></span>
                      {q.calibrates && <span>Calibrates: <strong>{q.calibrates}</strong></span>}
                    </div>
                    <Btn small onClick={(e) => { e.stopPropagation(); handleDelete(q.code); }}>Deactivate</Btn>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
