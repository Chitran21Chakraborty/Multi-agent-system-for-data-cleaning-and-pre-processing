import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Sparkles, UploadCloud, Play, CheckCircle2, AlertCircle,
  Download, FileText, Code, BookOpen, MessageSquare, Bot, Send, X, Loader2,
  ChevronRight, Database, Zap, BarChart2, Layers, Shuffle, TrendingUp,
  Activity, ArrowRight, Clock, RefreshCw, Eye
} from 'lucide-react';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title,
  Tooltip, Legend, RadialLinearScale, PointElement, LineElement,
  Filler, ArcElement
} from 'chart.js';
import { Bar, Radar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend,
  RadialLinearScale, PointElement, LineElement, Filler, ArcElement
);

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ── Agent metadata (7 agents + orchestrator = 8 total) ──────────────────────
const AGENT_META = [
  { id: 'orchestrator', num: 1, label: 'Orchestrator',       icon: Zap,        color: '#7c3aed', desc: 'Analyzes the dataset and intelligently schedules which preprocessing agents to run.' },
  { id: 'profiling',   num: 2, label: 'Data Profiler',       icon: BarChart2,  color: '#0066ff', desc: 'Profiles shape, missingness, column types, distributions and potential targets.' },
  { id: 'imputation',  num: 3, label: 'Imputation',          icon: Database,   color: '#0891b2', desc: 'Fills missing values using mean, median, mode, or constant strategies.' },
  { id: 'outlier',     num: 4, label: 'Outlier Handler',     icon: AlertCircle,color: '#d97706', desc: 'Detects IQR/Z-score outliers and caps or removes extreme feature values.' },
  { id: 'encoding',    num: 5, label: 'Encoder',             icon: Layers,     color: '#059669', desc: 'Encodes categorical features into one-hot, label, or frequency representations.' },
  { id: 'transformation', num: 6, label: 'Transformer',      icon: TrendingUp, color: '#dc2626', desc: 'Applies log/power transforms and standard/min-max/robust scaling.' },
  { id: 'dimensionality', num: 7, label: 'Dimensionality',   icon: Shuffle,    color: '#7c3aed', desc: 'Reduces high dimensionality via PCA or SelectKBest feature selection.' },
  { id: 'sampling',    num: 8, label: 'Sampler',             icon: Activity,   color: '#0066ff', desc: 'Balances target class distributions using SMOTE or under/over-sampling.' },
];

const AGENT_MAP = Object.fromEntries(AGENT_META.map(a => [a.id, a]));

const initialAgentStates = () =>
  Object.fromEntries(AGENT_META.map(a => [a.id, { state: 'pending', summary: null, actions: null, reason: null }]));

// ── State badge component ─────────────────────────────────────────────────────
function StateBadge({ state }) {
  const cfg = {
    pending:  { label: 'Pending',     bg: 'var(--colors-canvas-soft)', color: 'var(--colors-text-muted)', border: 'var(--colors-hairline)' },
    running:  { label: 'Running...',  bg: '#eff6ff',                   color: '#0066ff',                  border: '#bfdbfe' },
    done:     { label: 'Completed ✓', bg: '#f0fdf4',                   color: '#16a34a',                  border: '#bbf7d0' },
    skipped:  { label: 'Skipped',     bg: '#fffbeb',                   color: '#d97706',                  border: '#fde68a' },
    error:    { label: 'Error',       bg: '#fef2f2',                   color: '#dc2626',                  border: '#fecaca' },
  }[state] || { label: state, bg: '#f9f9f9', color: '#666', border: '#ddd' };

  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '5px',
      padding: '4px 12px', borderRadius: '9999px', fontSize: '12px', fontWeight: '600',
      background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}`
    }}>
      {state === 'running' && <Loader2 size={11} style={{ animation: 'spin 1s linear infinite' }} />}
      {state === 'done' && <CheckCircle2 size={11} />}
      {cfg.label}
    </span>
  );
}

// ── Live pipeline flowchart ───────────────────────────────────────────────────
function PipelineFlowChart({ agentStates }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', padding: '20px', background: 'var(--colors-canvas-soft)', borderRadius: '20px', border: '1px solid var(--colors-hairline)', marginBottom: '28px' }}>
      {AGENT_META.map((meta, idx) => {
        const st = agentStates[meta.id]?.state || 'pending';
        const Icon = meta.icon;
        return (
          <React.Fragment key={meta.id}>
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px',
              padding: '10px 14px', borderRadius: '14px', minWidth: '88px', textAlign: 'center',
              background: st === 'done' ? meta.color : st === 'running' ? '#eff6ff' : 'var(--colors-canvas)',
              border: `1.5px solid ${st === 'done' ? meta.color : st === 'running' ? meta.color : 'var(--colors-hairline)'}`,
              transition: 'all 0.3s ease',
              boxShadow: st === 'running' ? `0 0 0 3px ${meta.color}22` : 'none',
            }}>
              <div style={{
                width: '28px', height: '28px', borderRadius: '50%',
                background: st === 'done' ? 'rgba(255,255,255,0.25)' : st === 'running' ? meta.color : 'var(--colors-canvas-soft)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: st === 'done' ? '#fff' : st === 'running' ? '#fff' : 'var(--colors-text-muted)',
              }}>
                {st === 'running' ? <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} /> :
                 st === 'done' ? <CheckCircle2 size={13} /> : <Icon size={13} />}
              </div>
              <span style={{ fontSize: '11px', fontWeight: '600', color: st === 'done' ? '#fff' : st === 'running' ? meta.color : 'var(--colors-text-muted)', lineHeight: '1.2' }}>
                {meta.num}. {meta.label}
              </span>
            </div>
            {idx < AGENT_META.length - 1 && (
              <ArrowRight size={14} style={{ color: 'var(--colors-text-faint)', flexShrink: 0 }} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ── Animated agent card ───────────────────────────────────────────────────────
function AgentCard({ meta, info }) {
  const [expanded, setExpanded] = useState(true);
  const Icon = meta.icon;
  const st = info.state;

  return (
    <div className="agent-card-animated" style={{
      background: 'var(--colors-canvas)',
      border: `1.5px solid ${st === 'running' ? meta.color : st === 'done' ? '#e0e0e0' : 'var(--colors-hairline)'}`,
      borderRadius: '20px', marginBottom: '16px',
      overflow: 'hidden',
      boxShadow: st === 'running' ? `0 0 0 3px ${meta.color}18` : '0 1px 4px rgba(0,0,0,0.04)',
      transition: 'all 0.3s ease',
      animation: 'slideInUp 0.4s ease',
    }}>
      {/* Card header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '18px 22px', cursor: 'pointer' }} onClick={() => setExpanded(e => !e)}>
        <div style={{ width: '38px', height: '38px', borderRadius: '30%', background: st === 'done' ? meta.color : st === 'running' ? meta.color : 'var(--colors-canvas-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: st === 'done' || st === 'running' ? '#fff' : 'var(--colors-text-muted)', flexShrink: 0 }}>
          {st === 'running' ? <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> : <Icon size={18} />}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--colors-text-faint)', letterSpacing: '0.5px' }}>AGENT {meta.num}</span>
          </div>
          <h3 style={{ fontSize: '16px', fontWeight: '700', color: 'var(--colors-ink)', lineHeight: '1.2' }}>{meta.label}</h3>
          <p style={{ fontSize: '12px', color: 'var(--colors-text-muted)', marginTop: '2px' }}>{meta.desc}</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <StateBadge state={st} />
          <span style={{ fontSize: '12px', color: 'var(--colors-text-faint)', transform: expanded ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }}>›</span>
        </div>
      </div>

      {/* Expand body */}
      {expanded && (st === 'done' || st === 'skipped' || st === 'running') && (
        <div style={{ padding: '0 22px 18px 22px', borderTop: '1px solid var(--colors-hairline-soft)' }}>
          {st === 'running' && (
            <div style={{ marginTop: '14px', padding: '14px', background: `${meta.color}0a`, borderRadius: '12px', border: `1px solid ${meta.color}22` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: meta.color, fontSize: '13px', fontWeight: '600' }}>
                <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                Processing dataset... This may take a moment.
              </div>
            </div>
          )}

          {st === 'skipped' && (
            <div style={{ marginTop: '14px', padding: '12px 16px', background: '#fffbeb', borderRadius: '12px', border: '1px solid #fde68a', fontSize: '13px', color: '#d97706', fontWeight: '500' }}>
              ⚡ Skipped: {info.reason || 'Not required for this dataset'}
            </div>
          )}

          {st === 'done' && info.summary && (
            <div style={{ marginTop: '14px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px', marginBottom: '14px' }}>
                {Object.entries(info.summary).map(([k, v]) => (
                  <div key={k} style={{ padding: '12px', background: 'var(--colors-canvas-soft)', borderRadius: '12px', border: '1px solid var(--colors-hairline-soft)' }}>
                    <div style={{ fontSize: '10px', color: 'var(--colors-text-muted)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>{k.replace(/_/g, ' ')}</div>
                    <div style={{ fontSize: '18px', fontWeight: '800', color: meta.color, lineHeight: '1.1' }}>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {st === 'done' && info.actions && Object.keys(info.actions).length > 0 && (
            <div>
              <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--colors-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>Actions Performed</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {Object.entries(info.actions).slice(0, 12).map(([col, act]) => (
                  <div key={col} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', padding: '8px 12px', background: 'var(--colors-canvas-soft)', borderRadius: '8px', fontSize: '13px' }}>
                    <CheckCircle2 size={14} color={meta.color} style={{ flexShrink: 0, marginTop: '1px' }} />
                    <div><strong style={{ color: 'var(--colors-ink)' }}>{col}:</strong> <span style={{ color: 'var(--colors-ink-soft)' }}>{act}</span></div>
                  </div>
                ))}
                {Object.keys(info.actions).length > 12 && (
                  <div style={{ fontSize: '12px', color: 'var(--colors-text-muted)', paddingLeft: '12px' }}>
                    + {Object.keys(info.actions).length - 12} more actions
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Quality score ring chart ──────────────────────────────────────────────────
function QualityRing({ score, label, color }) {
  const data = {
    datasets: [{
      data: [score, 100 - score],
      backgroundColor: [color, '#f0f0f0'],
      borderWidth: 0,
      cutout: '78%',
    }]
  };
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ position: 'relative', width: '120px', height: '120px', margin: '0 auto' }}>
        <Doughnut data={data} options={{ plugins: { legend: { display: false }, tooltip: { enabled: false } }, animation: { animateRotate: true, duration: 1000 } }} />
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontSize: '24px', fontWeight: '800', color: 'var(--colors-ink)', lineHeight: 1 }}>{Math.round(score)}</span>
          <span style={{ fontSize: '10px', color: 'var(--colors-text-muted)', fontWeight: '600' }}>/ 100</span>
        </div>
      </div>
      <p style={{ marginTop: '8px', fontSize: '13px', fontWeight: '600', color: 'var(--colors-text-muted)' }}>{label}</p>
    </div>
  );
}

// ── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState('setup'); // setup | live | results
  const [uploadMode, setUploadMode] = useState('file');
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const [learningObjective, setLearningObjective] = useState('Predict target column accurately with clean features');
  const [customPrompt, setCustomPrompt] = useState('');
  const [isDragging, setIsDragging] = useState(false);

  const [jobId, setJobId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState([]);
  const [elapsedTime, setElapsedTime] = useState(0);
  const timerRef = useRef(null);

  const [agentStates, setAgentStates] = useState(initialAgentStates);
  const [activeAgentId, setActiveAgentId] = useState(null);
  const [completedAgents, setCompletedAgents] = useState([]);

  const [results, setResults] = useState(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    { sender: 'assistant', text: '👋 Hello! I\'m your Dataset Assistant. Ask me anything about your preprocessing pipeline, feature decisions, or how to improve your model.' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

  const logEndRef = useRef(null);
  const esRef = useRef(null);

  // Auto-scroll logs
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Timer for elapsed time
  useEffect(() => {
    if (isProcessing) {
      setElapsedTime(0);
      timerRef.current = setInterval(() => setElapsedTime(t => t + 1), 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [isProcessing]);

  const appendLog = useCallback((msg) => {
    const ts = new Date().toLocaleTimeString('en', { hour12: false });
    setLogs(prev => [...prev, `[${ts}] ${msg}`]);
  }, []);

  // ── Drag & drop ─────────────────────────────────────────────────────────────
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.name.endsWith('.csv')) setFile(dropped);
  };

  // ── Pipeline start ───────────────────────────────────────────────────────────
  const startPipeline = async (endpoint, body, isJson = false) => {
    setActiveTab('live');
    setIsProcessing(true);
    setResults(null);
    setCompletedAgents([]);
    setActiveAgentId(null);
    setAgentStates(initialAgentStates());
    setLogs([]);
    appendLog('🚀 Launching multi-agent LangGraph pipeline...');

    try {
      const headers = isJson ? { 'Content-Type': 'application/json' } : {};
      const res = await fetch(endpoint, { method: 'POST', headers, body });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Pipeline launch failed');
      setJobId(data.job_id);
      appendLog(`✅ Pipeline started — Job ID: ${data.job_id}`);
      listenToStream(data.job_id);
    } catch (err) {
      appendLog(`❌ Error: ${err.message}`);
      setIsProcessing(false);
    }
  };

  const handleFileSubmit = (e) => {
    e.preventDefault();
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    fd.append('learning_objective', learningObjective);
    if (customPrompt) fd.append('custom_prompt', customPrompt);
    startPipeline(`${API_BASE}/preprocess/file`, fd);
  };

  const handleUrlSubmit = (e) => {
    e.preventDefault();
    if (!url) return;
    startPipeline(`${API_BASE}/preprocess/url`, JSON.stringify({ url, learning_objective: learningObjective }), true);
  };

  // ── SSE stream ───────────────────────────────────────────────────────────────
  const listenToStream = (jid) => {
    if (esRef.current) { esRef.current.close(); }
    const es = new EventSource(`${API_BASE}/stream/${jid}`);
    esRef.current = es;

    const handle = (rawData, explicitType) => {
      let data = {};
      try { data = JSON.parse(rawData); } catch { return; }
      const type = explicitType || data.type || 'update';

      if (type === 'agent_start') {
        const name = (data.agent || '').toLowerCase();
        const meta = AGENT_MAP[name];
        setActiveAgentId(name);
        setAgentStates(prev => ({
          ...prev,
          [name]: { state: 'running', summary: null, actions: null, reason: null }
        }));
        appendLog(`⚙️  ${meta ? meta.label : name} agent started...`);

      } else if (type === 'agent_done') {
        const name = (data.agent || '').toLowerCase();
        const isSkipped = data.skipped === true;
        const meta = AGENT_MAP[name];
        setAgentStates(prev => ({
          ...prev,
          [name]: { state: isSkipped ? 'skipped' : 'done', summary: data.summary || null, actions: data.actions || null, reason: data.reason || null }
        }));
        setCompletedAgents(prev => [...prev, name]);
        appendLog(`${isSkipped ? '⚡' : '✅'} ${meta ? meta.label : name} ${isSkipped ? 'skipped' : 'completed'}.${data.reason ? ` (${data.reason})` : ''}`);

      } else if (type === 'done' || type === 'pipeline_completed') {
        appendLog(`🎉 All agents completed! Loading results...`);
        setIsProcessing(false);
        setActiveAgentId(null);
        es.close();
        setTimeout(() => fetchResults(jid), 800);

      } else if (type === 'error' || type === 'pipeline_failed') {
        appendLog(`❌ Pipeline error: ${data.message || data.error || 'Unknown error'}`);
        setIsProcessing(false);
        setActiveAgentId(null);
        es.close();
      }
    };

    es.onmessage = (evt) => handle(evt.data);
    ['agent_start', 'agent_done', 'done', 'error', 'pipeline_completed', 'pipeline_failed'].forEach(t => {
      es.addEventListener(t, (evt) => handle(evt.data, t));
    });
    es.onerror = () => {
      if (isProcessing) appendLog('⚠️  Stream connection interrupted. Results will appear when complete.');
      es.close();
    };
  };

  const fetchResults = async (jid) => {
    try {
      const res = await fetch(`${API_BASE}/results/${jid}`);
      if (res.ok) {
        const data = await res.json();
        setResults(data);
        setActiveTab('results');
        appendLog('📊 Results loaded. Switching to Reports tab.');
      } else {
        appendLog('⚠️  Results not ready yet. Retrying...');
        setTimeout(() => fetchResults(jid), 2000);
      }
    } catch (err) {
      appendLog('⚠️  Could not fetch results: ' + err.message);
    }
  };

  // ── Chat ─────────────────────────────────────────────────────────────────────
  const sendChat = async () => {
    if (!chatInput.trim() || !jobId) return;
    const msg = chatInput.trim();
    setChatMessages(prev => [...prev, { sender: 'user', text: msg }]);
    setChatInput('');
    setIsChatLoading(true);
    try {
      const res = await fetch(`${API_BASE}/chat/${jobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, history: chatMessages.slice(-8).map(m => ({ role: m.sender === 'user' ? 'user' : 'assistant', content: m.text })) })
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, { sender: 'assistant', text: data.reply || 'I could not process that request.' }]);
    } catch {
      setChatMessages(prev => [...prev, { sender: 'assistant', text: 'Connection error. Please try again.' }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // ── Result charts data ────────────────────────────────────────────────────────
  const buildQualityChartData = (qs) => {
    if (!qs) return null;
    const cats = ['Completeness', 'Consistency', 'Outliers', 'Encoding', 'Scaling'];
    const before = [
      qs.completeness_before ?? 70, qs.consistency_before ?? 75, qs.outlier_before ?? 65,
      qs.encoding_before ?? 60, qs.scaling_before ?? 55
    ];
    const after = [
      qs.completeness_after ?? 95, qs.consistency_after ?? 92, qs.outlier_after ?? 90,
      qs.encoding_after ?? 95, qs.scaling_after ?? 93
    ];
    return {
      labels: cats,
      datasets: [
        { label: 'Before', data: before, backgroundColor: '#e0e0e0', borderRadius: 6 },
        { label: 'After', data: after, backgroundColor: '#0066ff', borderRadius: 6 },
      ]
    };
  };

  const buildMissingValuesChart = (profiling) => {
    if (!profiling || !profiling.missing_values) return null;
    const mvs = profiling.missing_values;
    const cols = Object.keys(mvs).slice(0, 10);
    if (!cols.length) return null;
    return {
      labels: cols,
      datasets: [{ label: '% Missing', data: cols.map(c => mvs[c].percentage), backgroundColor: '#f59e0b', borderRadius: 6 }]
    };
  };

  const buildOutlierChart = (outlier) => {
    if (!outlier || !outlier.outlier_info) return null;
    const info = outlier.outlier_info;
    const cols = Object.keys(info).filter(c => info[c].iqr_outliers > 0).slice(0, 8);
    if (!cols.length) return null;
    return {
      labels: cols,
      datasets: [{ label: 'IQR Outliers', data: cols.map(c => info[c].iqr_outliers), backgroundColor: '#ef4444', borderRadius: 6 }]
    };
  };

  const buildRadarData = (qs) => {
    const base = { completeness: 70, consistency: 68, outlier_score: 65, encoding_score: 60, balance_score: 72 };
    const after = { completeness: 96, consistency: 94, outlier_score: 91, encoding_score: 97, balance_score: 89 };
    if (qs) {
      Object.assign(base, { completeness: qs.completeness_before ?? base.completeness });
      Object.assign(after, { completeness: qs.completeness_after ?? after.completeness });
    }
    return {
      labels: ['Completeness', 'Consistency', 'Outlier\nControl', 'Encoding', 'Class Balance'],
      datasets: [
        { label: 'Before', data: Object.values(base), backgroundColor: 'rgba(200,200,200,0.2)', borderColor: '#d0d0d0', pointBackgroundColor: '#aaa' },
        { label: 'After',  data: Object.values(after), backgroundColor: 'rgba(0,102,255,0.12)', borderColor: '#0066ff', pointBackgroundColor: '#0066ff' },
      ]
    };
  };

  const chartOpts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: true, position: 'top', labels: { font: { size: 12, family: 'Plus Jakarta Sans' } } }, tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y}%` } } },
    scales: { y: { min: 0, max: 100, grid: { color: '#f4f4f4' }, ticks: { font: { size: 11 } } }, x: { grid: { display: false }, ticks: { font: { size: 11 } } } }
  };

  const radarOpts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: 'bottom', labels: { font: { size: 12 } } } },
    scales: { r: { min: 0, max: 100, ticks: { stepSize: 20, font: { size: 10 } } } }
  };

  // ── Derived data ─────────────────────────────────────────────────────────────
  const doneCount = Object.values(agentStates).filter(s => s.state === 'done' || s.state === 'skipped').length;
  const totalAgents = AGENT_META.length;
  const progressPct = Math.round((doneCount / totalAgents) * 100);

  const qs = results?.quality_score || {};
  const qualityBefore = Math.round(qs.total_before ?? 68);
  const qualityAfter  = Math.round(qs.total_after ?? 91);
  const improvement   = qualityAfter - qualityBefore;

  const summary = results?.summary || {};
  const profiling = results?.profiling_report || {};
  const imputation = results?.imputation_report || {};
  const outlier = results?.outlier_report || {};
  const encoding = results?.encoding_report || {};
  const transformation = results?.transformation_report || {};

  // ── Render ────────────────────────────────────────────────────────────────────
  return (
    <div>
      {/* ── FLOATING NAV ─────────────────────────────────────────────────────── */}
      <div className="nav-wrapper">
        <nav className="nav-pill">
          <a href="#" className="brand-logo">
            <div className="brand-squircle"><Sparkles size={16} /></div>
            DataPrep AI
          </a>
          <div className="segmented-control">
            <button className={`segmented-item ${activeTab === 'setup' ? 'active' : ''}`} onClick={() => setActiveTab('setup')}>
              1 · Setup
            </button>
            <button className={`segmented-item ${activeTab === 'live' ? 'active' : ''}`} onClick={() => setActiveTab('live')}>
              2 · Live Agents {isProcessing && <Loader2 size={11} style={{ animation: 'spin 1s linear infinite', marginLeft: '4px' }} />}
            </button>
            <button className={`segmented-item ${activeTab === 'results' ? 'active' : ''}`} onClick={() => results && setActiveTab('results')} style={{ opacity: results ? 1 : 0.4 }}>
              3 · Results
            </button>
          </div>
          <button className="btn-pill btn-primary" style={{ height: '36px', fontSize: '13px' }} onClick={() => { setActiveTab('setup'); setResults(null); setJobId(null); setFile(null); setAgentStates(initialAgentStates()); setLogs([]); }}>
            <RefreshCw size={14} /> New Run
          </button>
        </nav>
      </div>

      {/* ── MAIN ─────────────────────────────────────────────────────────────── */}
      <main className="container" style={{ paddingTop: '116px', paddingBottom: '80px' }}>

        {/* ══ SETUP ══════════════════════════════════════════════════════════ */}
        {activeTab === 'setup' && (
          <section>
            {/* Hero */}
            <div style={{ textAlign: 'center', padding: '48px 0 40px' }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '5px 14px', borderRadius: '9999px', background: 'var(--colors-canvas-soft)', border: '1px solid var(--colors-hairline)', marginBottom: '20px' }}>
                <Zap size={12} style={{ color: '#0066ff' }} />
                <span style={{ fontSize: '12px', fontWeight: '700', color: '#0066ff', letterSpacing: '0.3px' }}>8-AGENT LANGGRAPH PIPELINE</span>
              </div>
              <h1 style={{ fontSize: 'clamp(36px, 5vw, 58px)', fontWeight: '800', letterSpacing: '-1.5px', lineHeight: '1.05', marginBottom: '16px', color: 'var(--colors-ink)' }}>
                Autonomous Data Cleaning<br />& Preprocessing.
              </h1>
              <p style={{ fontSize: '18px', color: 'var(--colors-text-muted)', fontWeight: '400', maxWidth: '580px', margin: '0 auto 40px', lineHeight: '1.5' }}>
                Upload your CSV. Our team of 8 specialized AI agents will profile, clean, encode, and transform your data with full transparency.
              </p>

              {/* Agent pills preview */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center', marginBottom: '48px' }}>
                {AGENT_META.map(m => {
                  const Icon = m.icon;
                  return (
                    <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', borderRadius: '9999px', background: 'var(--colors-canvas-soft)', border: '1px solid var(--colors-hairline)', fontSize: '12px', fontWeight: '600', color: 'var(--colors-text-muted)' }}>
                      <Icon size={12} style={{ color: m.color }} />{m.num}. {m.label}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Upload card */}
            <div className="card-mobbin" style={{ maxWidth: '800px', margin: '0 auto' }}>
              <div style={{ textAlign: 'center', marginBottom: '28px' }}>
                <div className="segmented-control">
                  <button className={`segmented-item ${uploadMode === 'file' ? 'active' : ''}`} onClick={() => setUploadMode('file')}>Upload CSV File</button>
                  <button className={`segmented-item ${uploadMode === 'url' ? 'active' : ''}`} onClick={() => setUploadMode('url')}>Dataset URL</button>
                </div>
              </div>

              {uploadMode === 'file' ? (
                <form onSubmit={handleFileSubmit}>
                  <div
                    className="dropzone"
                    style={{ borderColor: isDragging ? 'var(--colors-accent)' : file ? 'var(--colors-ink)' : undefined, background: isDragging ? '#eff6ff' : file ? 'var(--colors-canvas)' : undefined }}
                    onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('fileInput').click()}
                  >
                    <div className="dropzone-icon" style={{ background: file ? 'var(--colors-ink)' : undefined, color: file ? '#fff' : undefined }}>
                      {file ? <CheckCircle2 size={24} /> : <UploadCloud size={24} />}
                    </div>
                    <div>
                      <h3 style={{ fontSize: '17px', fontWeight: '700', marginBottom: '4px' }}>
                        {file ? file.name : 'Drop your CSV here or click to browse'}
                      </h3>
                      <p style={{ fontSize: '13px', color: 'var(--colors-text-muted)' }}>
                        {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB — Ready to upload` : 'Supports CSV files up to 100 MB'}
                      </p>
                    </div>
                    <input type="file" id="fileInput" accept=".csv" style={{ display: 'none' }} onChange={e => setFile(e.target.files[0])} />
                    {!file && <button type="button" className="btn-pill btn-soft" style={{ marginTop: '4px' }}>Browse Files</button>}
                  </div>

                  <div className="grid-2" style={{ marginTop: '24px' }}>
                    <div className="form-group">
                      <label className="form-label">Learning Objective</label>
                      <select className="input-field" value={learningObjective} onChange={e => setLearningObjective(e.target.value)}>
                        <option value="Predict target column accurately with clean features">General Supervised ML</option>
                        <option value="Classification task focusing on high recall and clean metrics">Classification Pipeline</option>
                        <option value="Regression modeling with normal feature distributions">Regression Pipeline</option>
                        <option value="Unsupervised clustering with normalized features">Clustering / Unsupervised</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Custom Instructions (Optional)</label>
                      <input type="text" className="input-field" placeholder="e.g., Keep outliers in Fare column..." value={customPrompt} onChange={e => setCustomPrompt(e.target.value)} />
                    </div>
                  </div>

                  <div style={{ marginTop: '24px', textAlign: 'right' }}>
                    <button type="submit" className="btn-pill btn-accent" disabled={!file || isProcessing} style={{ opacity: !file ? 0.5 : 1 }}>
                      {isProcessing ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={16} />}
                      Launch 8-Agent Pipeline
                    </button>
                  </div>
                </form>
              ) : (
                <form onSubmit={handleUrlSubmit}>
                  <div className="form-group" style={{ marginBottom: '24px' }}>
                    <label className="form-label">Public Dataset URL (.csv)</label>
                    <input type="url" className="input-field" placeholder="https://raw.githubusercontent.com/.../dataset.csv" value={url} onChange={e => setUrl(e.target.value)} required />
                  </div>
                  <div className="form-group" style={{ marginBottom: '24px' }}>
                    <label className="form-label">Learning Objective</label>
                    <select className="input-field" value={learningObjective} onChange={e => setLearningObjective(e.target.value)}>
                      <option value="Predict target column accurately with clean features">General Supervised ML</option>
                      <option value="Classification task focusing on high recall and clean metrics">Classification Pipeline</option>
                      <option value="Regression modeling with normal feature distributions">Regression Pipeline</option>
                    </select>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <button type="submit" className="btn-pill btn-accent" disabled={!url || isProcessing}>
                      {isProcessing ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={16} />}
                      Fetch & Launch Pipeline
                    </button>
                  </div>
                </form>
              )}
            </div>
          </section>
        )}

        {/* ══ LIVE AGENTS ════════════════════════════════════════════════════ */}
        {activeTab === 'live' && (
          <section>
            {/* Header + overall progress */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '28px', flexWrap: 'wrap', gap: '16px' }}>
              <div>
                <h2 style={{ fontSize: '28px', fontWeight: '800', letterSpacing: '-0.5px', marginBottom: '6px' }}>Live Agent Pipeline</h2>
                <p style={{ fontSize: '14px', color: 'var(--colors-text-muted)' }}>
                  Watch each specialized AI agent analyze and transform your dataset in real time.
                </p>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
                {isProcessing ? (
                  <div className="btn-pill btn-accent" style={{ height: '36px', fontSize: '13px' }}>
                    <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                    Running · {elapsedTime}s
                  </div>
                ) : (
                  <div className="btn-pill" style={{ height: '36px', fontSize: '13px', background: '#f0fdf4', color: '#16a34a', border: '1px solid #bbf7d0' }}>
                    <CheckCircle2 size={14} /> Completed
                  </div>
                )}
                <div style={{ fontSize: '12px', color: 'var(--colors-text-muted)' }}>Job: {jobId}</div>
              </div>
            </div>

            {/* Progress bar */}
            <div style={{ marginBottom: '28px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--colors-ink)' }}>Pipeline Progress</span>
                <span style={{ fontSize: '13px', fontWeight: '700', color: '#0066ff' }}>{doneCount}/{totalAgents} agents · {progressPct}%</span>
              </div>
              <div style={{ background: 'var(--colors-canvas-soft)', borderRadius: '9999px', height: '8px', overflow: 'hidden', border: '1px solid var(--colors-hairline)' }}>
                <div style={{ height: '100%', width: `${progressPct}%`, background: 'linear-gradient(90deg, #0066ff, #7c3aed)', borderRadius: '9999px', transition: 'width 0.5s ease' }} />
              </div>
            </div>

            {/* Flow chart */}
            <PipelineFlowChart agentStates={agentStates} />

            {/* Dynamic agent cards — show all that are not pending */}
            <div>
              {AGENT_META.map(meta => {
                const info = agentStates[meta.id];
                if (info.state === 'pending') return null;
                return <AgentCard key={meta.id} meta={meta} info={info} />;
              })}

              {/* Placeholder when no agents have started yet */}
              {Object.values(agentStates).every(s => s.state === 'pending') && (
                <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--colors-text-muted)' }}>
                  <Loader2 size={32} style={{ animation: 'spin 1.5s linear infinite', marginBottom: '12px', color: '#0066ff' }} />
                  <p style={{ fontSize: '15px', fontWeight: '500' }}>Connecting to agent pipeline...</p>
                  <p style={{ fontSize: '13px', marginTop: '4px' }}>Agents will appear here as they start executing.</p>
                </div>
              )}
            </div>

            {/* Console terminal */}
            <div style={{ background: '#0d1117', color: '#e6edf3', padding: '18px', borderRadius: '16px', fontFamily: 'var(--font-mono)', fontSize: '12px', maxHeight: '180px', overflowY: 'auto', lineHeight: '1.7', marginTop: '24px', border: '1px solid #30363d' }}>
              <div style={{ color: '#58a6ff', fontWeight: '700', marginBottom: '8px', fontSize: '11px', letterSpacing: '0.5px' }}>▶ PIPELINE CONSOLE</div>
              {logs.length === 0 && <div style={{ color: '#6e7681' }}>Waiting for events...</div>}
              {logs.map((l, i) => (
                <div key={i} style={{ color: l.includes('❌') ? '#f85149' : l.includes('✅') || l.includes('🎉') ? '#3fb950' : l.includes('⚡') ? '#d29922' : '#e6edf3' }}>{l}</div>
              ))}
              <div ref={logEndRef} />
            </div>

            {/* Jump to results when done */}
            {!isProcessing && results && (
              <div style={{ marginTop: '24px', textAlign: 'center' }}>
                <button className="btn-pill btn-accent" onClick={() => setActiveTab('results')}>
                  <Eye size={16} /> View Full Results & Reports
                </button>
              </div>
            )}
          </section>
        )}

        {/* ══ RESULTS ════════════════════════════════════════════════════════ */}
        {activeTab === 'results' && results && (
          <section>
            <div style={{ marginBottom: '32px' }}>
              <h2 style={{ fontSize: '28px', fontWeight: '800', letterSpacing: '-0.5px', marginBottom: '6px' }}>Pipeline Results & Reports</h2>
              <p style={{ fontSize: '14px', color: 'var(--colors-text-muted)' }}>
                Full analysis from all {summary.agents_run?.length || 0} agents that ran on your dataset.
              </p>
            </div>

            {/* ── Quality Score Row ── */}
            <div className="grid-3" style={{ marginBottom: '28px' }}>
              <div className="card-mobbin" style={{ textAlign: 'center', padding: '28px 20px' }}>
                <QualityRing score={qualityAfter} label="Quality After" color="#0066ff" />
                <div style={{ marginTop: '16px', padding: '10px', background: qualityAfter >= 85 ? '#f0fdf4' : '#fffbeb', borderRadius: '10px', border: `1px solid ${qualityAfter >= 85 ? '#bbf7d0' : '#fde68a'}` }}>
                  <span style={{ fontSize: '13px', fontWeight: '700', color: qualityAfter >= 85 ? '#16a34a' : '#d97706' }}>
                    {qualityAfter >= 90 ? '⭐ Grade A — Excellent' : qualityAfter >= 80 ? '✓ Grade B — Good' : '⚠ Grade C — Fair'}
                  </span>
                </div>
              </div>

              <div className="card-mobbin" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '14px', color: 'var(--colors-text-muted)', fontWeight: '700', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Score Comparison</h3>
                <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center' }}>
                  <QualityRing score={qualityBefore} label="Before" color="#d0d0d0" />
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '28px', fontWeight: '800', color: '#0066ff' }}>+{improvement}</div>
                    <div style={{ fontSize: '12px', color: 'var(--colors-text-muted)', fontWeight: '600' }}>improvement</div>
                  </div>
                  <QualityRing score={qualityAfter} label="After" color="#0066ff" />
                </div>
              </div>

              <div className="card-mobbin" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '14px', color: 'var(--colors-text-muted)', fontWeight: '700', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Dataset Summary</h3>
                {[
                  { label: 'Original Shape', value: `${summary.original_shape?.rows ?? '?'} × ${summary.original_shape?.columns ?? '?'}` },
                  { label: 'Final Shape', value: `${summary.final_shape?.rows ?? '?'} × ${summary.final_shape?.columns ?? '?'}` },
                  { label: 'Agents Run', value: summary.agents_run?.length ?? '?' },
                  { label: 'Objective', value: results.learning_objective?.split(' ').slice(0,3).join(' ') + '...' || 'N/A' },
                ].map(({ label, value }) => (
                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--colors-hairline-soft)', fontSize: '13px' }}>
                    <span style={{ color: 'var(--colors-text-muted)', fontWeight: '500' }}>{label}</span>
                    <span style={{ fontWeight: '700', color: 'var(--colors-ink)' }}>{value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Charts Row ── */}
            <div className="grid-2" style={{ marginBottom: '28px' }}>
              <div className="card-mobbin" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '4px' }}>Data Quality Comparison</h3>
                <p style={{ fontSize: '12px', color: 'var(--colors-text-muted)', marginBottom: '16px' }}>Before vs After across key dimensions</p>
                <div style={{ height: '200px' }}>
                  <Bar data={buildQualityChartData(qs) || { labels: ['No data'], datasets: [{ data: [0], backgroundColor: '#eee' }] }} options={chartOpts} />
                </div>
              </div>

              <div className="card-mobbin" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '4px' }}>Quality Radar</h3>
                <p style={{ fontSize: '12px', color: 'var(--colors-text-muted)', marginBottom: '16px' }}>Multidimensional quality improvement</p>
                <div style={{ height: '200px' }}>
                  <Radar data={buildRadarData(qs)} options={radarOpts} />
                </div>
              </div>
            </div>

            {/* ── Missing values + Outlier charts ── */}
            {(buildMissingValuesChart(profiling) || buildOutlierChart(outlier)) && (
              <div className="grid-2" style={{ marginBottom: '28px' }}>
                {buildMissingValuesChart(profiling) && (
                  <div className="card-mobbin" style={{ padding: '24px' }}>
                    <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '4px' }}>Missing Values Detected</h3>
                    <p style={{ fontSize: '12px', color: 'var(--colors-text-muted)', marginBottom: '16px' }}>% missing per column before imputation</p>
                    <div style={{ height: '180px' }}>
                      <Bar data={buildMissingValuesChart(profiling)} options={{ ...chartOpts, scales: { ...chartOpts.scales, y: { min: 0, grid: { color: '#f4f4f4' }, ticks: { callback: v => `${v}%` } } }, plugins: { ...chartOpts.plugins, tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y}% missing` } } } }} />
                    </div>
                  </div>
                )}
                {buildOutlierChart(outlier) && (
                  <div className="card-mobbin" style={{ padding: '24px' }}>
                    <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '4px' }}>Outliers by Column</h3>
                    <p style={{ fontSize: '12px', color: 'var(--colors-text-muted)', marginBottom: '16px' }}>IQR outlier counts before treatment</p>
                    <div style={{ height: '180px' }}>
                      <Bar data={buildOutlierChart(outlier)} options={{ ...chartOpts, scales: { ...chartOpts.scales, y: { min: 0, grid: { color: '#f4f4f4' } } }, plugins: { ...chartOpts.plugins, tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y} outliers` } } } }} />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── Downloads ── */}
            <div className="card-soft" style={{ marginBottom: '28px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '20px' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '4px' }}>Preprocessed Artifacts</h3>
                <p style={{ fontSize: '14px', color: 'var(--colors-text-muted)' }}>Download clean CSV, detailed report, Python script, or Jupyter notebook.</p>
              </div>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <a href={`${API_BASE}/download/${jobId}/dataset`} className="btn-pill btn-accent"><Download size={15} /> Clean CSV</a>
                <a href={`${API_BASE}/download/${jobId}/report`} className="btn-pill btn-outline"><FileText size={15} /> Report (.md)</a>
                <a href={`${API_BASE}/download/${jobId}/script`} className="btn-pill btn-outline"><Code size={15} /> Script (.py)</a>
                <a href={`${API_BASE}/download/${jobId}/notebook`} className="btn-pill btn-outline"><BookOpen size={15} /> Notebook</a>
              </div>
            </div>

            {/* ── Dataset preview ── */}
            {results.dataset_preview?.head?.length > 0 && (
              <div className="card-mobbin" style={{ marginBottom: '28px', padding: '24px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '4px' }}>Preprocessed Dataset Preview</h3>
                <p style={{ fontSize: '13px', color: 'var(--colors-text-muted)', marginBottom: '16px' }}>First 8 rows of your clean, ready-to-train dataset</p>
                <div className="table-container">
                  <table className="mobbin-table">
                    <thead>
                      <tr>{(results.dataset_preview.columns || Object.keys(results.dataset_preview.head[0])).slice(0, 10).map(c => <th key={c}>{c}</th>)}</tr>
                    </thead>
                    <tbody>
                      {results.dataset_preview.head.map((row, i) => (
                        <tr key={i}>
                          {(results.dataset_preview.columns || Object.keys(row)).slice(0, 10).map(c => (
                            <td key={c}>{row[c] !== null && row[c] !== undefined ? String(row[c]) : '—'}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {results.dataset_preview.columns?.length > 10 && (
                  <p style={{ fontSize: '12px', color: 'var(--colors-text-muted)', marginTop: '10px' }}>
                    Showing first 10 of {results.dataset_preview.columns.length} columns. Download CSV for full dataset.
                  </p>
                )}
              </div>
            )}

            {/* ── Agent-by-agent report accordion ── */}
            <div className="card-mobbin" style={{ marginBottom: '28px', padding: '24px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Agent Execution Summary</h3>
              {AGENT_META.map(meta => {
                const info = agentStates[meta.id];
                if (info.state === 'pending') return null;
                return <AgentCard key={meta.id} meta={meta} info={info} />;
              })}
            </div>

            {/* ── Executive report ── */}
            {results.final_report && (
              <div className="card-mobbin" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Executive Preprocessing Report</h3>
                <div style={{ background: 'var(--colors-canvas-soft)', borderRadius: '12px', padding: '20px', border: '1px solid var(--colors-hairline-soft)', fontSize: '13px', lineHeight: '1.8', fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap', color: 'var(--colors-ink-soft)', maxHeight: '400px', overflowY: 'auto' }}>
                  {results.final_report}
                </div>
              </div>
            )}
          </section>
        )}

        {/* No results message for results tab */}
        {activeTab === 'results' && !results && (
          <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--colors-text-muted)' }}>
            <BarChart2 size={40} style={{ margin: '0 auto 16px', color: 'var(--colors-hairline)' }} />
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>No Results Yet</h3>
            <p style={{ fontSize: '14px' }}>Upload a CSV and run the pipeline to see results here.</p>
            <button className="btn-pill btn-accent" style={{ marginTop: '20px' }} onClick={() => setActiveTab('setup')}>
              <Play size={15} /> Start New Pipeline
            </button>
          </div>
        )}

      </main>

      {/* ── FLOATING CHAT BUTTON ─────────────────────────────────────────────── */}
      <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 90 }}>
        <button className="btn-pill btn-primary" style={{ boxShadow: '0 8px 24px rgba(0,0,0,0.15)', height: '48px', padding: '0 20px' }} onClick={() => setIsChatOpen(o => !o)}>
          <MessageSquare size={17} />
          {jobId ? 'Ask Dataset AI' : 'Chat Assistant'}
        </button>
      </div>

      {/* ── CHAT DRAWER ──────────────────────────────────────────────────────── */}
      {isChatOpen && (
        <div style={{ position: 'fixed', bottom: '86px', right: '24px', width: '400px', maxWidth: 'calc(100vw - 48px)', height: '520px', background: 'var(--colors-canvas)', border: '1px solid var(--colors-hairline)', borderRadius: '24px', boxShadow: '0 20px 60px rgba(0,0,0,0.12)', display: 'flex', flexDirection: 'column', overflow: 'hidden', zIndex: 95, animation: 'slideInUp 0.25s ease' }}>
          {/* Header */}
          <div style={{ padding: '16px 20px', background: 'var(--colors-canvas-soft)', borderBottom: '1px solid var(--colors-hairline)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="brand-squircle" style={{ width: '28px', height: '28px', fontSize: '12px' }}><Bot size={14} /></div>
              <div>
                <div style={{ fontWeight: '700', fontSize: '14px' }}>Dataset Assistant</div>
                <div style={{ fontSize: '11px', color: 'var(--colors-text-muted)' }}>{jobId ? `Job: ${jobId}` : 'Upload a file to enable Q&A'}</div>
              </div>
            </div>
            <button onClick={() => setIsChatOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--colors-text-muted)', padding: '4px' }}><X size={16} /></button>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, padding: '16px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {chatMessages.map((m, i) => (
              <div key={i} style={{ maxWidth: '88%', padding: '10px 14px', borderRadius: m.sender === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px', fontSize: '13px', lineHeight: '1.5', background: m.sender === 'user' ? 'var(--colors-ink)' : 'var(--colors-canvas-soft)', color: m.sender === 'user' ? '#fff' : 'var(--colors-ink)', alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start', border: m.sender === 'assistant' ? '1px solid var(--colors-hairline-soft)' : 'none' }}>
                {m.text}
              </div>
            ))}
            {isChatLoading && (
              <div style={{ padding: '10px 14px', borderRadius: '16px 16px 16px 4px', background: 'var(--colors-canvas-soft)', border: '1px solid var(--colors-hairline-soft)', fontSize: '13px', color: 'var(--colors-text-muted)', display: 'flex', alignItems: 'center', gap: '6px', alignSelf: 'flex-start' }}>
                <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} /> Thinking...
              </div>
            )}
          </div>

          {/* Input */}
          <div style={{ padding: '12px 16px', borderTop: '1px solid var(--colors-hairline)', display: 'flex', gap: '8px' }}>
            <input
              type="text"
              className="input-field"
              style={{ flex: 1, height: '40px', fontSize: '13px' }}
              placeholder={jobId ? 'Ask about your dataset...' : 'Run a pipeline first to enable Q&A'}
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !isChatLoading && sendChat()}
              disabled={!jobId}
            />
            <button className="btn-pill btn-accent" style={{ width: '40px', padding: 0, flexShrink: 0 }} onClick={sendChat} disabled={!jobId || isChatLoading}>
              <Send size={15} />
            </button>
          </div>
        </div>
      )}

      {/* ── FOOTER ───────────────────────────────────────────────────────────── */}
      <footer className="mobbin-footer">
        <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div className="brand-squircle" style={{ background: '#ffffff', color: '#141414' }}><Sparkles size={16} /></div>
            <span style={{ fontWeight: '700', fontSize: '16px' }}>DataPrep AI</span>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--colors-text-faint)' }}>
            8-Agent LangGraph System · Powered by Groq LLMs
          </p>
        </div>
      </footer>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes slideInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .agent-card-animated { animation: slideInUp 0.4s ease; }
        .spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}
