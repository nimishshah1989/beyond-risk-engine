import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Products from './pages/Products'
import Methodology from './pages/Methodology'
import InvestorJourney from './pages/InvestorJourney'
import InvestorReport from './pages/InvestorReport'

const PAGES = [
  { id: 'dashboard', label: 'Dashboard', icon: 'grid' },
  { id: 'assessment', label: 'Assessment', icon: 'compass' },
  { id: 'report', label: 'Investor Report', icon: 'chart' },
  { id: 'products', label: 'Product Universe', icon: 'building' },
  { id: 'methodology', label: 'Methodology', icon: 'book' },
];

export default function App() {
  const [page, setPage] = useState('dashboard');
  const [investorId, setInvestorId] = useState(null);
  const [investorName, setInvestorName] = useState('');

  const handleSelectInvestor = (id, name, targetPage = 'assessment') => {
    setInvestorId(id);
    setInvestorName(name || '');
    setPage(targetPage);
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar pages={PAGES} current={page} onNav={setPage} />
      <main className="flex-1 overflow-auto">
        <div className="sticky top-0 z-20 bg-white border-b border-slate-200 px-8 py-3">
          <h1 className="text-lg font-extrabold text-slate-900">
            {PAGES.find(p => p.id === page)?.label}
          </h1>
          <p className="text-xs text-slate-400">Beyond — Adaptive Behavioral Risk Engine v3</p>
        </div>
        <div className="p-6">
          {page === 'dashboard' && (
            <Dashboard
              onStartJourney={(id, name) => handleSelectInvestor(id, name, 'assessment')}
              onViewReport={(id, name) => handleSelectInvestor(id, name, 'report')}
            />
          )}
          {page === 'assessment' && (
            <InvestorJourney
              investorId={investorId}
              investorName={investorName}
              onComplete={() => setPage('report')}
              onViewProducts={() => setPage('products')}
            />
          )}
          {page === 'report' && (
            <InvestorReport
              investorId={investorId}
              investorName={investorName}
              onViewProducts={() => setPage('products')}
            />
          )}
          {page === 'products' && <Products />}
          {page === 'methodology' && <Methodology />}
        </div>
      </main>
    </div>
  );
}
