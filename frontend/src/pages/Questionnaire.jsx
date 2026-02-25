import { useState } from 'react'
import { Card, Badge, Btn, Bar } from '../components/UI'
import { createInvestor, startAssessment, submitResponse } from '../services/api'

export default function Questionnaire({ onComplete }) {
  const [phase, setPhase] = useState('intake'); // intake | assessing | completing
  const [investor, setInvestor] = useState({ name: '', code: '', age: '', aum: '', segment: 'HNI' });
  const [assessmentId, setAssessmentId] = useState(null);
  const [currentQ, setCurrentQ] = useState(null);
  const [qNum, setQNum] = useState(0);
  const [scores, setScores] = useState(null);
  const [confidence, setConfidence] = useState(null);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [startTime, setStartTime] = useState(null);

  const handleStart = async () => {
    if (!investor.name || !investor.code) { setError('Name and Code are required'); return; }
    setLoading(true); setError(null);
    try {
      const inv = await createInvestor(investor);
      const res = await startAssessment(inv.id);
      setAssessmentId(res.assessment_id);
      setCurrentQ(res.question);
      setQNum(1);
      setPhase('assessing');
      setStartTime(Date.now());
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  const handleAnswer = async (optionIndex) => {
    setSelected(optionIndex);
    setLoading(true);
    const elapsed = Date.now() - startTime;
    try {
      const res = await submitResponse({
        assessment_id: assessmentId,
        question_code: currentQ.code,
        option_index: optionIndex,
        response_time_ms: elapsed
      });
      if (res.is_complete) {
        onComplete(res.assessment_id, res.trait_scores);
      } else {
        setCurrentQ(res.question);
        setQNum(res.question_number);
        setScores(res.current_scores);
        setConfidence(res.current_confidence);
        setSelected(null);
        setStartTime(Date.now());
      }
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  const tierColors = { anchor: '#1746a2', diagnostic: '#0891b2', calibration: '#d97706' };

  if (phase === 'intake') {
    return (
      <div className="max-w-xl mx-auto mt-8">
        <Card>
          <div className="text-center mb-6">
            <div className="text-3xl mb-2">📋</div>
            <h2 className="text-lg font-extrabold">New Behavioral Risk Assessment</h2>
            <p className="text-xs text-gray-400 mt-1">Adaptive 12-25 questions · IRT-based scoring · 10 behavioral traits</p>
          </div>
          {error && <div className="bg-red-50 text-red-700 text-xs p-3 rounded-lg mb-4">{error}</div>}
          <div className="space-y-3">
            <div>
              <label className="text-[11px] text-gray-500 font-semibold block mb-1">Investor Name *</label>
              <input value={investor.name} onChange={e => setInvestor({...investor, name: e.target.value})}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
                placeholder="e.g. Ushaben Raojibhai Patel" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-gray-500 font-semibold block mb-1">Client Code *</label>
                <input value={investor.code} onChange={e => setInvestor({...investor, code: e.target.value})}
                  className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
                  placeholder="e.g. U00269" />
              </div>
              <div>
                <label className="text-[11px] text-gray-500 font-semibold block mb-1">Age</label>
                <input value={investor.age} onChange={e => setInvestor({...investor, age: e.target.value})}
                  className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
                  placeholder="e.g. 67" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-gray-500 font-semibold block mb-1">AUM (Cr)</label>
                <input value={investor.aum} onChange={e => setInvestor({...investor, aum: e.target.value})} type="number"
                  className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
                  placeholder="e.g. 173.41" />
              </div>
              <div>
                <label className="text-[11px] text-gray-500 font-semibold block mb-1">Segment</label>
                <select value={investor.segment} onChange={e => setInvestor({...investor, segment: e.target.value})}
                  className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200">
                  <option>Retail</option><option>HNI</option><option>UHNI</option><option>Corporate</option>
                </select>
              </div>
            </div>
          </div>
          <div className="mt-6 flex justify-end">
            <Btn primary onClick={handleStart} disabled={loading}>{loading ? 'Starting...' : 'Begin Assessment →'}</Btn>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto mt-4">
      {/* Progress */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-sm font-bold text-gray-900">Question {qNum}</span>
          <Badge color={tierColors[currentQ?.tier] || '#666'}>{currentQ?.tier}</Badge>
        </div>
        <span className="text-xs text-gray-400">~{Math.max(25 - qNum, 0)} remaining</span>
      </div>
      <Bar value={qNum} max={25} color="#1746a2" h={4} />

      {error && <div className="bg-red-50 text-red-700 text-xs p-3 rounded-lg mt-3">{error}</div>}

      {/* Question */}
      <Card className="mt-5">
        {currentQ?.rationale && (
          <div className="bg-blue-50 text-blue-800 text-[11px] px-3 py-2 rounded-lg mb-4">
            <span className="font-bold">Why this question: </span>{currentQ.rationale}
          </div>
        )}
        <h2 className="text-base font-bold text-gray-900 leading-relaxed mb-5">{currentQ?.text}</h2>
        <div className="space-y-2.5">
          {currentQ?.options?.map((opt, i) => (
            <button key={i} onClick={() => !loading && handleAnswer(i)} disabled={loading}
              className={`w-full text-left p-4 rounded-xl border-2 transition-all text-sm ${
                selected === i ? 'border-blue-700 bg-blue-50' : 'border-gray-100 hover:border-blue-200 hover:bg-gray-50'
              } ${loading ? 'opacity-50' : 'cursor-pointer'}`}>
              <div className="flex items-start gap-3">
                <span className={`w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 ${
                  selected === i ? 'border-blue-700 bg-blue-700 text-white' : 'border-gray-300 text-gray-400'}`}>
                  {String.fromCharCode(65 + i)}
                </span>
                <span className="leading-relaxed">{opt.text}</span>
              </div>
            </button>
          ))}
        </div>
      </Card>

      {/* Live confidence */}
      {confidence && (
        <Card className="mt-4">
          <h4 className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-3">Live Trait Confidence</h4>
          <div className="grid grid-cols-5 gap-2">
            {Object.entries(confidence).map(([k, v]) => (
              <div key={k} className="text-center">
                <div className="text-[10px] text-gray-400 truncate">{k.split('_').map(w=>w[0].toUpperCase()).join('')}</div>
                <div className={`text-sm font-bold ${v >= 70 ? 'text-green-600' : v >= 40 ? 'text-amber-600' : 'text-red-500'}`}>{v}%</div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
