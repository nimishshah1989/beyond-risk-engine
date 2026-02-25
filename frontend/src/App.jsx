import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Questionnaire from './pages/Questionnaire'
import Results from './pages/Results'
import Products from './pages/Products'
import QuestionBank from './pages/QuestionBank'
import Upload from './pages/Upload'

const PAGES = [
  { id: 'dashboard', label: 'Dashboard', icon: '⚡' },
  { id: 'assess', label: 'New Assessment', icon: '📋' },
  { id: 'results', label: 'Assessment Results', icon: '📊' },
  { id: 'products', label: 'Product Universe', icon: '🏦' },
  { id: 'upload', label: 'AI Analyzer', icon: '🤖' },
  { id: 'questions', label: 'Question Bank', icon: '🧠' },
];

export default function App() {
  const [page, setPage] = useState('dashboard');
  const [assessmentId, setAssessmentId] = useState(null);
  const [investorTraits, setInvestorTraits] = useState(null);

  const handleAssessmentComplete = (id, traits) => {
    setAssessmentId(id);
    setInvestorTraits(traits);
    setPage('results');
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar pages={PAGES} current={page} onNav={setPage} />
      <main className="flex-1 overflow-auto">
        <div className="sticky top-0 z-20 bg-white border-b border-gray-200 px-8 py-3">
          <h1 className="text-lg font-extrabold text-gray-900 flex items-center gap-2">
            {PAGES.find(p => p.id === page)?.icon} {PAGES.find(p => p.id === page)?.label}
          </h1>
          <p className="text-xs text-gray-400">Beyond · Adaptive Behavioral Risk Engine v2</p>
        </div>
        <div className="p-6">
          {page === 'dashboard' && <Dashboard onNav={setPage} onViewResults={(id, t) => { setAssessmentId(id); setInvestorTraits(t); setPage('results'); }} />}
          {page === 'assess' && <Questionnaire onComplete={handleAssessmentComplete} />}
          {page === 'results' && <Results assessmentId={assessmentId} traits={investorTraits} onMatchProducts={() => setPage('products')} />}
          {page === 'products' && <Products investorTraits={investorTraits} />}
          {page === 'upload' && <Upload />}
          {page === 'questions' && <QuestionBank />}
        </div>
      </main>
    </div>
  );
}
