'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import axios from 'axios';

// ── All API calls go to /api/* on the same Vercel domain ──────────────────────
const API = '/api';

const SEVERITY_CONFIG = {
  mild:     { color: '#4ade80', bg: 'rgba(74,222,128,0.1)',  label: 'Mild',     icon: '○' },
  moderate: { color: '#fbbf24', bg: 'rgba(251,191,36,0.1)',  label: 'Moderate', icon: '◐' },
  severe:   { color: '#f87171', bg: 'rgba(248,113,113,0.1)', label: 'Severe',   icon: '●' },
  critical: { color: '#ff3b30', bg: 'rgba(255,59,48,0.15)',  label: 'Critical', icon: '⬤' },
};

// ─────────────────────────────────────────────────────────────────────────────
// Small reusable components
// ─────────────────────────────────────────────────────────────────────────────

function SymptomTag({ symptom, selected, onClick }) {
  return (
    <button className={`symptom-tag ${selected ? 'selected' : ''}`} onClick={() => onClick(symptom.id)}>
      {symptom.label}
    </button>
  );
}

function ResultCard({ prediction, rank }) {
  const sev   = SEVERITY_CONFIG[prediction.severity] || SEVERITY_CONFIG.moderate;
  const width = Math.max(8, prediction.confidence);
  return (
    <div className={`result-card ${rank === 0 ? 'top-result' : ''}`} style={{ animationDelay: `${rank * 80}ms` }}>
      <div className="result-header">
        <div className="result-rank">#{rank + 1}</div>
        <div className="result-disease">{prediction.disease}</div>
        <div className="result-confidence">{prediction.confidence}%</div>
      </div>
      <div className="confidence-bar">
        <div className="confidence-fill" style={{ width: `${width}%`, background: rank === 0 ? 'var(--accent)' : 'var(--muted)' }} />
      </div>
      <div className="result-meta">
        <span className="severity-badge" style={{ color: sev.color, background: sev.bg }}>{sev.icon} {sev.label}</span>
        <span className="result-advice">{prediction.advice}</span>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────

export default function Home() {
  const [allSymptoms,    setAllSymptoms]    = useState([]);
  const [categories,     setCategories]     = useState([]);
  const [selected,       setSelected]       = useState(new Set());
  const [activeCategory, setActiveCategory] = useState('');
  const [predictions,    setPredictions]    = useState(null);
  const [loading,        setLoading]        = useState(false);
  const [error,          setError]          = useState(null);
  const [step,           setStep]           = useState('select');
  const [search,         setSearch]         = useState('');
  const [apiStatus,      setApiStatus]      = useState('checking');

  // Load symptoms + categories from /api/*
  useEffect(() => {
    axios.get(`${API}/health`)
      .then(() => {
        setApiStatus('ok');
        return Promise.all([axios.get(`${API}/symptoms`), axios.get(`${API}/categories`)]);
      })
      .then(([sympRes, catRes]) => {
        setAllSymptoms(sympRes.data);
        setCategories(catRes.data);
        if (catRes.data.length > 0) setActiveCategory(catRes.data[0].id);
      })
      .catch(() => setApiStatus('error'));
  }, []);

  const toggleSymptom = (id) => {
    setSelected(prev => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next; });
  };

  const predict = async () => {
    if (selected.size < 2) { setError('Please select at least 2 symptoms.'); return; }
    setError(null);
    setLoading(true);
    try {
      const symptomIds = Array.from(selected);
      const res        = await axios.post(`${API}/predict`, { symptoms: symptomIds });
      setPredictions(res.data);
      setStep('results');
    } catch {
      setError('Could not reach the prediction service. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const reset = () => { setSelected(new Set()); setPredictions(null); setStep('select'); setSearch(''); setError(null); };

  const displayedSymptoms = useMemo(() => {
    if (search.trim()) { const q = search.toLowerCase(); return allSymptoms.filter(s => s.label.toLowerCase().includes(q)); }
    const cat = categories.find(c => c.id === activeCategory);
    if (!cat) return allSymptoms.slice(0, 20);
    return allSymptoms.filter(s => cat.keywords.some(k => s.id.includes(k)));
  }, [allSymptoms, categories, activeCategory, search]);

  const selectedSymptoms = allSymptoms.filter(s => selected.has(s.id));

  return (
    <div className="app">
      <div className="bg-grid" />
      <div className="bg-glow" />

      {/* Header */}
      <header className="header">
        <div className="header-inner">
          <div className="logo" onClick={reset}>
            <span className="logo-icon">⬡</span>
            <span className="logo-text">SymptomAI</span>
          </div>
          <div className="header-right">
            <div className={`api-dot ${apiStatus}`} title={`API: ${apiStatus}`} />
            {step === 'results' && <button className="btn-ghost" onClick={reset}>← New Check</button>}
          </div>
        </div>
      </header>

      <main className="main">

        {/* ── STEP 1: SELECT SYMPTOMS ─────────────────────────────────────── */}
        {step === 'select' && (
          <>
            <section className="hero">
              <p className="hero-eyebrow">AI-Powered Symptom Analysis</p>
              <h1 className="hero-title">What&apos;s your <em>body</em> telling you?</h1>
              <p className="hero-sub">
                Select your symptoms. Our ML model analyzes 41 conditions across 131 symptoms.
              </p>
            </section>

            {selected.size > 0 && (
              <div className="selected-bar">
                <span className="selected-count">{selected.size} symptom{selected.size !== 1 ? 's' : ''} selected</span>
                <div className="selected-chips">
                  {selectedSymptoms.map(s => (
                    <span key={s.id} className="chip" onClick={() => toggleSymptom(s.id)}>
                      {s.label} <span className="chip-x">×</span>
                    </span>
                  ))}
                </div>
                <button className="btn-clear" onClick={() => setSelected(new Set())}>Clear all</button>
              </div>
            )}

            <div className="search-wrap">
              <span className="search-icon">⌕</span>
              <input className="search-input" placeholder="Search symptoms…" value={search} onChange={e => setSearch(e.target.value)} />
              {search && <button className="search-clear" onClick={() => setSearch('')}>×</button>}
            </div>

            {!search && (
              <div className="category-tabs">
                {categories.map(cat => {
                  const ids      = allSymptoms.filter(s => cat.keywords.some(k => s.id.includes(k))).map(s => s.id);
                  const selCount = ids.filter(id => selected.has(id)).length;
                  return (
                    <button key={cat.id} className={`cat-tab ${activeCategory === cat.id ? 'active' : ''}`} onClick={() => setActiveCategory(cat.id)}>
                      <span className="cat-icon">{cat.icon}</span>
                      {cat.label}
                      {selCount > 0 && <span className="cat-badge">{selCount}</span>}
                    </button>
                  );
                })}
              </div>
            )}

            <div className="symptom-grid">
              {displayedSymptoms.length === 0 && <p className="no-results">No symptoms found for &quot;{search}&quot;</p>}
              {displayedSymptoms.map(s => (
                <SymptomTag key={s.id} symptom={s} selected={selected.has(s.id)} onClick={toggleSymptom} />
              ))}
            </div>

            {error && <div className="error-msg">{error}</div>}

            <div className="predict-wrap">
              <button className={`btn-predict ${selected.size >= 2 ? 'ready' : ''}`} onClick={predict} disabled={loading || selected.size < 2}>
                {loading ? <span className="loading-dots"><span/><span/><span/></span> : <>Analyze {selected.size > 0 ? `${selected.size} Symptom${selected.size !== 1 ? 's' : ''}` : 'Symptoms'} →</>}
              </button>
              {selected.size < 2 && <p className="predict-hint">Select at least 2 symptoms to continue</p>}
            </div>
          </>
        )}

        {/* ── STEP 2: RESULTS ─────────────────────────────────────────────── */}
        {step === 'results' && predictions && (
          <div className="results-section">
            <div className="results-header">
              <h2 className="results-title">Differential Diagnosis</h2>
              <p className="results-sub">Based on <strong>{predictions.symptom_count}</strong> symptom{predictions.symptom_count !== 1 ? 's' : ''} analyzed</p>
            </div>

            <div className="results-grid">
              {predictions.predictions.map((pred, i) => <ResultCard key={pred.disease} prediction={pred} rank={i} />)}
            </div>

            <div className="disclaimer-box">
              <span className="disclaimer-icon">⚠</span>
              <p>{predictions.disclaimer}</p>
            </div>

            <button className="btn-predict ready" onClick={reset}>← Check Different Symptoms</button>
          </div>
        )}

      </main>

      <footer className="footer">
        <p>ML model: scikit-learn · Dataset: Kaggle · <span className="footer-link">For educational purposes only</span></p>
      </footer>
    </div>
  );
}
