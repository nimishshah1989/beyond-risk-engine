import { useState, useCallback } from 'react'
import FinancialContext from './FinancialContext'
import GameAssessment from './GameAssessment'
import DocumentUpload from './DocumentUpload'
import ComprehensiveReport from './ComprehensiveReport'
import { recalculateProfile } from '../services/api'

const STEPS = [
  { id: 'profile', label: 'Investor Profile', description: 'Financial reality & emotional landscape' },
  { id: 'games', label: 'Behavioral Games', description: '4 games measuring real behavior' },
  { id: 'documents', label: 'Document Upload', description: 'CAMS/demat for revealed behavior' },
  { id: 'report', label: 'Assessment Report', description: 'Your comprehensive risk profile' },
];

function StepIndicator({ steps, currentStep, completedSteps }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 mb-5">
      <div className="flex items-center justify-between">
        {steps.map((step, i) => {
          const isCompleted = completedSteps.has(i);
          const isCurrent = i === currentStep;
          const isPast = i < currentStep;
          return (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center text-center flex-1">
                <div className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  isCompleted ? 'bg-emerald-600 text-white' : isCurrent ? 'bg-teal-600 text-white shadow-md' : 'bg-slate-100 text-slate-400'
                }`}>
                  {isCompleted ? '\u2713' : i + 1}
                </div>
                <p className={`text-[11px] font-semibold mt-1.5 ${isCurrent ? 'text-teal-700' : isPast || isCompleted ? 'text-slate-600' : 'text-slate-400'}`}>
                  {step.label}
                </p>
                <p className="text-[10px] text-slate-400 mt-0.5 hidden md:block">{step.description}</p>
              </div>
              {i < steps.length - 1 && (
                <div className={`h-0.5 w-8 mx-1 shrink-0 ${i < currentStep ? 'bg-teal-400' : 'bg-slate-200'}`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function InvestorJourney({ investorId, investorName, onComplete, onViewProducts }) {
  const [step, setStep] = useState(0);
  const [completed, setCompleted] = useState(new Set());
  const [recalculating, setRecalculating] = useState(false);

  const markComplete = useCallback((idx) => {
    setCompleted(prev => new Set([...prev, idx]));
  }, []);

  const goBack = useCallback(() => {
    setStep(prev => Math.max(prev - 1, 0));
  }, []);

  const handleProfileComplete = useCallback(() => {
    markComplete(0);
    setStep(1);
  }, [markComplete]);

  const handleGamesComplete = useCallback(() => {
    markComplete(1);
    setStep(2);
  }, [markComplete]);

  const handleDocumentsComplete = useCallback(async () => {
    markComplete(2);
    setRecalculating(true);
    try {
      await recalculateProfile(investorId);
    } catch (err) {
      console.error('Profile recalculation failed:', err);
    }
    setRecalculating(false);
    setStep(3);
  }, [investorId, markComplete]);

  const handleSkipDocuments = useCallback(async () => {
    setRecalculating(true);
    try {
      await recalculateProfile(investorId);
    } catch (err) {
      console.error('Profile recalculation failed:', err);
    }
    setRecalculating(false);
    setStep(3);
  }, [investorId]);

  if (!investorId) {
    return (
      <div className="max-w-4xl mx-auto mt-10 text-center">
        <p className="text-sm text-slate-500">No investor selected. Go back to the Dashboard and select an investor to begin.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-800">Investor Journey</h2>
            <p className="text-sm text-slate-500">{investorName || 'Investor'} &middot; Step {step + 1} of {STEPS.length}</p>
          </div>
          {step > 0 && step < 3 && (
            <button onClick={goBack} className="text-xs text-slate-500 hover:text-slate-700 transition-colors flex items-center gap-1">
              &larr; Back
            </button>
          )}
        </div>
      </div>

      <StepIndicator steps={STEPS} currentStep={step} completedSteps={completed} />

      {recalculating && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="text-center py-12">
            <div className="w-10 h-10 border-3 border-teal-200 border-t-teal-600 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm font-semibold text-slate-700">Generating your comprehensive assessment...</p>
            <p className="text-xs text-slate-400 mt-1">Fusing all data sources with Bayesian fusion</p>
          </div>
        </div>
      )}

      {!recalculating && (
        <>
          {step === 0 && (
            <FinancialContext investorId={investorId} investorName={investorName} onComplete={handleProfileComplete} />
          )}

          {step === 1 && (
            <GameAssessment investorId={investorId} investorName={investorName} onComplete={handleGamesComplete} />
          )}

          {step === 2 && (
            <div>
              <DocumentUpload investorId={investorId} investorName={investorName} onComplete={handleDocumentsComplete} embedded />
              <div className="mt-4 flex items-center justify-center gap-4">
                <button onClick={handleSkipDocuments}
                  className="text-xs font-bold px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors">
                  Skip &rarr; Generate Report Without Documents
                </button>
              </div>
            </div>
          )}

          {step === 3 && (
            <ComprehensiveReport investorId={investorId} investorName={investorName} onViewProducts={onViewProducts || (() => {})} />
          )}
        </>
      )}
    </div>
  );
}
