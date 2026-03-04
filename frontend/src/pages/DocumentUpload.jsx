import { useState, useEffect, useCallback, useRef } from 'react';
import { Card, Badge, Btn } from '../components/UI';

const BASE = import.meta.env.VITE_API_URL || '';

const STEPS = ['Upload', 'Parsing', 'Enriching', 'Scoring', 'Complete'];
const STATUS_TO_STEP = { pending: 1, parsing: 1, parsed: 2, scoring: 3, scored: 4, complete: 4 };
const FILE_TYPES = { pdf: 'CAS / Demat PDF', csv: 'Transactions CSV', xlsx: 'Holdings Excel' };

function detectFileType(name) {
  const ext = name.split('.').pop().toLowerCase();
  return FILE_TYPES[ext] ? ext : null;
}

export default function DocumentUpload({ investorId, investorName, onComplete, embedded = false }) {
  const [file, setFile] = useState(null);
  const [password, setPassword] = useState('');
  const [fileType, setFileType] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadId, setUploadId] = useState(null);
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const pollRef = useRef(null);

  // Fetch previous uploads for this investor
  const fetchHistory = useCallback(async () => {
    try {
      const res = await fetch(`${BASE}/api/documents/investor/${investorId}`);
      if (res.ok) setHistory(await res.json());
    } catch { /* silent — history is non-critical */ }
  }, [investorId]);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  // Poll upload status every 2s once we have an uploadId
  useEffect(() => {
    if (!uploadId) return;
    const poll = async () => {
      try {
        const res = await fetch(`${BASE}/api/documents/status/${uploadId}`);
        if (!res.ok) throw new Error('Status check failed');
        const data = await res.json();
        setStatus(data.status);
        if (data.status === 'scored' || data.status === 'complete') {
          setResult(data);
          clearInterval(pollRef.current);
          fetchHistory();
        }
        if (data.status === 'failed') {
          setError(data.error || 'Processing failed');
          clearInterval(pollRef.current);
        }
      } catch (err) {
        setError(err.message);
        clearInterval(pollRef.current);
      }
    };
    pollRef.current = setInterval(poll, 2000);
    poll(); // immediate first check
    return () => clearInterval(pollRef.current);
  }, [uploadId, fetchHistory]);

  const handleFileSelect = (selected) => {
    setFile(selected);
    setFileType(detectFileType(selected.name));
    setError(null);
    setResult(null);
    setStatus(null);
    setUploadId(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFileSelect(dropped);
  };

  const handleUpload = async () => {
    if (!file) return;
    if (!investorId) { setError('No investor selected. Go to Central and select an investor first.'); return; }
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('investor_id', String(investorId));
      if (password) formData.append('password', password);
      const res = await fetch(`${BASE}/api/documents/upload`, { method: 'POST', body: formData });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        const detail = err.detail;
        const msg = typeof detail === 'string' ? detail
          : Array.isArray(detail) ? detail.map(d => d.msg || d.message || JSON.stringify(d)).join('; ')
          : 'Upload failed';
        throw new Error(msg);
      }
      const data = await res.json();
      setUploadId(data.upload_id);
      setStatus('pending');
    } catch (err) {
      setError(err.message);
    }
    setUploading(false);
  };

  const currentStep = status ? (STATUS_TO_STEP[status] ?? 0) : 0;

  return (
    <div className="bg-slate-50 min-h-full p-6 space-y-5">
      {/* Header — hidden when embedded in wizard */}
      {!embedded && (
        <div>
          <h2 className="text-lg font-extrabold text-slate-900">Upload CAS / Demat Statement</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            For <span className="font-bold text-teal-700">{investorName}</span> — upload portfolio documents to parse holdings and transactions
          </p>
        </div>
      )}

      {/* Drop zone + password */}
      <Card>
        <label
          className="block cursor-pointer"
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <div className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
            dragging ? 'border-teal-500 bg-teal-50' : file ? 'border-teal-300 bg-teal-50/40' : 'border-slate-300 hover:border-teal-400'
          }`}>
            {file ? (
              <div>
                <div className="text-2xl mb-1">📄</div>
                <div className="text-sm font-bold text-slate-800">{file.name}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">{(file.size / 1024).toFixed(0)} KB</div>
                {fileType && <Badge color="#0d9488">{FILE_TYPES[fileType]}</Badge>}
              </div>
            ) : (
              <div>
                <div className="text-3xl mb-2">📁</div>
                <div className="text-sm font-bold text-slate-600">Drop a file here or click to browse</div>
                <div className="text-[11px] text-slate-400 mt-1">Accepts .pdf, .csv, .xlsx</div>
              </div>
            )}
          </div>
          <input type="file" accept=".pdf,.csv,.xlsx" className="hidden" onChange={(e) => e.target.files[0] && handleFileSelect(e.target.files[0])} />
        </label>

        {/* Password field for PDF */}
        {file && fileType === 'pdf' && (
          <div className="mt-4">
            <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">PDF Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="PAN + DOB as DDMMYYYY (e.g. ABCDE1234F01011990)"
              className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            />
            <p className="text-[10px] text-slate-400 mt-1">Leave blank if the PDF is not password-protected</p>
          </div>
        )}

        <div className="mt-4 flex justify-end">
          <Btn primary onClick={handleUpload} disabled={!file || uploading}>
            {uploading ? 'Uploading...' : 'Upload & Parse'}
          </Btn>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <div className="bg-red-50 text-red-700 text-xs p-4 rounded-xl border border-red-200">{error}</div>
      )}

      {/* Progress stepper */}
      {status && !error && (
        <Card>
          <div className="flex items-center justify-between">
            {STEPS.map((label, i) => {
              const done = i < currentStep;
              const active = i === currentStep;
              return (
                <div key={label} className="flex-1 flex flex-col items-center relative">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-colors ${
                    done ? 'bg-teal-600 border-teal-600 text-white'
                      : active ? 'bg-amber-100 border-amber-400 text-amber-700 animate-pulse'
                        : 'bg-slate-100 border-slate-300 text-slate-400'
                  }`}>
                    {done ? '✓' : i + 1}
                  </div>
                  <span className={`text-[10px] mt-1 font-bold ${done ? 'text-teal-700' : active ? 'text-amber-600' : 'text-slate-400'}`}>
                    {label}
                  </span>
                  {i < STEPS.length - 1 && (
                    <div className={`absolute top-4 left-[60%] w-[80%] h-0.5 ${done ? 'bg-teal-400' : 'bg-slate-200'}`} />
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Completion result */}
      {result && (
        <Card className="border-teal-200 bg-teal-50/30">
          <h3 className="text-sm font-bold text-teal-800 mb-3">Parsing Complete</h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-white p-3 rounded-lg border border-slate-200 text-center">
              <div className="text-lg font-extrabold text-slate-900 font-mono tabular-nums">{result.total_folios ?? '—'}</div>
              <div className="text-[10px] text-slate-500 font-bold uppercase">Folios</div>
            </div>
            <div className="bg-white p-3 rounded-lg border border-slate-200 text-center">
              <div className="text-lg font-extrabold text-slate-900 font-mono tabular-nums">{result.total_transactions ?? '—'}</div>
              <div className="text-[10px] text-slate-500 font-bold uppercase">Transactions</div>
            </div>
            <div className="bg-white p-3 rounded-lg border border-slate-200 text-center">
              <div className="text-xs font-bold text-slate-900 font-mono tabular-nums">{result.statement_from || '—'}</div>
              <div className="text-[10px] text-slate-500 font-bold uppercase">From</div>
            </div>
            <div className="bg-white p-3 rounded-lg border border-slate-200 text-center">
              <div className="text-xs font-bold text-slate-900 font-mono tabular-nums">{result.statement_to || '—'}</div>
              <div className="text-[10px] text-slate-500 font-bold uppercase">To</div>
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <Btn primary onClick={() => onComplete && onComplete(result)}>View Profile</Btn>
          </div>
        </Card>
      )}

      {/* Previous uploads */}
      {history.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-slate-800 mb-3">Previous Uploads</h3>
          <div className="space-y-2">
            {history.map((item) => (
              <div key={item.id || item.upload_id} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm">📄</span>
                  <span className="text-xs font-bold text-slate-700">{item.filename}</span>
                  <Badge color={item.status === 'scored' || item.status === 'complete' ? '#0d9488' : '#d97706'}>
                    {item.status}
                  </Badge>
                </div>
                <span className="text-[10px] text-slate-400 font-mono tabular-nums">
                  {(item.uploaded_at || item.created_at) ? new Date(item.uploaded_at || item.created_at).toLocaleDateString('en-IN') : ''}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
