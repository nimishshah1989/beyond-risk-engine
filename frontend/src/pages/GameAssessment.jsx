import { useState, useRef, useCallback } from 'react';
import {
  GameCard, GameProgress, GameTransition,
  RiskToleranceGame, LossAversionGame, TimePreferenceGame, HerdingGame,
} from '../components/games/GameComponents';

const BASE = import.meta.env.VITE_API_URL || '';
const GAME_ORDER = ['risk_tolerance', 'loss_aversion', 'time_preference', 'herding'];
const TRIAL_COUNTS = { risk_tolerance: 5, loss_aversion: 6, time_preference: 5, herding: 6 };
const GAME_META = [
  { key: 'risk_tolerance', label: 'Risk Tolerance', icon: '\uD83C\uDFB2', color: '#0d9488' },
  { key: 'loss_aversion', label: 'Loss Aversion', icon: '\uD83D\uDEE1\uFE0F', color: '#dc2626' },
  { key: 'time_preference', label: 'Time Preference', icon: '\u23F3', color: '#2563eb' },
  { key: 'herding', label: 'Herding Bias', icon: '\uD83D\uDC65', color: '#d97706' },
];

async function api(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

/* ── Score Summary ───────────────────────────────────────────────── */
function ScoreSummary({ scores, onViewProfile }) {
  return (
    <div className="max-w-lg mx-auto text-center">
      <GameCard className="py-8">
        <div className="text-4xl mb-3">{'\u2705'}</div>
        <h2 className="text-xl font-bold text-slate-800 mb-1">Assessment Complete</h2>
        <p className="text-sm text-slate-500 mb-6">Your behavioral profile has been computed</p>
        <div className="grid grid-cols-2 gap-3 mb-6">
          {GAME_META.map(({ key, label, icon, color }) => (
            <div key={key} className="bg-slate-50 rounded-xl border border-slate-200 p-4 text-center">
              <span className="text-2xl">{icon}</span>
              <p className="text-xs text-slate-500 mt-1">{label}</p>
              <p className="text-2xl font-bold font-mono mt-1" style={{ color }}>
                {scores?.[key] != null ? scores[key] : '--'}
                <span className="text-xs text-slate-400 font-normal">/100</span>
              </p>
            </div>
          ))}
        </div>
        <button onClick={onViewProfile}
          className="bg-teal-600 text-white font-semibold px-8 py-3 rounded-lg hover:bg-teal-700 transition-colors text-sm">
          View Full Profile {'\u2192'}
        </button>
      </GameCard>
    </div>
  );
}

/* ── Main GameAssessment Page ─────────────────────────────────────── */
export default function GameAssessment({ investorId, investorName, onComplete }) {
  const [phase, setPhase] = useState('welcome');
  const [sessionId, setSessionId] = useState(null);
  const [gameIndex, setGameIndex] = useState(0);
  const [trialNum, setTrialNum] = useState(1);
  const [stimulus, setStimulus] = useState(null);
  const [scores, setScores] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [locked, setLocked] = useState(false);
  const trialStart = useRef(0);

  const currentGame = GAME_ORDER[gameIndex];
  const totalTrials = TRIAL_COUNTS[currentGame] || 5;

  const handleStart = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const data = await api('/api/games/start', { investor_id: investorId });
      setSessionId(data.session_id);
      setStimulus(data.first_trials?.[GAME_ORDER[0]] || {});
      setGameIndex(0); setTrialNum(1);
      trialStart.current = performance.now();
      setPhase('playing');
    } catch (err) { setError(err.message); }
    setLoading(false);
  }, [investorId]);

  const handleRespond = useCallback(async (response) => {
    if (locked) return;
    setLocked(true);
    const responseTimeMs = Math.round(performance.now() - trialStart.current);
    try {
      const data = await api('/api/games/trial', {
        session_id: sessionId, game_type: currentGame, trial_number: trialNum,
        stimulus, response: { ...response, response_time_ms: responseTimeMs },
        response_time_ms: responseTimeMs,
      });
      // Brief visual feedback pause
      await new Promise((r) => setTimeout(r, 300));
      if (data.complete) {
        const nextIdx = gameIndex + 1;
        if (nextIdx < GAME_ORDER.length) {
          setGameIndex(nextIdx); setTrialNum(1);
          setStimulus(data.next_stimulus || null);
          setPhase('transition');
        } else {
          setPhase('processing');
          const result = await api('/api/games/complete', { session_id: sessionId });
          setScores(result); setPhase('results');
        }
      } else {
        setStimulus(data.next_stimulus || {});
        setTrialNum((n) => n + 1);
        trialStart.current = performance.now();
      }
    } catch (err) { setError(err.message); }
    setLocked(false);
  }, [locked, sessionId, currentGame, trialNum, stimulus, gameIndex]);

  const handleContinue = useCallback(() => {
    trialStart.current = performance.now();
    setPhase('playing');
  }, []);

  const renderGame = () => {
    const props = { stimulus, onRespond: handleRespond, disabled: locked };
    switch (currentGame) {
      case 'risk_tolerance':  return <RiskToleranceGame {...props} />;
      case 'loss_aversion':   return <LossAversionGame {...props} />;
      case 'time_preference': return <TimePreferenceGame {...props} />;
      case 'herding':         return <HerdingGame {...props} />;
      default:                return null;
    }
  };

  const errorBar = error && (
    <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-xl mb-4 flex items-center justify-between">
      <span>{error}</span>
      <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 ml-2">{'\u2715'}</button>
    </div>
  );

  /* ── Welcome ───────────────────────────────────────────────────── */
  if (phase === 'welcome') {
    return (
      <div className="max-w-md mx-auto mt-8">
        {errorBar}
        <GameCard className="text-center py-10">
          <div className="text-5xl mb-4">{'\uD83C\uDFAE'}</div>
          <h2 className="text-xl font-bold text-slate-800 mb-1">Behavioral Game Assessment</h2>
          {investorName && <p className="text-sm text-teal-600 font-medium mb-3">for {investorName}</p>}
          <p className="text-sm text-slate-500 mb-6 max-w-xs mx-auto">
            4 interactive games measuring your investment behavior. Takes about 2.5 minutes.
          </p>
          <div className="grid grid-cols-2 gap-3 text-left mb-8 max-w-xs mx-auto">
            {GAME_META.map(({ label, icon }, i) => (
              <div key={label} className="flex items-center gap-2 bg-slate-50 rounded-lg border border-slate-200 px-3 py-2">
                <span className="text-lg">{icon}</span>
                <div>
                  <p className="text-xs font-semibold text-slate-700">{label}</p>
                  <p className="text-[10px] text-slate-400">{TRIAL_COUNTS[GAME_ORDER[i]]} trials</p>
                </div>
              </div>
            ))}
          </div>
          <button onClick={handleStart} disabled={loading}
            className={`bg-teal-600 text-white font-semibold px-10 py-3 rounded-lg hover:bg-teal-700 transition-colors text-sm ${
              loading ? 'opacity-60 pointer-events-none' : ''}`}>
            {loading ? 'Preparing Games...' : 'Start Assessment \u2192'}
          </button>
        </GameCard>
      </div>
    );
  }

  /* ── Transition ────────────────────────────────────────────────── */
  if (phase === 'transition') {
    return (
      <div className="max-w-md mx-auto mt-8">
        {errorBar}
        <GameTransition nextGameIndex={gameIndex} onContinue={handleContinue} />
      </div>
    );
  }

  /* ── Processing ────────────────────────────────────────────────── */
  if (phase === 'processing') {
    return (
      <div className="max-w-md mx-auto mt-16 text-center">
        <GameCard className="py-12">
          <div className="flex justify-center gap-2 mb-6">
            {[0, 1, 2].map((i) => (
              <div key={i} className="w-3 h-3 rounded-full bg-teal-600 animate-bounce"
                style={{ animationDelay: `${i * 150}ms` }} />
            ))}
          </div>
          <h2 className="text-lg font-bold text-slate-800 mb-2">Computing Your Profile</h2>
          <p className="text-sm text-slate-500">Analyzing response patterns and reaction times...</p>
        </GameCard>
      </div>
    );
  }

  /* ── Results ───────────────────────────────────────────────────── */
  if (phase === 'results') {
    return <div className="mt-8">{errorBar}<ScoreSummary scores={scores} onViewProfile={() => onComplete?.(scores)} /></div>;
  }

  /* ── Playing ───────────────────────────────────────────────────── */
  return (
    <div className="max-w-xl mx-auto mt-4">
      {errorBar}
      <GameProgress currentGame={gameIndex} totalGames={GAME_ORDER.length}
        currentTrial={trialNum} totalTrials={totalTrials} />
      <div className="transition-opacity duration-200" style={{ opacity: locked ? 0.6 : 1 }}>
        {renderGame()}
      </div>
    </div>
  );
}
