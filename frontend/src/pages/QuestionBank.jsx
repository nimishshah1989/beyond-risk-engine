import { useState, useEffect } from 'react'
import { Card, Badge, Btn, Bar, LoadingSpinner } from '../components/UI'
import { getQuestions, getQuestionStats, createQuestion, updateQuestion, deleteQuestion } from '../services/api'

const TRAIT_IDS = [
  'loss_aversion', 'horizon_tolerance', 'liquidity_sensitivity', 'behavioral_stability',
  'ambiguity_tolerance', 'regret_sensitivity', 'leverage_comfort', 'goal_rigidity',
  'emotional_volatility', 'decision_confidence'
];

const EMPTY_QUESTION = {
  code: '', tier: 'diagnostic', text: '', rationale: '', difficulty: 0.5,
  discrimination: 1.5, trait_weights: {}, options: [
    { text: '', scores: {} }, { text: '', scores: {} }, { text: '', scores: {} }, { text: '', scores: {} }
  ], calibrates: ''
};

export default function QuestionBank() {
  const [questions, setQuestions] = useState([]);
  const [stats, setStats] = useState(null);
  const [filter, setFilter] = useState('all');
  const [expanded, setExpanded] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [form, setForm] = useState({ ...EMPTY_QUESTION });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);
  const [search, setSearch] = useState('');

  const load = () => {
    setLoading(true);
    Promise.all([getQuestions(), getQuestionStats()]).then(([q, s]) => {
      setQuestions(q); setStats(s); setLoading(false);
    }).catch(() => setLoading(false));
  };
  useEffect(load, []);

  const filtered = questions.filter(q => {
    const matchesTier = filter === 'all' || q.tier === filter;
    const matchesSearch = !search || q.text.toLowerCase().includes(search.toLowerCase()) || q.code.toLowerCase().includes(search.toLowerCase());
    return matchesTier && matchesSearch;
  });

  const tierColor = { anchor: '#1746a2', diagnostic: '#0891b2', calibration: '#d97706' };

  const handleDelete = async (code) => {
    if (!confirm(`Deactivate question ${code}?`)) return;
    await deleteQuestion(code);
    load();
  };

  const handleEdit = (q) => {
    setForm({
      code: q.code, tier: q.tier, text: q.text, rationale: q.rationale || '',
      difficulty: q.difficulty, discrimination: q.discrimination,
      trait_weights: { ...q.trait_weights },
      options: q.options.map(o => ({ text: o.text, scores: { ...o.scores } })),
      calibrates: q.calibrates || ''
    });
    setEditMode(true);
    setShowForm(true);
    setFormError(null);
  };

  const handleNew = () => {
    setForm({ ...EMPTY_QUESTION, options: [{ text: '', scores: {} }, { text: '', scores: {} }, { text: '', scores: {} }, { text: '', scores: {} }] });
    setEditMode(false);
    setShowForm(true);
    setFormError(null);
  };

  const handleSave = async () => {
    if (!form.code || !form.text || form.options.some(o => !o.text)) {
      setFormError('Code, question text, and all option texts are required');
      return;
    }
    setSaving(true); setFormError(null);
    try {
      if (editMode) {
        await updateQuestion(form.code, form);
      } else {
        await createQuestion(form);
      }
      setShowForm(false);
      load();
    } catch (e) {
      setFormError(e.message);
    }
    setSaving(false);
  };

  const updateOption = (idx, field, value) => {
    const opts = [...form.options];
    if (field === 'text') opts[idx].text = value;
    else { opts[idx].scores = { ...opts[idx].scores, [field]: parseInt(value) || 0 }; }
    setForm({ ...form, options: opts });
  };

  const updateTraitWeight = (trait, value) => {
    const tw = { ...form.trait_weights };
    if (value === '' || value === '0') delete tw[trait];
    else tw[trait] = parseFloat(value) || 0;
    setForm({ ...form, trait_weights: tw });
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      {/* KPIs */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        <Card><div className="text-[11px] text-gray-400">Total Questions</div><div className="text-2xl font-extrabold">{stats?.total || 0}</div></Card>
        <Card><div className="text-[11px] text-gray-400">Anchors</div><div className="text-2xl font-extrabold text-blue-800">{stats?.anchors || 0}</div><div className="text-[10px] text-gray-400">Always asked first — baseline</div></Card>
        <Card><div className="text-[11px] text-gray-400">Diagnostics</div><div className="text-2xl font-extrabold text-cyan-700">{stats?.diagnostics || 0}</div><div className="text-[10px] text-gray-400">Adaptively selected by AI</div></Card>
        <Card><div className="text-[11px] text-gray-400">Calibrations</div><div className="text-2xl font-extrabold text-amber-600">{stats?.calibrations || 0}</div><div className="text-[10px] text-gray-400">Consistency verification</div></Card>
      </div>

      {/* Add/Edit Form Modal */}
      {showForm && (
        <Card className="mb-5 border-blue-200 bg-blue-50/30">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold">{editMode ? `Edit Question: ${form.code}` : 'Add New Question'}</h3>
            <Btn small onClick={() => setShowForm(false)}>✕ Cancel</Btn>
          </div>
          {formError && <div className="bg-red-50 text-red-700 text-xs p-2 rounded-lg mb-3">{formError}</div>}

          <div className="grid grid-cols-4 gap-3 mb-3">
            <div>
              <label className="text-[10px] text-gray-500 font-bold block mb-1">Code *</label>
              <input value={form.code} onChange={e => setForm({...form, code: e.target.value})} disabled={editMode}
                className="w-full px-2 py-1.5 rounded border border-gray-200 text-xs" placeholder="e.g. D16" />
            </div>
            <div>
              <label className="text-[10px] text-gray-500 font-bold block mb-1">Tier *</label>
              <select value={form.tier} onChange={e => setForm({...form, tier: e.target.value})}
                className="w-full px-2 py-1.5 rounded border border-gray-200 text-xs">
                <option value="anchor">Anchor</option><option value="diagnostic">Diagnostic</option><option value="calibration">Calibration</option>
              </select>
            </div>
            <div>
              <label className="text-[10px] text-gray-500 font-bold block mb-1">Difficulty (0-1)</label>
              <input value={form.difficulty} onChange={e => setForm({...form, difficulty: parseFloat(e.target.value) || 0})} type="number" step="0.1"
                className="w-full px-2 py-1.5 rounded border border-gray-200 text-xs" />
            </div>
            <div>
              <label className="text-[10px] text-gray-500 font-bold block mb-1">Discrimination</label>
              <input value={form.discrimination} onChange={e => setForm({...form, discrimination: parseFloat(e.target.value) || 1})} type="number" step="0.1"
                className="w-full px-2 py-1.5 rounded border border-gray-200 text-xs" />
            </div>
          </div>

          <div className="mb-3">
            <label className="text-[10px] text-gray-500 font-bold block mb-1">Question Text *</label>
            <textarea value={form.text} onChange={e => setForm({...form, text: e.target.value})} rows={2}
              className="w-full px-2 py-1.5 rounded border border-gray-200 text-xs" placeholder="Your portfolio drops 20%..." />
          </div>

          <div className="mb-3">
            <label className="text-[10px] text-gray-500 font-bold block mb-1">Rationale (why this question exists)</label>
            <input value={form.rationale} onChange={e => setForm({...form, rationale: e.target.value})}
              className="w-full px-2 py-1.5 rounded border border-gray-200 text-xs" placeholder="Measures loss aversion in a realistic scenario" />
          </div>

          {/* Trait weights */}
          <div className="mb-3">
            <label className="text-[10px] text-gray-500 font-bold block mb-1">Trait Weights (which traits this question measures, 0-3)</label>
            <div className="grid grid-cols-5 gap-2">
              {TRAIT_IDS.map(t => (
                <div key={t} className="flex items-center gap-1">
                  <span className="text-[9px] text-gray-400 truncate w-16">{t.split('_').map(w=>w[0].toUpperCase()).join('')}</span>
                  <input value={form.trait_weights[t] || ''} onChange={e => updateTraitWeight(t, e.target.value)}
                    type="number" step="0.5" min="0" max="3"
                    className="w-12 px-1 py-0.5 rounded border border-gray-200 text-[10px] text-center" placeholder="0" />
                </div>
              ))}
            </div>
          </div>

          {/* Options */}
          <div className="mb-3">
            <label className="text-[10px] text-gray-500 font-bold block mb-2">Options (4 choices with trait scores 0-100)</label>
            {form.options.map((opt, oi) => (
              <div key={oi} className="mb-2 p-2 bg-white rounded-lg border border-gray-100">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-[10px] font-bold text-gray-400 w-4">{String.fromCharCode(65+oi)}</span>
                  <input value={opt.text} onChange={e => updateOption(oi, 'text', e.target.value)}
                    className="flex-1 px-2 py-1 rounded border border-gray-200 text-xs" placeholder="Option text..." />
                </div>
                <div className="flex gap-1.5 flex-wrap">
                  {Object.keys(form.trait_weights).filter(t => form.trait_weights[t] > 0).map(t => (
                    <div key={t} className="flex items-center gap-0.5">
                      <span className="text-[8px] text-gray-400">{t.split('_').map(w=>w[0]).join('')}:</span>
                      <input value={opt.scores[t] || ''} onChange={e => updateOption(oi, t, e.target.value)}
                        type="number" min="0" max="100"
                        className="w-10 px-0.5 py-0 rounded border border-gray-200 text-[9px] text-center" placeholder="50" />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2">
            <Btn onClick={() => setShowForm(false)}>Cancel</Btn>
            <Btn primary onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : editMode ? 'Update Question' : 'Add Question'}</Btn>
          </div>
        </Card>
      )}

      {/* Question list */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold">Question Pool</h3>
            <p className="text-[10.5px] text-gray-400">Anchor → Diagnostic (adaptive) → Calibration (consistency)</p>
          </div>
          <div className="flex gap-2 items-center">
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search..."
              className="px-2 py-1 rounded-lg border border-gray-200 text-xs w-36 focus:outline-none focus:ring-1 focus:ring-blue-200" />
            {['all', 'anchor', 'diagnostic', 'calibration'].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-3 py-1 rounded-full text-[11px] font-bold ${filter === f ? 'bg-blue-800 text-white' : 'bg-gray-100 text-gray-500'}`}>
                {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
            <Btn primary small onClick={handleNew}>+ Add Question</Btn>
          </div>
        </div>

        <div className="space-y-2">
          {filtered.map((q) => (
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
                  {q.trait_weights && Object.keys(q.trait_weights).filter(t => q.trait_weights[t] > 0).map(t => (
                    <span key={t} className="text-[8px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 font-bold">
                      {t.split('_').map(w=>w[0].toUpperCase()).join('')}
                    </span>
                  ))}
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

                  <div className="text-[10px] font-bold text-gray-400 uppercase mb-2">Options & Scoring</div>
                  <div className="space-y-1.5 mb-3">
                    {q.options?.map((opt, j) => (
                      <div key={j} className="flex items-center gap-2 p-2 rounded-lg bg-white border border-gray-100 text-xs">
                        <span className="w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center text-[10px] font-bold text-gray-500">{String.fromCharCode(65+j)}</span>
                        <span className="flex-1">{opt.text}</span>
                        <div className="flex gap-1">
                          {opt.scores && Object.entries(opt.scores).map(([trait, score]) => (
                            <span key={trait} className="text-[9px] px-1.5 py-0.5 rounded font-bold"
                              style={{ background: score >= 70 ? '#fef2f2' : score >= 40 ? '#fffbeb' : '#ecfdf5', color: score >= 70 ? '#dc2626' : score >= 40 ? '#d97706' : '#059669' }}>
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
                    <div className="flex gap-2">
                      <Btn small onClick={(e) => { e.stopPropagation(); handleEdit(q); }}>Edit</Btn>
                      <Btn small onClick={(e) => { e.stopPropagation(); handleDelete(q.code); }}>Deactivate</Btn>
                    </div>
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
