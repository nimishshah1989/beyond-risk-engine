import { useState, useEffect } from 'react';

const fmtINR = (n) => '\u20B9' + n.toLocaleString('en-IN');
const GAME_LABELS = ['Risk Tolerance', 'Loss Aversion', 'Time Preference', 'Herding Bias'];
const GAME_ICONS = ['\uD83C\uDFB2', '\uD83D\uDEE1\uFE0F', '\u23F3', '\uD83D\uDC65'];

/* ── GameCard ─────────────────────────────────────────────────────── */
export function GameCard({ children, className = '' }) {
  return (
    <div className={`bg-white rounded-xl border border-slate-200 p-6 ${className}`}>
      {children}
    </div>
  );
}

/* ── GameProgress ─────────────────────────────────────────────────── */
export function GameProgress({ currentGame, totalGames, currentTrial, totalTrials }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 px-5 py-3 mb-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-base">{GAME_ICONS[currentGame]}</span>
          <span className="text-sm font-semibold text-slate-800">
            Game {currentGame + 1}: {GAME_LABELS[currentGame]}
          </span>
        </div>
        <span className="text-xs font-medium text-slate-400">Trial {currentTrial} of {totalTrials}</span>
      </div>
      <div className="flex gap-1.5 mb-2">
        {Array.from({ length: totalGames }).map((_, i) => (
          <div key={i} className="flex-1 h-1.5 rounded-full overflow-hidden bg-slate-100">
            <div className="h-full rounded-full transition-all duration-300" style={{
              width: i < currentGame ? '100%' : i === currentGame ? `${(currentTrial / totalTrials) * 100}%` : '0%',
              background: i <= currentGame ? '#0d9488' : '#e2e8f0',
            }} />
          </div>
        ))}
      </div>
      <div className="flex items-center gap-1">
        {Array.from({ length: totalTrials }).map((_, i) => (
          <div key={i} className={`w-2 h-2 rounded-full transition-all duration-200 ${
            i < currentTrial ? 'bg-teal-600' : 'bg-slate-200'}`} />
        ))}
      </div>
    </div>
  );
}

/* ── ChoiceButton (internal) ──────────────────────────────────────── */
const BTN_STYLES = {
  teal: ['border-teal-200 hover:border-teal-500 hover:bg-teal-50 active:bg-teal-100', 'bg-teal-600 text-white'],
  blue: ['border-blue-200 hover:border-blue-500 hover:bg-blue-50 active:bg-blue-100', 'bg-blue-600 text-white'],
};

function ChoiceButton({ label, title, description, color = 'teal', onClick, disabled }) {
  const [border, badge] = BTN_STYLES[color] || BTN_STYLES.teal;
  return (
    <button onClick={onClick} disabled={disabled}
      className={`flex-1 p-5 rounded-xl border-2 transition-all duration-150 text-left ${border} ${
        disabled ? 'opacity-50 pointer-events-none' : 'cursor-pointer'}`}>
      <span className={`inline-block text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${badge} mb-2`}>
        {label}
      </span>
      <p className="text-lg font-bold font-mono text-slate-800 leading-snug">{title}</p>
      {description && <p className="text-xs text-slate-500 mt-1.5">{description}</p>}
    </button>
  );
}

/* ── RiskToleranceGame ────────────────────────────────────────────── */
export function RiskToleranceGame({ stimulus, onRespond, disabled }) {
  const { guaranteed = 50000, gamble_amount = 120000, probability = 50 } = stimulus || {};
  return (
    <GameCard>
      <div className="text-center mb-6">
        <p className="text-sm text-slate-500 mb-1">Choose your preferred option</p>
        <p className="text-base font-semibold text-slate-800">A guaranteed payout or a gamble with higher potential?</p>
      </div>
      <div className="flex gap-4">
        <ChoiceButton label="Option A - Safe" title={fmtINR(guaranteed)}
          description="Guaranteed amount, zero risk" color="teal"
          onClick={() => onRespond({ choice: 'safe' })} disabled={disabled} />
        <ChoiceButton label="Option B - Gamble" title={fmtINR(gamble_amount)}
          description={`${probability}% chance of winning, ${100 - probability}% chance of nothing`}
          color="blue" onClick={() => onRespond({ choice: 'gamble' })} disabled={disabled} />
      </div>
    </GameCard>
  );
}

/* ── LossAversionGame ─────────────────────────────────────────────── */
export function LossAversionGame({ stimulus, onRespond, disabled }) {
  const { gain = 20000, loss = 10000 } = stimulus || {};
  return (
    <GameCard>
      <div className="text-center mb-6">
        <p className="text-sm text-slate-500 mb-1">Would you take this 50/50 gamble?</p>
        <div className="flex items-center justify-center gap-6 mt-3">
          <div className="text-center">
            <p className="text-xs text-emerald-600 font-semibold uppercase tracking-wider">Win</p>
            <p className="text-2xl font-bold font-mono text-emerald-600">{fmtINR(gain)}</p>
          </div>
          <div className="text-slate-300 text-2xl font-light">or</div>
          <div className="text-center">
            <p className="text-xs text-red-600 font-semibold uppercase tracking-wider">Lose</p>
            <p className="text-2xl font-bold font-mono text-red-600">{fmtINR(loss)}</p>
          </div>
        </div>
        <p className="text-xs text-slate-400 mt-2">Equal 50% probability for each outcome</p>
      </div>
      <div className="flex gap-4">
        <ChoiceButton label="Accept Gamble" title="Take the risk"
          description={`Win ${fmtINR(gain)} or Lose ${fmtINR(loss)}`} color="blue"
          onClick={() => onRespond({ choice: 'accept' })} disabled={disabled} />
        <ChoiceButton label="Reject Gamble" title="Walk away"
          description="Keep what you have, no risk" color="teal"
          onClick={() => onRespond({ choice: 'reject' })} disabled={disabled} />
      </div>
    </GameCard>
  );
}

/* ── TimePreferenceGame ───────────────────────────────────────────── */
export function TimePreferenceGame({ stimulus, onRespond, disabled }) {
  const { immediate = 50000, delayed = 100000, delay_months = 12 } = stimulus || {};
  const delayLabel = delay_months >= 12
    ? `${delay_months / 12} year${delay_months > 12 ? 's' : ''}`
    : `${delay_months} month${delay_months > 1 ? 's' : ''}`;
  return (
    <GameCard>
      <div className="text-center mb-6">
        <p className="text-sm text-slate-500 mb-1">When would you like your money?</p>
        <p className="text-base font-semibold text-slate-800">A smaller amount now, or a larger amount later?</p>
      </div>
      <div className="flex gap-4">
        <ChoiceButton label="Now" title={fmtINR(immediate)}
          description="Receive this amount today" color="teal"
          onClick={() => onRespond({ choice: 'now' })} disabled={disabled} />
        <ChoiceButton label={`In ${delayLabel}`} title={fmtINR(delayed)}
          description={`Wait ${delayLabel} to receive this amount`} color="blue"
          onClick={() => onRespond({ choice: 'later' })} disabled={disabled} />
      </div>
    </GameCard>
  );
}

/* ── HerdingGame ──────────────────────────────────────────────────── */
export function HerdingGame({ stimulus, onRespond, disabled }) {
  const { option_a = 'Fund A', option_b = 'Fund B', social_signal = null, scenario = '' } = stimulus || {};
  return (
    <GameCard>
      <div className="text-center mb-5">
        <p className="text-sm text-slate-500 mb-2">Investment Scenario</p>
        <p className="text-base font-semibold text-slate-800 leading-relaxed max-w-lg mx-auto">{scenario}</p>
        {social_signal && (
          <div className="mt-3 inline-flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2">
            <span className="text-base">{'\uD83D\uDCE2'}</span>
            <span className="text-sm text-amber-800 font-medium">{social_signal}</span>
          </div>
        )}
      </div>
      <div className="flex gap-4">
        <ChoiceButton label="Option A" title={option_a} color="teal"
          onClick={() => onRespond({ choice: 'A' })} disabled={disabled} />
        <ChoiceButton label="Option B" title={option_b} color="blue"
          onClick={() => onRespond({ choice: 'B' })} disabled={disabled} />
      </div>
    </GameCard>
  );
}

/* ── GameTransition ───────────────────────────────────────────────── */
const GAME_DESCS = [
  'We will test how you evaluate risk versus safety.',
  'We will measure your sensitivity to potential losses.',
  'We will explore your patience and time preferences.',
  'We will see how social information affects your decisions.',
];

export function GameTransition({ nextGameIndex, onContinue }) {
  return (
    <div className="max-w-md mx-auto text-center">
      <GameCard className="py-10">
        <div className="text-4xl mb-4">{GAME_ICONS[nextGameIndex]}</div>
        <p className="text-xs font-semibold text-teal-600 uppercase tracking-wider mb-1">
          Up Next - Game {nextGameIndex + 1} of 4
        </p>
        <h2 className="text-xl font-bold text-slate-800 mb-2">{GAME_LABELS[nextGameIndex]}</h2>
        <p className="text-sm text-slate-500 mb-6">{GAME_DESCS[nextGameIndex]}</p>
        <button onClick={onContinue}
          className="bg-teal-600 text-white font-semibold px-8 py-3 rounded-lg hover:bg-teal-700 transition-colors text-sm">
          Start Game {nextGameIndex + 1} {'\u2192'}
        </button>
      </GameCard>
    </div>
  );
}
