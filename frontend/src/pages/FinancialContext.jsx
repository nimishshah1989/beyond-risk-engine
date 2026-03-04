import { useState, useEffect, useCallback } from 'react'
import { Card, Badge, Bar } from '../components/UI'

const BASE = import.meta.env.VITE_API_URL || '';

// --- Helpers ---

function formatINR(lakhs) {
  if (lakhs == null || lakhs === '') return '';
  const num = Number(lakhs);
  if (isNaN(num)) return '';
  if (num >= 100) return `₹${(num / 100).toFixed(2)} Cr`;
  return `₹${num.toFixed(2)} L`;
}

function fmtLakhs(v) {
  if (v == null || v === '') return '—';
  return `₹${Number(v).toLocaleString('en-IN')} L`;
}

async function apiGet(path) {
  const res = await fetch(`${BASE}${path}`, { headers: { 'Content-Type': 'application/json' } });
  if (!res.ok) { const e = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(e.detail || 'Request failed'); }
  return res.json();
}

async function apiPost(path, data) {
  const res = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
  if (!res.ok) { const e = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(e.detail || 'Request failed'); }
  return res.json();
}

// --- Sub-components ---

function Toast({ message, type, onClose }) {
  if (!message) return null;
  const bg = type === 'error' ? 'bg-red-50 border-red-200 text-red-700' : 'bg-emerald-50 border-emerald-200 text-emerald-700';
  return (
    <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl border text-sm font-medium shadow-sm ${bg} flex items-center gap-3`}>
      <span>{message}</span>
      <button onClick={onClose} className="text-xs opacity-60 hover:opacity-100">&#x2715;</button>
    </div>
  );
}

function SectionHeader({ index, title, icon, isOpen, isComplete, onClick }) {
  return (
    <button onClick={onClick} className={`w-full flex items-center gap-3 px-5 py-3.5 text-left transition-colors rounded-xl border ${isOpen ? 'bg-teal-50 border-teal-200' : 'bg-white border-slate-200 hover:bg-slate-50'}`}>
      <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${isComplete ? 'bg-emerald-600 text-white' : isOpen ? 'bg-teal-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
        {isComplete ? '✓' : index + 1}
      </span>
      <span className="text-base">{icon}</span>
      <span className={`text-sm font-semibold ${isOpen ? 'text-teal-700' : 'text-slate-700'}`}>{title}</span>
      <span className="ml-auto text-slate-400 text-xs">{isOpen ? '▼' : '▶'}</span>
    </button>
  );
}

function Field({ label, helper, children, monetary }) {
  return (
    <div>
      <label className="text-xs text-slate-500 font-semibold block mb-1">{monetary && <span className="text-teal-600 mr-0.5">₹</span>}{label}</label>
      {children}
      {helper && <p className="text-[10px] text-slate-400 mt-0.5">{helper}</p>}
    </div>
  );
}

function NumInput({ value, onChange, placeholder, className = '' }) {
  return <input type="number" value={value ?? ''} onChange={e => onChange(e.target.value === '' ? '' : Number(e.target.value))} placeholder={placeholder} className={`w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 font-mono placeholder:text-slate-400 focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none ${className}`} />;
}

function Select({ value, onChange, options, placeholder }) {
  return (
    <select value={value || ''} onChange={e => onChange(e.target.value)} className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none">
      {placeholder && <option value="">{placeholder}</option>}
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function TextArea({ value, onChange, placeholder, rows = 3 }) {
  return <textarea value={value || ''} onChange={e => onChange(e.target.value)} placeholder={placeholder} rows={rows} className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none resize-none" />;
}

function RadioGroup({ value, onChange, options }) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map(o => (
        <button key={o.value} onClick={() => onChange(o.value)} className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${value === o.value ? 'bg-teal-600 text-white border-teal-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

function CapacityGauge({ score }) {
  const s = score ?? 0;
  const color = s <= 30 ? '#dc2626' : s <= 60 ? '#d97706' : '#059669';
  const label = s <= 30 ? 'Low Capacity' : s <= 60 ? 'Moderate Capacity' : 'High Capacity';
  const bg = s <= 30 ? 'bg-red-50' : s <= 60 ? 'bg-amber-50' : 'bg-emerald-50';
  return (
    <div className={`${bg} rounded-xl p-5 text-center`}>
      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-2">Financial Capacity Score</p>
      <p className="text-5xl font-bold font-mono" style={{ color }}>{s}</p>
      <p className="text-xl text-slate-400 font-mono">/100</p>
      <div className="w-full bg-slate-200 rounded-full h-3 mt-3 max-w-xs mx-auto">
        <div className="h-3 rounded-full transition-all duration-700" style={{ width: `${s}%`, background: color }} />
      </div>
      <p className="text-sm font-semibold mt-2" style={{ color }}>{label}</p>
    </div>
  );
}

// --- Skeleton ---

function FormSkeleton() {
  return (
    <div className="max-w-3xl mx-auto mt-6 space-y-3">
      {[1,2,3,4,5,6].map(i => <div key={i} className="h-14 bg-slate-100 animate-pulse rounded-xl" />)}
    </div>
  );
}

// --- Field Mapping (frontend shorthand → backend API field names) ---

const FIELD_MAP_TO_API = {
  monthly_obligations: 'monthly_fixed_obligations',
  annual_discretionary: 'annual_discretionary_spend',
  obligation_1y: 'upcoming_obligations_1y',
  obligation_3y: 'upcoming_obligations_3y',
  obligation_5y: 'upcoming_obligations_5y',
  obligation_10y: 'upcoming_obligations_10y',
  equity_mf: 'existing_equity_mf',
  debt_mf: 'existing_debt_mf',
  direct_equity: 'existing_direct_equity',
  fixed_deposits: 'existing_fixed_deposits',
  real_estate: 'existing_real_estate_value',
  gold: 'existing_gold',
  ppf_epf_nps: 'existing_ppf_epf_nps',
  insurance_corpus: 'existing_insurance_corpus',
  other_investments: 'existing_other_investments',
  cash_savings: 'existing_cash_savings',
  primary_residence: 'primary_residence_value',
  total_liabilities: 'existing_liabilities',
  income_growth: 'income_growth_expectation',
  has_loss_experience: 'has_experienced_real_loss',
  loss_context: 'worst_loss_context',
  loss_behavior: 'behavior_during_loss',
  recovery_experience: 'loss_recovery_experience',
  target_return: 'target_return_annual_pct',
  time_horizon: 'time_horizon_years',
  family_influence: 'family_influence_level',
  has_advisor: 'existing_advisor_relationship',
};

const FIELD_MAP_FROM_API = Object.fromEntries(
  Object.entries(FIELD_MAP_TO_API).map(([k, v]) => [v, k])
);

function toApiPayload(form) {
  const payload = {};
  for (const [key, val] of Object.entries(form)) {
    if (val === '' || val === null || val === undefined) continue;
    const apiKey = FIELD_MAP_TO_API[key] || key;
    payload[apiKey] = val;
  }
  return payload;
}

function fromApiContext(ctx) {
  if (!ctx || typeof ctx !== 'object') return {};
  const form = {};
  for (const [key, val] of Object.entries(ctx)) {
    const formKey = FIELD_MAP_FROM_API[key] || key;
    form[formKey] = val;
  }
  return form;
}

// --- Default State ---

const EMPTY_FORM = {
  // Meaning of money
  money_meaning: '', first_instinct: '',
  // Fear & emotional landscape
  worst_fear: '', fear_impact: '', regret_preference: '',
  // Knowledge & experience
  knowledge_level: '', investment_experience: [], wealth_concentration: '',
  equity_experience: null, downturn_behavior: '', recovery_behavior: '',
  // Income & stability
  annual_income: '', income_source: '', income_stability: '', income_growth: '', years_to_retirement: '',
  monthly_obligations: '', annual_discretionary: '',
  obligation_1y: '', obligation_3y: '', obligation_5y: '', obligation_10y: '', obligation_notes: '',
  equity_mf: '', debt_mf: '', direct_equity: '', fixed_deposits: '', real_estate: '',
  gold: '', ppf_epf_nps: '', insurance_corpus: '', other_investments: '', cash_savings: '',
  primary_residence: '', total_liabilities: '',
  has_loss_experience: false, worst_loss_amount: '', loss_context: '', loss_behavior: '', recovery_experience: '',
  target_return: '', return_purpose: '', time_horizon: '',
  decision_maker: '', family_influence: '', has_advisor: false, tax_bracket: '',
};

const ASSET_FIELDS = [
  { key: 'equity_mf', label: 'Equity MF' }, { key: 'debt_mf', label: 'Debt MF' },
  { key: 'direct_equity', label: 'Direct Equity' }, { key: 'fixed_deposits', label: 'Fixed Deposits' },
  { key: 'real_estate', label: 'Real Estate (non-primary)' }, { key: 'gold', label: 'Gold' },
  { key: 'ppf_epf_nps', label: 'PPF / EPF / NPS' }, { key: 'insurance_corpus', label: 'Insurance Corpus' },
  { key: 'other_investments', label: 'Other Investments' }, { key: 'cash_savings', label: 'Cash Savings' },
];

const EXPERIENCE_OPTIONS = [
  { value: 'direct_equity', label: 'Direct Equities' },
  { value: 'equity_mf', label: 'Equity Mutual Funds' },
  { value: 'debt_mf', label: 'Debt Mutual Funds' },
  { value: 'bonds', label: 'Bonds / NCDs' },
  { value: 'pms', label: 'PMS' },
  { value: 'aif', label: 'AIF' },
  { value: 'real_estate', label: 'Real Estate Investment' },
  { value: 'gold', label: 'Gold / Commodities' },
  { value: 'international', label: 'International Funds' },
  { value: 'structured', label: 'Structured Products' },
  { value: 'crypto', label: 'Crypto / Digital Assets' },
  { value: 'fno', label: 'F&O / Derivatives' },
];

function EmotionCard({ icon, label, tag, description, selected, onClick }) {
  return (
    <button onClick={() => onClick(tag)} className={`flex flex-col items-center text-center p-4 rounded-xl border-2 transition-all ${selected ? 'border-teal-500 bg-teal-50 shadow-sm' : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'}`}>
      <span className="text-2xl mb-1.5">{icon}</span>
      <span className={`text-xs font-bold ${selected ? 'text-teal-700' : 'text-slate-700'}`}>{label}</span>
      {description && <span className="text-[10px] text-slate-400 mt-0.5 leading-tight">{description}</span>}
    </button>
  );
}

function CheckboxGroup({ options, selected, onChange }) {
  const toggle = (val) => {
    const set = new Set(selected || []);
    if (set.has(val)) set.delete(val); else set.add(val);
    onChange([...set]);
  };
  return (
    <div className="flex flex-wrap gap-2">
      {options.map(o => (
        <button key={o.value} onClick={() => toggle(o.value)} className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${(selected || []).includes(o.value) ? 'bg-teal-600 text-white border-teal-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

const SECTIONS = [
  { title: 'Meaning of Money', icon: '💎' },
  { title: 'Fear & Emotional Landscape', icon: '🌊' },
  { title: 'Knowledge & Experience', icon: '📚' },
  { title: 'Income & Stability', icon: '💼' },
  { title: 'Obligations & Liquidity Needs', icon: '📅' },
  { title: 'Existing Assets (Balance Sheet)', icon: '🏦' },
  { title: 'Real Loss Experience', icon: '📉' },
  { title: 'Return Aspirations', icon: '🎯' },
  { title: 'Decision Making', icon: '🤝' },
];

// --- Main Component ---

export default function FinancialContext({ investorId, investorName, onComplete }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [openSection, setOpenSection] = useState(0);
  const [completedSections, setCompletedSections] = useState(new Set());
  const [capacity, setCapacity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState({ message: '', type: '' });

  const showToast = (message, type = 'success') => { setToast({ message, type }); setTimeout(() => setToast({ message: '', type: '' }), 3000); };
  const set = (key, val) => setForm(prev => ({ ...prev, [key]: val }));

  // Computed values
  const totalInvestable = ASSET_FIELDS.reduce((sum, f) => sum + (Number(form[f.key]) || 0), 0);
  const netWorth = totalInvestable + (Number(form.primary_residence) || 0) - (Number(form.total_liabilities) || 0);
  const liquidityRunway = (Number(form.monthly_obligations) || 1) > 0
    ? Math.round((Number(form.cash_savings) || 0) / (Number(form.monthly_obligations) || 1))
    : 0;
  const obligationCoverage = totalInvestable > 0
    ? ((totalInvestable - (Number(form.obligation_1y) || 0)) / totalInvestable * 100).toFixed(1)
    : 0;

  // Load existing context
  useEffect(() => {
    if (!investorId) { setLoading(false); return; }
    apiGet(`/api/context/${investorId}`)
      .then(data => {
        const ctx = data?.context || data;
        if (ctx && typeof ctx === 'object') setForm(prev => ({ ...prev, ...fromApiContext(ctx) }));
      })
      .catch(() => { /* No existing context — start fresh */ })
      .finally(() => setLoading(false));
  }, [investorId]);

  // Save section data
  const saveSection = useCallback(async () => {
    if (!investorId) return;
    setSaving(true);
    try {
      await apiPost(`/api/context/${investorId}`, toApiPayload(form));
      showToast('Saved');
    } catch (err) {
      showToast(err.message, 'error');
    }
    setSaving(false);
  }, [investorId, form]);

  // Fetch capacity score
  const fetchCapacity = useCallback(async () => {
    if (!investorId) return;
    try {
      const data = await apiGet(`/api/context/${investorId}/capacity`);
      setCapacity(data);
    } catch { /* Capacity endpoint may not be available yet */ }
  }, [investorId]);

  const handleSectionChange = (idx) => {
    // Mark current section as complete, save, then open new section
    setCompletedSections(prev => new Set([...prev, openSection]));
    saveSection();
    setOpenSection(idx === openSection ? -1 : idx);
    if (idx >= 5 || completedSections.size >= 5) fetchCapacity();
  };

  const isSectionComplete = (idx) => completedSections.has(idx);

  if (loading) return <FormSkeleton />;

  return (
    <div className="max-w-3xl mx-auto mt-2">
      <Toast message={toast.message} type={toast.type} onClose={() => setToast({ message: '', type: '' })} />

      {/* Header */}
      <div className="mb-5">
        <h2 className="text-xl font-semibold text-slate-800">Investor Profile — Understanding You</h2>
        <p className="text-sm text-slate-500 mt-0.5">{investorName || 'Investor'} &middot; Complete all 9 sections for a comprehensive financial & emotional profile</p>
      </div>

      {/* Progress bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-5">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-500">{completedSections.size} of {SECTIONS.length} sections completed</span>
          {saving && <span className="text-[10px] text-teal-600 font-medium animate-pulse">Saving...</span>}
        </div>
        <div className="flex gap-1.5">
          {SECTIONS.map((_, i) => (
            <div key={i} className={`flex-1 h-2 rounded-full transition-colors ${isSectionComplete(i) ? 'bg-teal-500' : i === openSection ? 'bg-teal-200' : 'bg-slate-100'}`} />
          ))}
        </div>
      </div>

      {/* Sections */}
      <div className="space-y-2.5">

        {/* Section 1: Meaning of Money */}
        <div>
          <SectionHeader index={0} title={SECTIONS[0].title} icon={SECTIONS[0].icon} isOpen={openSection === 0} isComplete={isSectionComplete(0)} onClick={() => handleSectionChange(0)} />
          {openSection === 0 && (
            <Card className="mt-1.5">
              <div className="p-5 space-y-5">
                <div>
                  <p className="text-sm font-semibold text-slate-700 mb-1">What does money mean to you?</p>
                  <p className="text-xs text-slate-400 mb-3">Choose the one that resonates most deeply — there are no right answers</p>
                  <div className="grid grid-cols-5 gap-2.5">
                    <EmotionCard icon="🛡️" label="Security" tag="security" description="Never worrying about emergencies" selected={form.money_meaning === 'security'} onClick={v => set('money_meaning', v)} />
                    <EmotionCard icon="🌊" label="Freedom" tag="freedom" description="Ability to say no" selected={form.money_meaning === 'freedom'} onClick={v => set('money_meaning', v)} />
                    <EmotionCard icon="🏔️" label="Legacy" tag="legacy" description="Generational wealth" selected={form.money_meaning === 'legacy'} onClick={v => set('money_meaning', v)} />
                    <EmotionCard icon="✨" label="Lifestyle" tag="lifestyle" description="Living well" selected={form.money_meaning === 'lifestyle'} onClick={v => set('money_meaning', v)} />
                    <EmotionCard icon="📈" label="The Game" tag="game" description="Wealth as the score" selected={form.money_meaning === 'game'} onClick={v => set('money_meaning', v)} />
                  </div>
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-700 mb-1">When money comes in, what's your first instinct?</p>
                  <RadioGroup value={form.first_instinct} onChange={v => set('first_instinct', v)}
                    options={[{ value: 'save', label: 'Save it' }, { value: 'invest', label: 'Invest it' }, { value: 'spend', label: 'Spend / enjoy it' }, { value: 'give', label: 'Share / give it' }]} />
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Section 2: Fear & Emotional Landscape */}
        <div>
          <SectionHeader index={1} title={SECTIONS[1].title} icon={SECTIONS[1].icon} isOpen={openSection === 1} isComplete={isSectionComplete(1)} onClick={() => handleSectionChange(1)} />
          {openSection === 1 && (
            <Card className="mt-1.5">
              <div className="p-5 space-y-5">
                <div>
                  <p className="text-sm font-semibold text-slate-700 mb-1">What is your worst financial fear?</p>
                  <p className="text-xs text-slate-400 mb-3">The scenario that makes your stomach drop</p>
                  <div className="grid grid-cols-3 gap-2.5">
                    <EmotionCard icon="📉" label="Drawdown Loss" tag="drawdown" description="Portfolio losing 40%" selected={form.worst_fear === 'drawdown'} onClick={v => set('worst_fear', v)} />
                    <EmotionCard icon="🔐" label="Illiquidity" tag="illiquidity" description="Money locked when needed" selected={form.worst_fear === 'illiquidity'} onClick={v => set('worst_fear', v)} />
                    <EmotionCard icon="💸" label="Inflation Erosion" tag="inflation" description="Purchasing power eroding" selected={form.worst_fear === 'inflation'} onClick={v => set('worst_fear', v)} />
                    <EmotionCard icon="😔" label="FOMO" tag="fomo" description="Others building wealth, not me" selected={form.worst_fear === 'fomo'} onClick={v => set('worst_fear', v)} />
                    <EmotionCard icon="🏦" label="Trust Betrayal" tag="trust" description="Fraud, mismanagement" selected={form.worst_fear === 'trust'} onClick={v => set('worst_fear', v)} />
                    <EmotionCard icon="⚰️" label="Legacy Failure" tag="legacy" description="Family without resources" selected={form.worst_fear === 'legacy'} onClick={v => set('worst_fear', v)} />
                  </div>
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-700 mb-1">If your portfolio dropped 30% tomorrow, how would it affect you?</p>
                  <RadioGroup value={form.fear_impact} onChange={v => set('fear_impact', v)}
                    options={[
                      { value: 'panic', label: "Can't sleep, checking hourly" },
                      { value: 'anxious', label: 'Very stressed but holding' },
                      { value: 'steady', label: "Uncomfortable but trusting the process" },
                      { value: 'detached', label: 'Barely notice, might buy more' },
                    ]} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-700 mb-1">Which regret hurts more?</p>
                  <div className="grid grid-cols-2 gap-3">
                    <button onClick={() => set('regret_preference', 'loss_regret')} className={`p-4 rounded-xl border-2 text-left transition-all ${form.regret_preference === 'loss_regret' ? 'border-red-400 bg-red-50' : 'border-slate-200 hover:border-slate-300'}`}>
                      <span className="text-sm font-bold text-red-700">Invested aggressively and lost 40%</span>
                      <p className="text-xs text-slate-500 mt-1">The pain of actual financial loss</p>
                    </button>
                    <button onClick={() => set('regret_preference', 'miss_regret')} className={`p-4 rounded-xl border-2 text-left transition-all ${form.regret_preference === 'miss_regret' ? 'border-amber-400 bg-amber-50' : 'border-slate-200 hover:border-slate-300'}`}>
                      <span className="text-sm font-bold text-amber-700">Played it safe and missed a 200% rally</span>
                      <p className="text-xs text-slate-500 mt-1">The frustration of missed opportunity</p>
                    </button>
                  </div>
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Section 3: Knowledge & Experience */}
        <div>
          <SectionHeader index={2} title={SECTIONS[2].title} icon={SECTIONS[2].icon} isOpen={openSection === 2} isComplete={isSectionComplete(2)} onClick={() => handleSectionChange(2)} />
          {openSection === 2 && (
            <Card className="mt-1.5">
              <div className="p-5 space-y-5">
                <Field label="Investment Knowledge Level">
                  <RadioGroup value={form.knowledge_level} onChange={v => set('knowledge_level', v)}
                    options={[{ value: 'basic', label: 'Basic' }, { value: 'intermediate', label: 'Intermediate' }, { value: 'advanced', label: 'Advanced' }, { value: 'expert', label: 'Expert' }]} />
                </Field>
                <Field label="Investment Experience" helper="Select all asset classes you have invested in">
                  <CheckboxGroup options={EXPERIENCE_OPTIONS} selected={form.investment_experience} onChange={v => set('investment_experience', v)} />
                </Field>
                <div className="grid grid-cols-2 gap-4">
                  <Field label="Have you invested in equities before?">
                    <RadioGroup value={form.equity_experience === true ? 'YES' : form.equity_experience === false ? 'NO' : ''} onChange={v => set('equity_experience', v === 'YES')}
                      options={[{ value: 'YES', label: 'Yes' }, { value: 'NO', label: 'No' }]} />
                  </Field>
                  <Field label="What % of your total wealth is this portfolio?" helper="Concentration of wealth in this investment">
                    <div className="relative">
                      <NumInput value={form.wealth_concentration} onChange={v => set('wealth_concentration', v)} placeholder="e.g. 40" />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-slate-400 font-mono">%</span>
                    </div>
                  </Field>
                </div>
                {form.equity_experience && (
                  <div className="bg-blue-50 rounded-xl p-4 border border-blue-100 space-y-4">
                    <Field label="During a market downturn, what did you actually do?">
                      <RadioGroup value={form.downturn_behavior} onChange={v => set('downturn_behavior', v)}
                        options={[
                          { value: 'sold_all', label: 'Sold everything' },
                          { value: 'sold_some', label: 'Sold some' },
                          { value: 'held', label: 'Held through' },
                          { value: 'bought_more', label: 'Bought more' },
                          { value: 'not_invested', label: "Wasn't invested then" },
                        ]} />
                    </Field>
                    <Field label="After the downturn, what happened?">
                      <RadioGroup value={form.recovery_behavior} onChange={v => set('recovery_behavior', v)}
                        options={[
                          { value: 'full_recovery', label: 'Full recovery — stayed invested' },
                          { value: 'exited_early', label: 'Exited early — missed recovery' },
                          { value: 'never_returned', label: 'Never returned to equities' },
                        ]} />
                    </Field>
                  </div>
                )}
              </div>
            </Card>
          )}
        </div>

        {/* Section 4: Income & Stability */}
        <div>
          <SectionHeader index={3} title={SECTIONS[3].title} icon={SECTIONS[3].icon} isOpen={openSection === 3} isComplete={isSectionComplete(3)} onClick={() => handleSectionChange(3)} />
          {openSection === 3 && (
            <Card className="mt-1.5">
              <div className="grid grid-cols-2 gap-4 p-5">
                <Field label="Annual Income (Lakhs)" monetary>
                  <NumInput value={form.annual_income} onChange={v => set('annual_income', v)} placeholder="e.g. 25" />
                </Field>
                <Field label="Income Source">
                  <Select value={form.income_source} onChange={v => set('income_source', v)} placeholder="Select..."
                    options={[{ value: 'SALARIED', label: 'Salaried' }, { value: 'BUSINESS', label: 'Business' }, { value: 'PROFESSIONAL', label: 'Professional' }, { value: 'RETIRED', label: 'Retired' }, { value: 'MIXED', label: 'Mixed' }]} />
                </Field>
                <Field label="Income Stability">
                  <Select value={form.income_stability} onChange={v => set('income_stability', v)} placeholder="Select..."
                    options={[{ value: 'VERY_STABLE', label: 'Very Stable' }, { value: 'STABLE', label: 'Stable' }, { value: 'MODERATE', label: 'Moderate' }, { value: 'VOLATILE', label: 'Volatile' }]} />
                </Field>
                <Field label="Income Growth Expectation">
                  <Select value={form.income_growth} onChange={v => set('income_growth', v)} placeholder="Select..."
                    options={[{ value: 'GROWING', label: 'Growing' }, { value: 'STABLE', label: 'Stable' }, { value: 'DECLINING', label: 'Declining' }]} />
                </Field>
                <Field label="Years to Retirement">
                  <NumInput value={form.years_to_retirement} onChange={v => set('years_to_retirement', v)} placeholder="e.g. 15" />
                </Field>
              </div>
            </Card>
          )}
        </div>

        {/* Section 5: Obligations & Liquidity */}
        <div>
          <SectionHeader index={4} title={SECTIONS[4].title} icon={SECTIONS[4].icon} isOpen={openSection === 4} isComplete={isSectionComplete(4)} onClick={() => handleSectionChange(4)} />
          {openSection === 4 && (
            <Card className="mt-1.5">
              <div className="space-y-4 p-5">
                <div className="grid grid-cols-2 gap-4">
                  <Field label="Monthly Fixed Obligations (Lakhs/mo)" monetary helper="EMIs, rent, insurance, school fees">
                    <NumInput value={form.monthly_obligations} onChange={v => set('monthly_obligations', v)} placeholder="e.g. 1.5" />
                  </Field>
                  <Field label="Annual Discretionary Spend (Lakhs)" monetary helper="Lifestyle, travel, entertainment">
                    <NumInput value={form.annual_discretionary} onChange={v => set('annual_discretionary', v)} placeholder="e.g. 8" />
                  </Field>
                </div>
                <div>
                  <p className="text-xs text-slate-500 font-semibold mb-2"><span className="text-teal-600 mr-0.5">₹</span>Upcoming Obligations (Lakhs)</p>
                  <div className="grid grid-cols-4 gap-3">
                    <Field label="At 1 Year"><NumInput value={form.obligation_1y} onChange={v => set('obligation_1y', v)} placeholder="0" /></Field>
                    <Field label="At 3 Years"><NumInput value={form.obligation_3y} onChange={v => set('obligation_3y', v)} placeholder="0" /></Field>
                    <Field label="At 5 Years"><NumInput value={form.obligation_5y} onChange={v => set('obligation_5y', v)} placeholder="0" /></Field>
                    <Field label="At 10 Years"><NumInput value={form.obligation_10y} onChange={v => set('obligation_10y', v)} placeholder="0" /></Field>
                  </div>
                </div>
                <Field label="Obligation Notes" helper="e.g. daughter's wedding 2028, son's education 2030">
                  <TextArea value={form.obligation_notes} onChange={v => set('obligation_notes', v)} placeholder="Describe planned major expenses..." />
                </Field>
              </div>
            </Card>
          )}
        </div>

        {/* Section 6: Existing Assets */}
        <div>
          <SectionHeader index={5} title={SECTIONS[5].title} icon={SECTIONS[5].icon} isOpen={openSection === 5} isComplete={isSectionComplete(5)} onClick={() => handleSectionChange(5)} />
          {openSection === 5 && (
            <Card className="mt-1.5">
              <div className="p-5 space-y-4">
                <p className="text-xs text-slate-400">Enter all values in Lakhs (₹)</p>
                <div className="grid grid-cols-2 gap-3">
                  {ASSET_FIELDS.map(f => (
                    <Field key={f.key} label={f.label} monetary>
                      <NumInput value={form[f.key]} onChange={v => set(f.key, v)} placeholder="0" />
                    </Field>
                  ))}
                </div>
                <div className="border-t border-slate-100 pt-4 grid grid-cols-2 gap-3">
                  <Field label="Primary Residence Value (not investable)" monetary>
                    <NumInput value={form.primary_residence} onChange={v => set('primary_residence', v)} placeholder="0" />
                  </Field>
                  <Field label="Total Outstanding Liabilities" monetary>
                    <NumInput value={form.total_liabilities} onChange={v => set('total_liabilities', v)} placeholder="0" />
                  </Field>
                </div>
                {/* Computed totals */}
                <div className="bg-slate-50 rounded-xl p-4 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-slate-400 mb-0.5">Total Investable Assets</p>
                    <p className="text-xl font-bold font-mono text-teal-600">{formatINR(totalInvestable)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400 mb-0.5">Net Worth</p>
                    <p className={`text-xl font-bold font-mono ${netWorth >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatINR(netWorth)}</p>
                  </div>
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Section 7: Real Loss Experience */}
        <div>
          <SectionHeader index={6} title={SECTIONS[6].title} icon={SECTIONS[6].icon} isOpen={openSection === 6} isComplete={isSectionComplete(6)} onClick={() => handleSectionChange(6)} />
          {openSection === 6 && (
            <Card className="mt-1.5">
              <div className="p-5 space-y-4">
                <Field label="Have you experienced a real investment loss?">
                  <RadioGroup value={form.has_loss_experience ? 'YES' : 'NO'} onChange={v => set('has_loss_experience', v === 'YES')}
                    options={[{ value: 'YES', label: 'Yes' }, { value: 'NO', label: 'No' }]} />
                </Field>
                {form.has_loss_experience && (
                  <div className="space-y-4 bg-red-50 rounded-xl p-4 border border-red-100">
                    <div className="grid grid-cols-2 gap-4">
                      <Field label="Worst Loss Amount (Lakhs)" monetary>
                        <NumInput value={form.worst_loss_amount} onChange={v => set('worst_loss_amount', v)} placeholder="e.g. 10" />
                      </Field>
                      <Field label="Context" helper="e.g. 2008 crash, bad stock pick">
                        <input type="text" value={form.loss_context || ''} onChange={e => set('loss_context', e.target.value)} placeholder="What caused the loss?" className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none" />
                      </Field>
                    </div>
                    <Field label="Behavior During Loss">
                      <RadioGroup value={form.loss_behavior} onChange={v => set('loss_behavior', v)}
                        options={[{ value: 'PANIC_SOLD', label: 'Panic Sold' }, { value: 'HELD_THROUGH', label: 'Held Through' }, { value: 'BOUGHT_MORE', label: 'Bought More' }, { value: 'FROZE', label: 'Froze / Did Nothing' }]} />
                    </Field>
                    <Field label="Recovery Experience">
                      <RadioGroup value={form.recovery_experience} onChange={v => set('recovery_experience', v)}
                        options={[{ value: 'RECOVERED_FULLY', label: 'Recovered Fully' }, { value: 'PARTIAL_RECOVERY', label: 'Partial Recovery' }, { value: 'PERMANENT_LOSS', label: 'Permanent Loss' }]} />
                    </Field>
                  </div>
                )}
              </div>
            </Card>
          )}
        </div>

        {/* Section 8: Return Aspirations */}
        <div>
          <SectionHeader index={7} title={SECTIONS[7].title} icon={SECTIONS[7].icon} isOpen={openSection === 7} isComplete={isSectionComplete(7)} onClick={() => handleSectionChange(7)} />
          {openSection === 7 && (
            <Card className="mt-1.5">
              <div className="p-5 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <Field label="Target Annual Return (%)">
                    <div className="relative">
                      <NumInput value={form.target_return} onChange={v => set('target_return', v)} placeholder="e.g. 12" />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-slate-400 font-mono">%</span>
                    </div>
                  </Field>
                  <Field label="Time Horizon (Years)">
                    <NumInput value={form.time_horizon} onChange={v => set('time_horizon', v)} placeholder="e.g. 10" />
                  </Field>
                </div>
                <Field label="Return Purpose" helper="Why do you want this return? What goal does it serve?">
                  <TextArea value={form.return_purpose} onChange={v => set('return_purpose', v)} placeholder="e.g. Build retirement corpus, fund children's education, wealth creation..." />
                </Field>
              </div>
            </Card>
          )}
        </div>

        {/* Section 9: Decision Making */}
        <div>
          <SectionHeader index={8} title={SECTIONS[8].title} icon={SECTIONS[8].icon} isOpen={openSection === 8} isComplete={isSectionComplete(8)} onClick={() => handleSectionChange(8)} />
          {openSection === 8 && (
            <Card className="mt-1.5">
              <div className="p-5 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <Field label="Decision Maker">
                    <Select value={form.decision_maker} onChange={v => set('decision_maker', v)} placeholder="Select..."
                      options={[{ value: 'SELF', label: 'Self' }, { value: 'JOINT_SPOUSE', label: 'Joint with Spouse' }, { value: 'FAMILY_ELDER', label: 'Family Elder' }, { value: 'ADVISOR_DEPENDENT', label: 'Advisor Dependent' }]} />
                  </Field>
                  <Field label="Family Influence Level">
                    <Select value={form.family_influence} onChange={v => set('family_influence', v)} placeholder="Select..."
                      options={[{ value: 'NONE', label: 'None' }, { value: 'LOW', label: 'Low' }, { value: 'MODERATE', label: 'Moderate' }, { value: 'HIGH', label: 'High' }, { value: 'DOMINANT', label: 'Dominant' }]} />
                  </Field>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <Field label="Existing Advisor Relationship?">
                    <RadioGroup value={form.has_advisor ? 'YES' : 'NO'} onChange={v => set('has_advisor', v === 'YES')}
                      options={[{ value: 'YES', label: 'Yes' }, { value: 'NO', label: 'No' }]} />
                  </Field>
                  <Field label="Tax Bracket">
                    <Select value={form.tax_bracket} onChange={v => set('tax_bracket', v)} placeholder="Select..."
                      options={[{ value: '0', label: '0% (No Tax)' }, { value: '5', label: '5%' }, { value: '20', label: '20%' }, { value: '30', label: '30%' }, { value: 'SURCHARGE', label: '30% + Surcharge' }]} />
                  </Field>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Capacity Score & Summary */}
      {completedSections.size >= 5 && (
        <div className="mt-6 space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <CapacityGauge score={capacity?.financial_capacity_score ?? Math.min(Math.round(completedSections.size / SECTIONS.length * 65), 100)} />
              <div className="flex flex-col justify-center gap-4">
                <div className="bg-white rounded-xl border border-slate-200 p-4">
                  <p className="text-xs text-slate-400 mb-0.5">Liquidity Runway</p>
                  <p className={`text-2xl font-bold font-mono ${liquidityRunway >= 12 ? 'text-emerald-600' : liquidityRunway >= 6 ? 'text-amber-600' : 'text-red-600'}`}>{liquidityRunway} <span className="text-sm font-normal text-slate-400">months</span></p>
                  <p className="text-[10px] text-slate-400 mt-0.5">Cash savings / monthly obligations</p>
                </div>
                <div className="bg-white rounded-xl border border-slate-200 p-4">
                  <p className="text-xs text-slate-400 mb-0.5">Obligation Coverage Ratio</p>
                  <p className={`text-2xl font-bold font-mono ${Number(obligationCoverage) >= 80 ? 'text-emerald-600' : Number(obligationCoverage) >= 50 ? 'text-amber-600' : 'text-red-600'}`}>{obligationCoverage}<span className="text-sm font-normal text-slate-400">%</span></p>
                  <p className="text-[10px] text-slate-400 mt-0.5">(Investable - 1yr obligations) / Investable</p>
                </div>
              </div>
              <div className="flex flex-col justify-center gap-3">
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-400">Total Investable</p>
                  <p className="text-lg font-bold font-mono text-teal-600">{formatINR(totalInvestable)}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-400">Net Worth</p>
                  <p className={`text-lg font-bold font-mono ${netWorth >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatINR(netWorth)}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-400">Target Return</p>
                  <p className="text-lg font-bold font-mono text-slate-800">{form.target_return ? `${form.target_return}%` : '—'} <span className="text-xs font-normal text-slate-400">{form.time_horizon ? `over ${form.time_horizon}y` : ''}</span></p>
                </div>
              </div>
            </div>
          </div>

          {/* Continue button */}
          <div className="flex justify-end">
            <button onClick={() => { saveSection(); onComplete(); }}
              className="bg-teal-600 text-white font-medium px-6 py-2.5 rounded-lg hover:bg-teal-700 transition-colors text-sm flex items-center gap-2">
              Continue to Assessment <span>&#8594;</span>
            </button>
          </div>
        </div>
      )}

      {/* Show continue hint if not enough sections completed */}
      {completedSections.size < 5 && (
        <div className="mt-6 bg-slate-50 rounded-xl border border-slate-200 p-5 text-center">
          <p className="text-sm text-slate-500">Complete at least 5 sections to see your Financial Capacity Score</p>
          <p className="text-xs text-slate-400 mt-1">All {SECTIONS.length} sections recommended for accurate scoring</p>
        </div>
      )}
    </div>
  );
}
