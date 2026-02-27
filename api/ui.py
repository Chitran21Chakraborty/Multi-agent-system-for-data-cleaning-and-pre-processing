from fastapi.responses import HTMLResponse
from fastapi import APIRouter

router = APIRouter()

@router.get("/ui", response_class=HTMLResponse)
def get_ui():
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Multi-Agent Preprocessing</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }

body {
    font-family: 'Segoe UI', sans-serif;
    background: #080b12;
    color: #c9d1d9;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

header {
    padding: 18px 40px;
    border-bottom: 1px solid #161b22;
    display: flex;
    align-items: center;
    gap: 14px;
    background: #0d1117;
}

header h1 { font-size: 1.1rem; color: #e6edf3; font-weight: 600; }

.badge {
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    background: #1f2937;
    color: #60a5fa;
    border: 1px solid #1e40af33;
}

.badge.green { color: #34d399; border-color: #065f4633; background: #022c22; }

/* Layout */
.main {
    display: grid;
    grid-template-columns: 380px 1fr;
    gap: 0;
    flex: 1;
    min-height: 0;
}

/* Left panel */
.left {
    background: #0d1117;
    border-right: 1px solid #161b22;
    padding: 28px 24px;
    overflow-y: auto;
}

.left h2 {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #484f58;
    margin-bottom: 20px;
    font-weight: 600;
}

/* Upload form */
.form-section { margin-bottom: 28px; }

.upload-zone {
    border: 1px dashed #30363d;
    border-radius: 8px;
    padding: 28px 16px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    background: #080b12;
    margin-bottom: 12px;
}

.upload-zone:hover { border-color: #58a6ff; background: #0d1f36; }
.upload-zone.has-file { border-color: #238636; background: #0a1f0a; }
.upload-zone .icon { font-size: 1.8rem; display: block; margin-bottom: 8px; }
.upload-zone p { font-size: 0.82rem; color: #484f58; }
.upload-zone .link { color: #58a6ff; }
.file-name { font-size: 0.8rem; color: #3fb950; margin-bottom: 12px; }

input[type="file"] { display: none; }

input[type="text"], textarea {
    width: 100%;
    padding: 10px 14px;
    background: #080b12;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #c9d1d9;
    font-size: 0.85rem;
    outline: none;
    transition: border 0.2s;
    margin-bottom: 10px;
}

input:focus { border-color: #58a6ff; }

.presets {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-bottom: 10px;
}

.preset {
    padding: 7px 10px;
    background: #080b12;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #484f58;
    cursor: pointer;
    font-size: 0.75rem;
    text-align: center;
    transition: all 0.2s;
}

.preset:hover { border-color: #58a6ff; color: #58a6ff; }
.preset.selected { border-color: #58a6ff; color: #58a6ff; background: #0d1f36; }

.run-btn {
    width: 100%;
    padding: 11px;
    background: #238636;
    color: #fff;
    border: 1px solid #2ea043;
    border-radius: 6px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}

.run-btn:hover { background: #2ea043; }
.run-btn:disabled { background: #161b22; border-color: #30363d; color: #484f58; cursor: not-allowed; }

.error-box {
    background: #1a0a0a;
    border: 1px solid #da3633;
    border-radius: 6px;
    padding: 10px 14px;
    color: #f85149;
    font-size: 0.8rem;
    margin-bottom: 10px;
    display: none;
}

/* Pipeline flow */
.pipeline-section { margin-top: 4px; }
.pipeline-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #484f58;
    margin-bottom: 16px;
    font-weight: 600;
}

.pipeline-flow {
    display: flex;
    flex-direction: column;
    gap: 0;
}

.flow-item {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    position: relative;
}

.flow-connector {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex-shrink: 0;
}

.flow-dot {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 2px solid #30363d;
    background: #080b12;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    transition: all 0.4s;
    flex-shrink: 0;
}

.flow-dot.running {
    border-color: #58a6ff;
    background: #0d1f36;
    animation: pulse 1.2s infinite;
}

.flow-dot.done {
    border-color: #238636;
    background: #0a1f0a;
}

.flow-dot.skipped {
    border-color: #484f58;
    background: #080b12;
    opacity: 0.5;
}

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(88,166,255,0.4); }
    50% { box-shadow: 0 0 0 6px rgba(88,166,255,0); }
}

.flow-line {
    width: 2px;
    height: 32px;
    background: #30363d;
    transition: background 0.4s;
}

.flow-line.done { background: #238636; }

.flow-info {
    padding-top: 4px;
    padding-bottom: 32px;
    flex: 1;
}

.flow-name {
    font-size: 0.85rem;
    font-weight: 600;
    color: #484f58;
    transition: color 0.4s;
}

.flow-name.running { color: #58a6ff; }
.flow-name.done { color: #3fb950; }
.flow-name.skipped { color: #484f58; }

.flow-status {
    font-size: 0.72rem;
    color: #484f58;
    margin-top: 2px;
}

.flow-status.running { color: #58a6ff; }
.flow-status.done { color: #3fb950; }

/* Right panel — cards */
.right {
    padding: 28px 32px;
    overflow-y: auto;
    background: #080b12;
}

.right-header {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #484f58;
    margin-bottom: 20px;
    font-weight: 600;
}

.cards-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.agent-card {
    background: #0d1117;
    border: 1px solid #161b22;
    border-radius: 10px;
    padding: 20px 24px;
    animation: slideIn 0.4s ease;
    transition: border-color 0.3s;
}

.agent-card.active { border-color: #1f6feb; }
.agent-card.complete { border-color: #238636; }

@keyframes slideIn {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

.card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
}

.card-icon { font-size: 1.2rem; }

.card-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #e6edf3;
    flex: 1;
}

.card-badge {
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
}

.card-badge.running {
    background: #0d1f36;
    color: #58a6ff;
    border: 1px solid #1f6feb;
}

.card-badge.complete {
    background: #0a1f0a;
    color: #3fb950;
    border: 1px solid #238636;
}

.card-badge.skipped {
    background: #161b22;
    color: #484f58;
    border: 1px solid #30363d;
}

/* Typing animation for running card */
.typing-line {
    font-size: 0.82rem;
    color: #484f58;
    font-style: italic;
}

.typing-dot {
    display: inline-block;
    animation: blink 1s infinite;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
    0%, 80%, 100% { opacity: 0; }
    40% { opacity: 1; }
}

/* Summary table */
.summary-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 12px;
}

.summary-item {
    background: #080b12;
    border: 1px solid #161b22;
    border-radius: 6px;
    padding: 10px 14px;
}

.summary-key {
    font-size: 0.7rem;
    color: #484f58;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

.summary-val {
    font-size: 0.88rem;
    color: #c9d1d9;
    font-weight: 600;
}

.insights-box {
    background: #080b12;
    border: 1px solid #161b22;
    border-radius: 6px;
    padding: 12px 14px;
    font-size: 0.82rem;
    color: #8b949e;
    line-height: 1.6;
    margin-top: 4px;
}

/* Final result card */
.result-card {
    background: #0a1f0a;
    border: 1px solid #238636;
    border-radius: 10px;
    padding: 24px;
    animation: slideIn 0.4s ease;
}

.result-card h3 {
    font-size: 1rem;
    color: #3fb950;
    margin-bottom: 16px;
    font-weight: 700;
}

.dl-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-top: 16px;
}

.dl-btn {
    display: block;
    padding: 12px;
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    text-align: center;
    text-decoration: none;
    color: #c9d1d9;
    font-size: 0.8rem;
    transition: all 0.2s;
}

.dl-btn:hover { border-color: #58a6ff; color: #58a6ff; }
.dl-icon { display: block; font-size: 1.4rem; margin-bottom: 6px; }

.col-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 10px;
}

.col-tag {
    padding: 3px 10px;
    background: #080b12;
    border: 1px solid #30363d;
    border-radius: 20px;
    font-size: 0.72rem;
    color: #8b949e;
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 300px;
    color: #30363d;
    text-align: center;
    gap: 12px;
}

.empty-state .big-icon { font-size: 3rem; }
.empty-state p { font-size: 0.85rem; line-height: 1.6; }
</style>
</head>
<body>

<header>
    <h1>🤖 Multi-Agent Data Preprocessing</h1>
    <span class="badge">LLaMA 3.3 70B</span>
    <span class="badge green">LangGraph</span>
</header>

<div class="main">

    <!-- LEFT PANEL -->
    <div class="left">
        <h2>Configuration</h2>

        <div class="form-section">
            <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()">
                <span class="icon">📂</span>
                <p><span class="link">Click to upload</span> or drag & drop</p>
                <p style="margin-top:4px; font-size:0.75rem;">CSV files only</p>
            </div>
            <input type="file" id="fileInput" accept=".csv" onchange="handleFile(this)">
            <p class="file-name" id="fileName"></p>

            <div class="presets">
                <div class="preset" onclick="setObj(this,'binary classification')">Binary Classification</div>
                <div class="preset" onclick="setObj(this,'multiclass classification')">Multiclass</div>
                <div class="preset" onclick="setObj(this,'regression')">Regression</div>
                <div class="preset" onclick="setObj(this,'clustering')">Clustering</div>
            </div>

            <input type="text" id="objInput" placeholder="Learning objective...">

            <div class="error-box" id="errorBox"></div>

            <button class="run-btn" id="runBtn" onclick="startPipeline()">
                ▶ Run Pipeline
            </button>
        </div>

        <!-- Pipeline flow -->
        <div class="pipeline-section" id="pipelineSection" style="display:none">
            <div class="pipeline-label">Pipeline Flow</div>
            <div class="pipeline-flow" id="pipelineFlow"></div>
        </div>
    </div>

    <!-- RIGHT PANEL -->
    <div class="right">
        <div class="right-header">Agent Output</div>
        <div class="cards-container" id="cardsContainer">
            <div class="empty-state">
                <span class="big-icon">⚡</span>
                <p>Upload a CSV file and set your learning objective.<br>Each agent will report its findings here in real-time.</p>
            </div>
        </div>
    </div>

</div>

<script>
const AGENTS = {
    profiling:      { icon: '🔍', label: 'Data Profiling' },
    imputation:     { icon: '🩹', label: 'Missing Value Imputation' },
    outlier:        { icon: '📊', label: 'Outlier Detection' },
    encoding:       { icon: '🔤', label: 'Categorical Encoding' },
    transformation: { icon: '⚖️', label: 'Feature Transformation' },
    dimensionality: { icon: '📐', label: 'Dimensionality Reduction' },
    sampling:       { icon: '🔁', label: 'Sampling & Balancing' }
};

let selectedFile = null;
let eventSource = null;

// Drag & drop
const zone = document.getElementById('uploadZone');
zone.addEventListener('dragover', e => { e.preventDefault(); zone.style.borderColor = '#58a6ff'; });
zone.addEventListener('dragleave', () => zone.style.borderColor = '');
zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.style.borderColor = '';
    const f = e.dataTransfer.files[0];
    if (f?.name.endsWith('.csv')) setFile(f);
});

function handleFile(input) {
    if (input.files[0]) setFile(input.files[0]);
}

function setFile(f) {
    selectedFile = f;
    document.getElementById('fileName').textContent = '✅ ' + f.name;
    document.getElementById('uploadZone').classList.add('has-file');
}

function setObj(el, text) {
    document.querySelectorAll('.preset').forEach(p => p.classList.remove('selected'));
    el.classList.add('selected');
    document.getElementById('objInput').value = text;
}

function showError(msg) {
    const b = document.getElementById('errorBox');
    b.style.display = 'block';
    b.textContent = '❌ ' + msg;
}

function hideError() {
    document.getElementById('errorBox').style.display = 'none';
}

// Build pipeline flow sidebar
function buildFlow(agents) {
    const flow = document.getElementById('pipelineFlow');
    flow.innerHTML = '';
    document.getElementById('pipelineSection').style.display = 'block';

    agents.forEach((agent, i) => {
        const info = AGENTS[agent] || { icon: '⚙️', label: agent };
        const isLast = i === agents.length - 1;

        flow.innerHTML += `
            <div class="flow-item" id="flow-${agent}">
                <div class="flow-connector">
                    <div class="flow-dot" id="dot-${agent}">${info.icon}</div>
                    ${!isLast ? `<div class="flow-line" id="line-${agent}"></div>` : ''}
                </div>
                <div class="flow-info">
                    <div class="flow-name" id="fname-${agent}">${info.label}</div>
                    <div class="flow-status" id="fstatus-${agent}">Waiting...</div>
                </div>
            </div>
        `;
    });
}

function setFlowRunning(agent) {
    const dot = document.getElementById(`dot-${agent}`);
    const name = document.getElementById(`fname-${agent}`);
    const status = document.getElementById(`fstatus-${agent}`);
    if (dot) dot.classList.add('running');
    if (name) { name.classList.remove('done'); name.classList.add('running'); }
    if (status) { status.textContent = 'Running...'; status.className = 'flow-status running'; }
}

function setFlowDone(agent, skipped=false) {
    const dot = document.getElementById(`dot-${agent}`);
    const name = document.getElementById(`fname-${agent}`);
    const status = document.getElementById(`fstatus-${agent}`);
    const line = document.getElementById(`line-${agent}`);
    if (dot) { dot.classList.remove('running'); dot.classList.add(skipped ? 'skipped' : 'done'); }
    if (name) { name.classList.remove('running'); name.classList.add(skipped ? 'skipped' : 'done'); }
    if (status) {
        status.textContent = skipped ? 'Skipped' : 'Complete';
        status.className = `flow-status ${skipped ? 'skipped' : 'done'}`;
    }
    if (line && !skipped) line.classList.add('done');
}

// Cards
function addRunningCard(agent) {
    const info = AGENTS[agent] || { icon: '⚙️', label: agent };
    const container = document.getElementById('cardsContainer');

    // Remove empty state
    const empty = container.querySelector('.empty-state');
    if (empty) empty.remove();

    const card = document.createElement('div');
    card.className = 'agent-card active';
    card.id = `card-${agent}`;
    card.innerHTML = `
        <div class="card-header">
            <span class="card-icon">${info.icon}</span>
            <span class="card-title">${info.label}</span>
            <span class="card-badge running">Running</span>
        </div>
        <div class="typing-line">
            Analyzing<span class="typing-dot">.</span><span class="typing-dot">.</span><span class="typing-dot">.</span>
        </div>
    `;
    container.appendChild(card);
    card.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

function completeCard(agent, data) {
    const card = document.getElementById(`card-${agent}`);
    if (!card) return;
    const info = AGENTS[agent] || { icon: '⚙️', label: agent };
    const skipped = data.skipped;

    card.className = `agent-card ${skipped ? '' : 'complete'}`;
    card.innerHTML = `
        <div class="card-header">
            <span class="card-icon">${info.icon}</span>
            <span class="card-title">${info.label}</span>
            <span class="card-badge ${skipped ? 'skipped' : 'complete'}">${skipped ? 'Skipped' : 'Complete'}</span>
        </div>
        ${skipped ? `<div class="insights-box">⏭ ${data.reason || 'Not needed for this dataset'}</div>`
                  : buildSummaryHTML(data)}
    `;
}

function buildSummaryHTML(data) {
    const summary = data.summary || {};
    const items = Object.entries(summary).filter(([k]) => k !== 'insights');
    
    let html = '';
    
    if (items.length > 0) {
        html += '<div class="summary-grid">';
        items.forEach(([k, v]) => {
            html += `
                <div class="summary-item">
                    <div class="summary-key">${k.replace(/_/g,' ')}</div>
                    <div class="summary-val">${v}</div>
                </div>`;
        });
        html += '</div>';
    }

    if (summary.insights) {
        html += `<div class="insights-box">💡 ${summary.insights}</div>`;
    }

    if (data.actions && Object.keys(data.actions).length > 0) {
        html += '<div class="insights-box" style="margin-top:8px;"><strong>Actions Taken:</strong><br>';
        Object.entries(data.actions).forEach(([col, action]) => {
            html += `<span style="color:#8b949e">• <strong style="color:#c9d1d9">${col}</strong> → ${action}</span><br>`;
        });
        html += '</div>';
    }

    return html;
}

function showFinalResult(data) {
    const container = document.getElementById('cardsContainer');
    const summary = data.summary || {};
    const orig = summary.original_shape || {};
    const final = summary.final_shape || {};
    const cols = summary.final_columns || [];

    const card = document.createElement('div');
    card.className = 'result-card';
    card.innerHTML = `
        <h3>✅ Preprocessing Complete</h3>
        <div class="summary-grid">
            <div class="summary-item">
                <div class="summary-key">Original Shape</div>
                <div class="summary-val">${orig.rows} × ${orig.columns}</div>
            </div>
            <div class="summary-item">
                <div class="summary-key">Final Shape</div>
                <div class="summary-val">${final.rows} × ${final.columns}</div>
            </div>
        </div>
        <div class="col-tags">
            ${cols.map(c => `<span class="col-tag">${c}</span>`).join('')}
        </div>
        <div class="dl-grid">
            <a href="/download/${data.job_id}/dataset" class="dl-btn">
                <span class="dl-icon">📊</span>Dataset
            </a>
            <a href="/download/${data.job_id}/report" class="dl-btn">
                <span class="dl-icon">📄</span>Report
            </a>
            <a href="/download/${data.job_id}/script" class="dl-btn">
                <span class="dl-icon">🐍</span>Script
            </a>
        </div>
    `;
    container.appendChild(card);
    card.scrollIntoView({ behavior: 'smooth', block: 'end' });
    document.getElementById('runBtn').disabled = false;
}

async function startPipeline() {
    hideError();
    const obj = document.getElementById('objInput').value.trim();
    if (!selectedFile) { showError('Please upload a CSV file'); return; }
    if (!obj) { showError('Please enter a learning objective'); return; }

    document.getElementById('runBtn').disabled = true;
    document.getElementById('cardsContainer').innerHTML = '';

    // Show all agents as waiting first (orchestrator decides which run)
    const allAgents = ['profiling','imputation','outlier','encoding','transformation','dimensionality','sampling'];
    buildFlow(allAgents);

    // Upload file
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('learning_objective', obj);

    let jobId;
    try {
        const res = await fetch('/preprocess/file', { method: 'POST', body: formData });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to start');
        }
        const data = await res.json();
        jobId = data.job_id;
    } catch (err) {
        showError(err.message);
        document.getElementById('runBtn').disabled = false;
        return;
    }

    // Connect SSE
    if (eventSource) eventSource.close();
    eventSource = new EventSource(`/stream/${jobId}`);

    eventSource.addEventListener('agent_start', e => {
        const d = JSON.parse(e.data);
        setFlowRunning(d.agent);
        addRunningCard(d.agent);
    });

    eventSource.addEventListener('agent_done', e => {
        const d = JSON.parse(e.data);
        setFlowDone(d.agent, d.skipped);
        completeCard(d.agent, d);
    });

  

                        eventSource.addEventListener('done', e => {
    const d = JSON.parse(e.data);
    // Mark any still-waiting agents as "Not needed"
    const allAgents = ['profiling','imputation','outlier','encoding',
                       'transformation','dimensionality','sampling'];
    const agentsRun = d.summary?.agents_run || [];
    allAgents.forEach(agent => {
        const status = document.getElementById(`fstatus-${agent}`);
        const name = document.getElementById(`fname-${agent}`);
        if (status && status.textContent === 'Waiting...') {
            status.textContent = 'Not needed';
            status.style.color = '#484f58';
            if (name) name.style.color = '#484f58';
        }
    });
    showFinalResult(d);
    eventSource.close();
});

    eventSource.addEventListener('ping', () => {});
    eventSource.onerror = () => {
        showError('Connection lost. Check server.');
        document.getElementById('runBtn').disabled = false;
    };
}
</script>

</body>
</html>
""")