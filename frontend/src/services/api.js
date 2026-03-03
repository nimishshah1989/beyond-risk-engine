const BASE = import.meta.env.VITE_API_URL || '';

async function request(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

// Questions
export const getQuestions = (tier) => request(`/api/questions/${tier ? `?tier=${tier}` : ''}`);
export const getQuestionStats = () => request('/api/questions/stats/summary');
export const createQuestion = (data) => request('/api/questions/', { method: 'POST', body: JSON.stringify(data) });
export const updateQuestion = (code, data) => request(`/api/questions/${code}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteQuestion = (code) => request(`/api/questions/${code}`, { method: 'DELETE' });

// Investors
export const getInvestors = () => request('/api/investors');
export const createInvestor = (data) => request('/api/investors', { method: 'POST', body: JSON.stringify(data) });
export const getInvestor = (id) => request(`/api/investors/${id}`);

// Assessments
export const startAssessment = (investorId) => request(`/api/assessments/start?investor_id=${investorId}`, { method: 'POST' });
export const submitResponse = (data) => request('/api/assessments/respond', { method: 'POST', body: JSON.stringify(data) });
export const getAssessment = (id) => request(`/api/assessments/${id}`);
export const getFullReport = (id) => request(`/api/assessments/${id}/full-report`);

// Products
export const getProducts = (category) => request(`/api/products/${category ? `?category=${category}` : ''}`);
export const getCategories = () => request('/api/products/categories');
export const matchProducts = (traits) => request('/api/products/match', { method: 'POST', body: JSON.stringify(traits) });

// Financial Context
export const getFinancialContext = (investorId) => request(`/api/context/${investorId}`);
export const saveFinancialContext = (investorId, data) => request(`/api/context/${investorId}`, { method: 'POST', body: JSON.stringify(data) });
export const getCapacityScore = (investorId) => request(`/api/context/${investorId}/capacity`);

// Games
export const startGameSession = (investorId) => request('/api/games/start', { method: 'POST', body: JSON.stringify({ investor_id: investorId }) });
export const submitGameTrial = (data) => request('/api/games/trial', { method: 'POST', body: JSON.stringify(data) });
export const completeGameSession = (sessionId) => request('/api/games/complete', { method: 'POST', body: JSON.stringify({ session_id: sessionId }) });
export const getGameSession = (sessionId) => request(`/api/games/session/${sessionId}`);

// Documents
export const getUploadStatus = (uploadId) => request(`/api/documents/status/${uploadId}`);
export const getInvestorUploads = (investorId) => request(`/api/documents/investor/${investorId}`);

// Profiles
export const getProfile = (investorId) => request(`/api/profiles/${investorId}`);
export const getProfileHistory = (investorId) => request(`/api/profiles/${investorId}/history`);
export const recalculateProfile = (investorId) => request(`/api/profiles/${investorId}/recalculate`, { method: 'POST' });

// Market
export const getMarketRegime = () => request('/api/market/regime');
export const checkAspiration = (data) => request('/api/market/aspiration-check', { method: 'POST', body: JSON.stringify(data) });
