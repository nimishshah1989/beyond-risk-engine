import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Questionnaire from './pages/Questionnaire'
import Results from './pages/Results'
import Strategy from './pages/Strategy'
import Products from './pages/Products'
import QuestionBank from './pages/QuestionBank'
import Methodology from './pages/Methodology'
import FinancialContext from './pages/FinancialContext'

const PAGES = [
  { id: 'dashboard', label: 'Central', icon: '⚡' },
  { id: 'context', label: 'Financial Profile', icon: '💼' },
  { id: 'assess', label: 'New Assessment', icon: '📋' },
  { id: 'results', label: 'Assessment Results', icon: '📊' },
  { id: 'strategy', label: 'Recommended Strategy', icon: '🎯' },
  { id: 'products', label: 'Product Universe', icon: '🏦' },
  { id: 'questions', label: 'Question Bank', icon: '🧠' },
  { id: 'methodology', label: 'Methodology', icon: '📖' },
];

export default function App() {
  const [page, setPage] = useState('dashboard');
  const [assessmentId, setAssessmentId] = useState(null);
  const [investorTraits, setInvestorTraits] = useState(null);
  const [investorName, setInvestorName] = useState('');
  const [investorId, setInvestorId] = useState(null);
  const [fullReport, setFullReport] = useState(null);

  const handleAssessmentComplete = (id, traits) => {
    setAssessmentId(id);
    setInvestorTraits(traits);
    setPage('results');
  };

  const handleOpenContext = (id, name) => {
    setInvestorId(id);
    setInvestorName(name || '');
    setPage('context');
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar pages={PAGES} current={page} onNav={setPage} />
      <main className="flex-1 overflow-auto">
        <div className="sticky top-0 z-20 bg-white border-b border-gray-200 px-8 py-3">
          <h1 className="text-lg font-extrabold text-gray-900 flex items-center gap-2">
            {PAGES.find(p => p.id === page)?.icon} {PAGES.find(p => p.id === page)?.label}
          </h1>
          <p className="text-xs text-gray-400">Beyond · Adaptive Behavioral Risk Engine v3</p>
        </div>
        <div className="p-6">
          {page === 'dashboard' && <Dashboard onNav={setPage} onOpenContext={handleOpenContext} onViewResults={(id, t, name, report) => { setAssessmentId(id); setInvestorTraits(t); setInvestorName(name || ''); setFullReport(report || null); setPage('results'); }} />}
          {page === 'context' && <FinancialContext investorId={investorId} investorName={investorName} onComplete={() => setPage('assess')} />}
          {page === 'assess' && <Questionnaire onComplete={handleAssessmentComplete} />}
          {page === 'results' && <Results assessmentId={assessmentId} traits={investorTraits} onMatchProducts={() => setPage('strategy')} onViewStrategy={() => setPage('strategy')} />}
          {page === 'strategy' && <Strategy investorTraits={investorTraits} investorName={investorName} onViewProducts={() => setPage('products')} />}
          {page === 'products' && <Products />}
          {page === 'questions' && <QuestionBank />}
          {page === 'methodology' && <Methodology />}
        </div>
      </main>
    </div>
  );
}
