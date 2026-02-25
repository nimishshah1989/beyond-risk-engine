import { useState } from 'react'
import { Card, Badge, Btn, Bar } from '../components/UI'
import { analyzeDocument, saveAnalyzedProduct } from '../services/api'
import { TRAITS } from '../data/traits'

export default function Upload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true); setError(null); setResult(null); setSaved(false);
    try {
      const res = await analyzeDocument(file);
      setResult(res.analysis);
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  const handleSave = async () => {
    if (!result) return;
    try {
      await saveAnalyzedProduct({
        risk_vector: result.risk_vector,
        extracted_info: result.extracted_info,
        reasoning: result.reasoning,
        source_file: file.name
      });
      setSaved(true);
    } catch (e) { setError(e.message); }
  };

  const traitColor = (v) => v >= 70 ? '#dc2626' : v >= 40 ? '#d97706' : '#059669';

  return (
    <div>
      <Card className="mb-5">
        <div className="flex items-start gap-4">
          <div className="text-4xl">🤖</div>
          <div>
            <h2 className="text-lg font-extrabold">AI Instrument Analyzer</h2>
            <p className="text-xs text-gray-500 mt-1">
              Upload a product factsheet (PMS, AIF, MF, SIF) and the AI will automatically compute the 10-trait
              behavioral demand vector — how much of each behavioral trait an investor needs to comfortably hold this product.
            </p>
          </div>
        </div>
      </Card>

      {/* Upload area */}
      <Card className="mb-5">
        <div className="flex items-center gap-4">
          <label className="flex-1 cursor-pointer">
            <div className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${file ? 'border-green-300 bg-green-50' : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/30'}`}>
              {file ? (
                <div><div className="text-2xl mb-1">📄</div><div className="text-sm font-bold text-green-800">{file.name}</div><div className="text-[11px] text-green-600">{(file.size/1024).toFixed(0)} KB · Click to change</div></div>
              ) : (
                <div><div className="text-3xl mb-2">📎</div><div className="text-sm font-bold text-gray-600">Drop a PDF factsheet or click to upload</div><div className="text-[11px] text-gray-400">PMS, AIF, MF scheme documents · Max 10MB</div></div>
              )}
            </div>
            <input type="file" accept=".pdf" className="hidden" onChange={e => setFile(e.target.files[0])} />
          </label>
          <Btn primary onClick={handleUpload} disabled={!file || loading} className="h-12">
            {loading ? '⏳ Analyzing...' : '🔬 Analyze Document'}
          </Btn>
        </div>
      </Card>

      {error && <div className="bg-red-50 text-red-700 text-xs p-4 rounded-xl mb-5 border border-red-200">❌ {error}</div>}

      {loading && (
        <Card className="mb-5">
          <div className="text-center py-8">
            <div className="text-3xl mb-3 animate-pulse">🧠</div>
            <p className="text-sm font-bold text-blue-800">AI is reading the document...</p>
            <p className="text-xs text-gray-400 mt-1">Extracting product characteristics and computing behavioral demand scores</p>
            <div className="mt-4 w-48 mx-auto"><Bar value={65} max={100} color="#1746a2" h={4} /></div>
          </div>
        </Card>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Extracted Info */}
          <Card className="mb-4">
            <h3 className="text-sm font-bold mb-3">📋 Extracted Product Information</h3>
            <div className="grid grid-cols-3 gap-4">
              {result.extracted_info && Object.entries(result.extracted_info).map(([k, v]) => v && (
                <div key={k} className="bg-gray-50 p-3 rounded-lg">
                  <div className="text-[10px] text-gray-400 uppercase font-bold">{k.replace(/_/g, ' ')}</div>
                  <div className="text-xs font-bold text-gray-900 mt-0.5">{typeof v === 'number' ? v.toLocaleString() : v}</div>
                </div>
              ))}
            </div>
          </Card>

          {/* Risk Vector */}
          <Card className="mb-4">
            <h3 className="text-sm font-bold mb-3">🎯 Computed Behavioral Demand Vector</h3>
            <p className="text-[10.5px] text-gray-400 mb-4">How much of each trait an investor needs to comfortably hold this product</p>
            <div className="space-y-3">
              {result.risk_vector && Object.entries(result.risk_vector).map(([trait, val]) => {
                const t = TRAITS[trait];
                return (
                  <div key={trait}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span>{t?.icon || '📊'}</span>
                        <span className="text-xs font-bold">{t?.name || trait}</span>
                        <Badge color={traitColor(val)}>{val >= 70 ? 'High Demand' : val >= 40 ? 'Moderate' : 'Low Demand'}</Badge>
                      </div>
                      <span className="text-sm font-extrabold" style={{color: traitColor(val)}}>{val}</span>
                    </div>
                    <Bar value={val} max={100} color={traitColor(val)} h={7} />
                  </div>
                );
              })}
            </div>
          </Card>

          {/* AI Reasoning */}
          {result.reasoning && (
            <Card className="mb-4">
              <h3 className="text-sm font-bold mb-3">🧠 AI Reasoning</h3>
              <p className="text-[10.5px] text-gray-400 mb-3">Why the AI assigned each score — review before saving</p>
              <div className="space-y-2">
                {Object.entries(result.reasoning).map(([trait, reason]) => (
                  <div key={trait} className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-[10px] font-bold text-blue-700 uppercase">{trait.replace(/_/g, ' ')}</div>
                    <p className="text-xs text-gray-600 mt-1">{reason}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Save */}
          <Card className={saved ? 'bg-green-50 border-green-200' : ''}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold">{saved ? '✅ Saved to Product Database' : 'Save to Product Universe?'}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{saved ? 'Product is now available for behavioral matching' : 'Review the analysis above, then save to make it available for matching'}</p>
              </div>
              {!saved && <Btn primary onClick={handleSave}>💾 Save Product</Btn>}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
