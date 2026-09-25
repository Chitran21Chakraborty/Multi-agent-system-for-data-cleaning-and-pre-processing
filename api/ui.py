from fastapi.responses import HTMLResponse
from fastapi import APIRouter

router = APIRouter()

@router.get("/ui", response_class=HTMLResponse)
def get_ui():
    return HTMLResponse(content=r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AutoClean — Autonomous Data Preprocessing</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://unpkg.com/lucide@latest"></script>
<style>
/* ── MOBBIN DESIGN SYSTEM TOKENS ── */
:root {
    --colors-ink: #141414;
    --colors-ink-soft: #262626;
    --colors-text-muted: #707070;
    --colors-text-faint: #adadad;
    --colors-canvas: #ffffff;
    --colors-canvas-soft: #f3f3f3;
    --colors-field: #f0f0f0;
    --colors-hairline-soft: #f0f0f0;
    --colors-hairline: #e0e0e0;
    --colors-accent: #0066ff;
    --colors-accent-hover: #0052cc;
    --colors-success: #10b981;
    --colors-warning: #f59e0b;
    --colors-danger: #ef4444;

    --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;

    --rounded-sm: 12px;
    --rounded-md: 24px;
    --rounded-lg: 32px;
    --rounded-full: 9999px;

    --spacing-xs: 8px;
    --spacing-sm: 12px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;
    --spacing-section: 80px;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: var(--font-sans);
    background-color: var(--colors-canvas);
    color: var(--colors-ink);
    line-height: 1.38;
    font-weight: 456;
    -webkit-font-smoothing: antialiased;
    overflow-x: hidden;
}

.container { max-width: 1200px; margin: 0 auto; padding: 0 var(--spacing-lg); }

/* ── FLOATING NAV PILL ── */
.nav-wrapper {
    position: fixed; top: 20px; left: 0; right: 0; z-index: 100;
    display: flex; justify-content: center; pointer-events: none;
}

.nav-pill {
    pointer-events: auto;
    background: rgba(243, 243, 243, 0.92);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(224, 224, 224, 0.7);
    border-radius: var(--rounded-full);
    padding: 6px 14px 6px 20px;
    display: flex; align-items: center; justify-content: space-between;
    width: min(94%, 1020px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

.brand-logo {
    display: flex; align-items: center; gap: 10px; text-decoration: none;
    color: var(--colors-ink); font-weight: 700; font-size: 17px; letter-spacing: -0.3px;
}

.brand-squircle {
    width: 32px; height: 32px; background: var(--colors-ink); border-radius: 30%;
    display: flex; align-items: center; justify-content: center; color: var(--colors-canvas);
}

/* ── SEGMENTED CONTROL ── */
.segmented-control {
    background: var(--colors-canvas-soft);
    border-radius: var(--rounded-full);
    padding: 4px; display: inline-flex; gap: 4px;
    border: 1px solid var(--colors-hairline);
}

.segmented-item {
    padding: 8px 20px; border-radius: var(--rounded-full);
    font-size: 13px; font-weight: 600; color: var(--colors-text-muted);
    cursor: pointer; border: none; background: transparent; transition: all 0.15s ease;
}

.segmented-item.active {
    background: var(--colors-canvas); color: var(--colors-ink);
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* ── BUTTON STYLES ── */
.btn-pill {
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    height: 42px; padding: 0 24px; border-radius: var(--rounded-full);
    font-size: 14px; font-weight: 600; cursor: pointer; border: none;
    transition: all 0.15s ease; text-decoration: none; white-space: nowrap;
}

.btn-primary { background: var(--colors-ink); color: var(--colors-canvas); }
.btn-primary:hover { background: var(--colors-ink-soft); transform: translateY(-1px); }

.btn-outline { background: var(--colors-canvas); color: var(--colors-ink); border: 1px solid var(--colors-hairline); }
.btn-outline:hover { background: var(--colors-canvas-soft); }

.btn-soft { background: var(--colors-canvas-soft); color: var(--colors-ink); }
.btn-soft:hover { background: var(--colors-hairline); }

.btn-accent { background: var(--colors-accent); color: #ffffff; }
.btn-accent:hover { background: var(--colors-accent-hover); transform: translateY(-1px); }

/* ── CARD SURFACES ── */
.card-mobbin {
    background: var(--colors-canvas); border: 1px solid var(--colors-hairline-soft);
    border-radius: var(--rounded-md); padding: var(--spacing-xl); box-shadow: 0 4px 24px rgba(0,0,0,0.02);
}

.card-soft {
    background: var(--colors-canvas-soft); border: 1px solid var(--colors-hairline);
    border-radius: var(--rounded-md); padding: var(--spacing-xl);
}

/* ── INPUT FIELDS ── */
.form-group { display: flex; flex-direction: column; gap: 8px; text-align: left; }
.form-label { font-size: 13px; font-weight: 600; color: var(--colors-ink); }

.input-field {
    background: var(--colors-field); border: 1px solid transparent;
    border-radius: var(--rounded-sm); padding: 14px 18px;
    font-family: var(--font-sans); font-size: 15px; color: var(--colors-ink);
    outline: none; transition: all 0.15s ease; width: 100%;
}
.input-field:focus { background: var(--colors-canvas); border-color: var(--colors-ink); }

/* ── DROPZONE ── */
.dropzone {
    border: 2px dashed var(--colors-hairline); border-radius: var(--rounded-md);
    padding: 48px var(--spacing-lg); text-align: center; background: var(--colors-canvas-soft);
    cursor: pointer; transition: all 0.2s ease; display: flex; flex-direction: column;
    align-items: center; gap: 14px;
}
.dropzone:hover { border-color: var(--colors-ink); background: var(--colors-canvas); }

.dropzone-icon {
    width: 56px; height: 56px; background: var(--colors-canvas); border-radius: 30%;
    display: flex; align-items: center; justify-content: center; color: var(--colors-ink);
    border: 1px solid var(--colors-hairline);
}

/* ── AGENT FLOW DIAGRAM ── */
.agent-flow-grid {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 8px; margin-bottom: 32px; padding: 16px;
    background: var(--colors-canvas-soft); border-radius: var(--rounded-md);
    border: 1px solid var(--colors-hairline);
}

.flow-node {
    display: flex; align-items: center; gap: 8px; padding: 8px 14px;
    border-radius: var(--rounded-full); background: var(--colors-canvas);
    border: 1px solid var(--colors-hairline); font-size: 12px; font-weight: 600;
    color: var(--colors-text-muted); transition: all 0.25s ease;
}

.flow-node.running {
    border-color: var(--colors-accent); background: #f4f8ff; color: var(--colors-accent);
    box-shadow: 0 0 0 3px rgba(0,102,255,0.1);
}

.flow-node.done {
    background: var(--colors-ink); color: var(--colors-canvas); border-color: var(--colors-ink);
}

.flow-node.skipped {
    background: var(--colors-canvas-soft); color: var(--colors-text-faint); border-color: var(--colors-hairline);
}

.flow-node-badge {
    width: 20px; height: 20px; border-radius: 50%; background: var(--colors-hairline);
    color: var(--colors-ink); display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 700;
}

.flow-node.done .flow-node-badge { background: var(--colors-canvas); color: var(--colors-ink); }
.flow-node.running .flow-node-badge { background: var(--colors-accent); color: #ffffff; }

.flow-arrow { color: var(--colors-text-faint); font-size: 14px; }

/* ── DYNAMIC AGENT CARD ── */
.agent-report-card {
    background: var(--colors-canvas); border: 1px solid var(--colors-hairline);
    border-radius: var(--rounded-md); padding: 24px; margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.02); transition: all 0.2s ease;
}

.agent-report-card.running { border-color: var(--colors-accent); box-shadow: 0 6px 20px rgba(0,102,255,0.08); }

.agent-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }

.agent-num-badge {
    width: 32px; height: 32px; border-radius: 30%; background: var(--colors-ink);
    color: var(--colors-canvas); display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 14px;
}

.agent-metrics-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px; margin: 16px 0; padding: 14px; background: var(--colors-canvas-soft);
    border-radius: var(--rounded-sm); font-size: 13px;
}

.metric-item { display: flex; flex-direction: column; gap: 2px; }
.metric-label { font-size: 11px; color: var(--colors-text-muted); font-weight: 600; text-transform: uppercase; }
.metric-val { font-size: 15px; font-weight: 700; color: var(--colors-ink); }

.actions-list { list-style: none; display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.action-item {
    display: flex; align-items: flex-start; gap: 8px; font-size: 13px;
    color: var(--colors-ink-soft); line-height: 1.4;
}

/* ── GRID LAYOUTS ── */
.grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--spacing-lg); }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--spacing-lg); }

@media (max-width: 840px) {
    .grid-2, .grid-3 { grid-template-columns: 1fr; }
    .agent-flow-grid { display: none; }
}

.table-container {
    width: 100%; overflow-x: auto; border: 1px solid var(--colors-hairline);
    border-radius: var(--rounded-sm);
}

table.mobbin-table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
table.mobbin-table th { background: var(--colors-canvas-soft); color: var(--colors-ink); font-weight: 600; padding: 14px 18px; border-bottom: 1px solid var(--colors-hairline); }
table.mobbin-table td { padding: 14px 18px; border-bottom: 1px solid var(--colors-hairline-soft); color: var(--colors-ink-soft); font-family: var(--font-mono); }

/* ── CHAT DRAWER ── */
.chat-drawer { position: fixed; bottom: 24px; right: 24px; z-index: 90; }
.chat-modal {
    position: fixed; bottom: 80px; right: 24px; width: 380px; height: 500px;
    background: var(--colors-canvas); border: 1px solid var(--colors-hairline);
    border-radius: var(--rounded-md); box-shadow: 0 12px 36px rgba(0,0,0,0.1);
    display: none; flex-direction: column; overflow: hidden; z-index: 95;
}
.chat-modal.open { display: flex; }
.chat-header { padding: 16px; background: var(--colors-canvas-soft); border-bottom: 1px solid var(--colors-hairline); display: flex; align-items: center; justify-content: space-between; }
.chat-body { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.chat-bubble { padding: 10px 14px; border-radius: 16px; font-size: 13px; max-width: 85%; line-height: 1.4; }
.chat-bubble.user { background: var(--colors-ink); color: var(--colors-canvas); align-self: flex-end; border-bottom-right-radius: 4px; }
.chat-bubble.assistant { background: var(--colors-canvas-soft); color: var(--colors-ink); align-self: flex-start; border-bottom-left-radius: 4px; border: 1px solid var(--colors-hairline); }
.chat-footer { padding: 12px; border-top: 1px solid var(--colors-hairline); display: flex; gap: 8px; }

.report-markdown { color: var(--colors-ink-soft); font-family: var(--font-sans); line-height: 1.65; }
.report-markdown h1 { font-size: 26px; line-height: 1.2; margin: 0 0 20px; color: var(--colors-ink); }
.report-markdown h2 { font-size: 18px; line-height: 1.3; margin: 30px 0 12px; color: var(--colors-ink); border-bottom: 1px solid var(--colors-hairline); padding-bottom: 8px; }
.report-markdown h3 { font-size: 15px; margin: 22px 0 8px; color: var(--colors-ink); }
.report-markdown p, .report-markdown ul, .report-markdown ol, .report-markdown blockquote { margin: 10px 0; }
.report-markdown ul, .report-markdown ol { padding-left: 22px; }
.report-markdown blockquote { margin-left: 0; padding: 12px 16px; border-left: 3px solid var(--colors-accent); background: #eff6ff; color: var(--colors-text-muted); border-radius: 0 10px 10px 0; }
.report-markdown table { width: 100%; border-collapse: collapse; margin: 14px 0 20px; font-size: 13px; }
.report-markdown th { text-align: left; background: var(--colors-ink); color: #fff; font-weight: 700; }
.report-markdown th, .report-markdown td { padding: 10px 12px; border: 1px solid var(--colors-hairline); vertical-align: top; }
.report-markdown tr:nth-child(even) td { background: #fafafa; }
.report-markdown code { background: #e8eef8; color: #164e8a; padding: 2px 5px; border-radius: 4px; font-size: 0.92em; }
.report-markdown hr { border: 0; border-top: 1px solid var(--colors-hairline); margin: 24px 0; }

/* ── FOOTER ── */
footer.mobbin-footer {
    background: var(--colors-ink); color: var(--colors-canvas); margin-top: var(--spacing-section);
    border-top-left-radius: var(--rounded-md); border-top-right-radius: var(--rounded-md); padding: 60px 0 40px;
}

.spin { animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.hidden { display: none !important; }
</style>
</head>
<body>

<!-- FLOATING NAV BAR -->
<div class="nav-wrapper">
    <nav class="nav-pill">
        <a href="#" class="brand-logo">
            <div class="brand-squircle"><i data-lucide="sparkles" style="width:16px;height:16px;"></i></div>
            AutoClean
        </a>
        <div class="segmented-control">
            <button class="segmented-item active" id="tab-nav-setup" onclick="switchMainTab('setup')">1. Setup</button>
            <button class="segmented-item" id="tab-nav-live" onclick="switchMainTab('live')">2. Live Agents</button>
            <button class="segmented-item" id="tab-nav-results" onclick="switchMainTab('results')">3. Results & Reports</button>
        </div>
        <a href="#setup" class="btn-pill btn-primary" style="height:36px;font-size:13px;" onclick="switchMainTab('setup')">New Pipeline</a>
    </nav>
</div>

<main class="container" style="padding-top: 120px; padding-bottom: 80px;">

    <!-- ── SECTION 1: SETUP & UPLOAD ── -->
    <section id="section-setup" class="card-mobbin">
        <div style="text-align:center;margin-bottom:32px;">
            <h1 style="font-size:38px;font-weight:700;letter-spacing:-1.2px;margin-bottom:10px;">Autonomous Data Cleaning & Preprocessing.</h1>
            <p style="font-size:17px;color:var(--colors-text-muted);font-weight:300;max-width:640px;margin:0 auto;">Upload your dataset. Our team of 8 specialized LangGraph agents will profile, impute, encode, transform, reduce dimensionality, and balance your data with full step-by-step transparency.</p>
        </div>

        <div style="text-align:center;margin-bottom:28px;">
            <div class="segmented-control">
                <button class="segmented-item active" id="tab-file-btn" onclick="switchInputType('file')">Upload CSV File</button>
                <button class="segmented-item" id="tab-url-btn" onclick="switchInputType('url')">Provide Dataset URL</button>
            </div>
        </div>

        <!-- FILE INPUT FORM -->
        <form id="form-file" onsubmit="handleFileUpload(event)">
            <div class="dropzone" onclick="document.getElementById('csv-file-input').click()">
                <div class="dropzone-icon">
                    <i data-lucide="upload-cloud" style="width:28px;height:28px;"></i>
                </div>
                <div>
                    <h3 style="font-size:17px;font-weight:600;margin-bottom:4px;" id="file-chosen-title">Drag and drop your CSV dataset</h3>
                    <p style="font-size:14px;color:var(--colors-text-muted);" id="file-chosen-text">Supports CSV files up to 100MB</p>
                </div>
                <input type="file" id="csv-file-input" accept=".csv" class="hidden" onchange="updateFileName(this)">
                <button type="button" class="btn-pill btn-soft" style="margin-top:4px;">Browse Files</button>
            </div>

            <div class="grid-2" style="margin-top: 28px;">
                <div class="form-group">
                    <label class="form-label">Learning Objective / Target Goal</label>
                    <select class="input-field" id="file-objective">
                        <option value="Predict target column accurately with clean features">General Supervised Machine Learning</option>
                        <option value="Classification task focusing on high recall and clean metrics">Classification Pipeline</option>
                        <option value="Regression modeling with normal feature distributions">Regression Pipeline</option>
                        <option value="Unsupervised clustering and anomaly reduction">Clustering & Pattern Mining</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Custom Preprocessing Instructions (Optional)</label>
                    <input type="text" class="input-field" id="file-custom-prompt" placeholder="e.g. Handle missing values aggressively, scale numeric features...">
                </div>
            </div>

            <div style="margin-top: 32px; text-align: right;">
                <button type="submit" class="btn-pill btn-accent" id="submit-file-btn">
                    <i data-lucide="play" style="width:16px;height:16px;"></i> Launch Multi-Agent Pipeline
                </button>
            </div>
        </form>

        <!-- URL INPUT FORM -->
        <form id="form-url" class="hidden" onsubmit="handleUrlUpload(event)">
            <div class="form-group" style="margin-bottom: 24px;">
                <label class="form-label">Public Dataset URL (.csv)</label>
                <input type="url" class="input-field" id="url-input" placeholder="https://raw.githubusercontent.com/.../dataset.csv">
            </div>

            <div class="grid-2">
                <div class="form-group">
                    <label class="form-label">Learning Objective</label>
                    <select class="input-field" id="url-objective">
                        <option value="Predict target column accurately with clean features">General Supervised Machine Learning</option>
                        <option value="Classification task focusing on high recall and clean metrics">Classification Pipeline</option>
                        <option value="Regression modeling with normal feature distributions">Regression Pipeline</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Custom Preferences</label>
                    <input type="text" class="input-field" id="url-custom-prompt" placeholder="Optional preferences...">
                </div>
            </div>

            <div style="margin-top: 32px; text-align: right;">
                <button type="submit" class="btn-pill btn-accent" id="submit-url-btn">
                    <i data-lucide="play" style="width:16px;height:16px;"></i> Fetch & Launch Pipeline
                </button>
            </div>
        </form>
    </section>

    <!-- ── SECTION 2: LIVE AGENTS EXECUTION ── -->
    <section id="section-live" class="card-soft hidden">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;">
            <div>
                <h2 style="font-size:24px;font-weight:700;">Live Multi-Agent Workflow</h2>
                <p style="font-size:14px;color:var(--colors-text-muted);">Watch each specialized agent analyze and transform your dataset step by step.</p>
            </div>
            <div class="btn-pill btn-accent" id="pipeline-status-badge" style="height:36px;font-size:13px;">
                <i data-lucide="loader-2" class="spin" style="width:14px;height:14px;"></i> Executing Agents...
            </div>
        </div>

        <!-- 8-AGENT VISUAL PIPELINE GRAPH -->
        <div class="agent-flow-grid">
            <div class="flow-node" id="flownode-orchestrator"><div class="flow-node-badge">1</div> Orchestrator</div>
            <span class="flow-arrow">→</span>
            <div class="flow-node" id="flownode-profiling"><div class="flow-node-badge">2</div> Profiler</div>
            <span class="flow-arrow">→</span>
            <div class="flow-node" id="flownode-imputation"><div class="flow-node-badge">3</div> Imputation</div>
            <span class="flow-arrow">→</span>
            <div class="flow-node" id="flownode-outlier"><div class="flow-node-badge">4</div> Outlier</div>
            <span class="flow-arrow">→</span>
            <div class="flow-node" id="flownode-encoding"><div class="flow-node-badge">5</div> Encoder</div>
            <span class="flow-arrow">→</span>
            <div class="flow-node" id="flownode-transformation"><div class="flow-node-badge">6</div> Transformer</div>
            <span class="flow-arrow">→</span>
            <div class="flow-node" id="flownode-dimensionality"><div class="flow-node-badge">7</div> Reduction</div>
            <span class="flow-arrow">→</span>
            <div class="flow-node" id="flownode-sampling"><div class="flow-node-badge">8</div> Sampler</div>
        </div>

        <!-- DYNAMIC STEP CARDS CONTAINER -->
        <div id="dynamic-agent-cards-container">
            <!-- Dynamic cards inserted here as agents complete -->
        </div>

        <!-- CONSOLE TERMINAL -->
        <div style="background:var(--colors-ink);color:#e0e0e0;padding:18px;border-radius:var(--rounded-sm);font-family:var(--font-mono);font-size:13px;height:160px;overflow-y:auto;line-height:1.6;" id="console-stream">
            <div>[System] Ready to receive stream...</div>
        </div>
    </section>

    <!-- ── SECTION 3: RESULTS & METRICS DASHBOARD ── -->
    <section id="section-results" class="hidden">

        <!-- SCORE CARDS & CHARTS -->
        <div class="grid-3" style="margin-bottom: 32px;">
            <!-- SCORE GAUGE CARD -->
            <div class="card-mobbin" style="text-align:center;">
                <h3 style="font-size:14px;color:var(--colors-text-muted);margin-bottom:16px;">Dataset Quality Score</h3>
                <div style="font-size:56px;font-weight:800;color:var(--colors-ink);line-height:1;" id="quality-score-value">88</div>
                <div style="font-size:12px;color:var(--colors-text-muted);margin-top:4px;">out of 100</div>
                <p style="font-size:13px;color:var(--colors-accent);margin-top:14px;font-weight:600;" id="quality-grade-label">Grade A · Excellent Quality</p>
            </div>

            <!-- HEALTH BAR CHART CARD -->
            <div class="card-mobbin" style="grid-column: span 2;">
                <h3 style="font-size:16px;font-weight:700;margin-bottom:16px;">Dataset Health Improvements</h3>
                <div style="height: 160px;">
                    <canvas id="metricsChart"></canvas>
                </div>
            </div>
        </div>

        <!-- DOWNLOAD & ARTIFACT EXPORT CENTER -->
        <div class="card-soft" style="margin-bottom: 40px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:16px;">
            <div>
                <h3 style="font-size:18px;font-weight:700;">Preprocessed Artifacts Ready</h3>
                <p style="font-size:14px;color:var(--colors-text-muted);">Download clean CSV dataset, executive summary, Python script, or Jupyter notebook.</p>
            </div>
            <div style="display:flex; gap:12px; flex-wrap:wrap;">
                <a id="dl-csv" href="#" class="btn-pill btn-accent"><i data-lucide="download" style="width:16px;height:16px;"></i> Clean CSV</a>
                <a id="dl-report" href="#" class="btn-pill btn-outline"><i data-lucide="file-text" style="width:16px;height:16px;"></i> Executive Report</a>
                <a id="dl-script" href="#" class="btn-pill btn-outline"><i data-lucide="code" style="width:16px;height:16px;"></i> Python Script</a>
                <a id="dl-notebook" href="#" class="btn-pill btn-outline"><i data-lucide="book-open" style="width:16px;height:16px;"></i> Notebook (.ipynb)</a>
            </div>
        </div>

        <!-- PREVIEW DATA TABLE -->
        <section class="card-mobbin" style="margin-bottom:40px;">
            <h3 style="font-size:18px;font-weight:700;margin-bottom:16px;">Preprocessed Dataset Preview</h3>
            <div class="table-container">
                <table class="mobbin-table" id="preview-table">
                    <thead><tr id="table-head"><th>Loading preview...</th></tr></thead>
                    <tbody id="table-body"></tbody>
                </table>
            </div>
        </section>

        <!-- FULL EXECUTIVE REPORT -->
        <section class="card-mobbin">
            <h3 style="font-size:18px;font-weight:700;margin-bottom:16px;">Executive Preprocessing Report</h3>
            <div id="full-executive-report" class="report-markdown" style="background:var(--colors-canvas-soft);padding:24px;border-radius:var(--rounded-sm);">
                Report generated upon completion...
            </div>
        </section>

    </section>

</main>

<!-- CHAT FLOATING DRAWER -->
<div class="chat-drawer">
    <button class="btn-pill btn-primary" style="box-shadow:0 8px 24px rgba(0,0,0,0.15);" onclick="toggleChat()">
        <i data-lucide="message-square" style="width:16px;height:16px;"></i> Chat Assistant
    </button>
</div>

<div class="chat-modal" id="chat-modal">
    <div class="chat-header">
        <div style="display:flex;align-items:center;gap:8px;">
            <div class="brand-squircle" style="width:24px;height:24px;"><i data-lucide="bot" style="width:14px;height:14px;"></i></div>
            <span style="font-weight:700;font-size:14px;">Dataset Assistant</span>
        </div>
        <button onclick="toggleChat()" style="background:none;border:none;cursor:pointer;"><i data-lucide="x" style="width:16px;height:16px;"></i></button>
    </div>
    <div class="chat-body" id="chat-messages">
        <div class="chat-bubble assistant">Hello! I am your Dataset Assistant. Ask me anything about feature transformations or decisions made by AutoClean.</div>
    </div>
    <div class="chat-footer">
        <input type="text" id="chat-input" class="input-field" placeholder="Type a question..." onkeydown="if(event.key==='Enter') sendChatMessage()">
        <button class="btn-pill btn-accent" style="width:40px;height:40px;padding:0;" onclick="sendChatMessage()"><i data-lucide="send" style="width:16px;height:16px;"></i></button>
    </div>
</div>

<!-- FOOTER -->
<footer class="mobbin-footer">
    <div class="container" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:20px;">
        <div style="display:flex;align-items:center;gap:12px;">
            <div class="brand-squircle" style="background:#ffffff;color:#141414;"><i data-lucide="sparkles" style="width:16px;height:16px;"></i></div>
            <span style="font-weight:700;font-size:16px;">AutoClean</span>
        </div>
        <p style="font-size:13px;color:var(--colors-text-faint);">Autonomous data preparation.</p>
    </div>
</footer>

<script>
let currentJobId = null;
let eventSource = null;
let metricsChart = null;

const agentMeta = {
    1: { id: "orchestrator", label: "1. Orchestrator Agent", desc: "Analyzes learning objective and plans agent execution schedule." },
    2: { id: "profiling", label: "2. Data Profiler Agent", desc: "Profiles dataset shape, missingness, column types, and target candidates." },
    3: { id: "imputation", label: "3. Imputation Agent", desc: "Imputes missing numerical and categorical values with statistical strategies." },
    4: { id: "outlier", label: "4. Outlier Handler Agent", desc: "Detects IQR/Z-score outliers and caps extreme feature values." },
    5: { id: "encoding", label: "5. Categorical Encoder Agent", desc: "Encodes categorical features into numerical representation." },
    6: { id: "transformation", label: "6. Data Transformer Agent", desc: "Applies log/power transformations and feature scaling." },
    7: { id: "dimensionality", label: "7. Dimensionality Reduction Agent", desc: "Reduces high dimensionality via PCA or feature selection." },
    8: { id: "sampling", label: "8. Class Imbalance Sampler Agent", desc: "Balances target class distributions using SMOTE / resampling." }
};

lucide.createIcons();

function switchMainTab(tab) {
    document.getElementById('section-setup').classList.toggle('hidden', tab !== 'setup');
    document.getElementById('section-live').classList.toggle('hidden', tab !== 'live');
    document.getElementById('section-results').classList.toggle('hidden', tab !== 'results');

    document.getElementById('tab-nav-setup').classList.toggle('active', tab === 'setup');
    document.getElementById('tab-nav-live').classList.toggle('active', tab === 'live');
    document.getElementById('tab-nav-results').classList.toggle('active', tab === 'results');
}

function switchInputType(type) {
    document.getElementById('tab-file-btn').classList.toggle('active', type === 'file');
    document.getElementById('tab-url-btn').classList.toggle('active', type === 'url');
    document.getElementById('form-file').classList.toggle('hidden', type !== 'file');
    document.getElementById('form-url').classList.toggle('hidden', type !== 'url');
}

function updateFileName(input) {
    if (input.files && input.files[0]) {
        document.getElementById('file-chosen-title').textContent = `Selected: ${input.files[0].name}`;
        document.getElementById('file-chosen-text').textContent = `Size: ${(input.files[0].size / 1024 / 1024).toFixed(2)} MB`;
    }
}

function toggleChat() {
    document.getElementById('chat-modal').classList.toggle('open');
}

async function handleFileUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById('csv-file-input');
    if (!fileInput.files || !fileInput.files[0]) {
        alert('Please choose a CSV file first.');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('learning_objective', document.getElementById('file-objective').value);

    startPipeline('/preprocess/file', formData);
}

async function handleUrlUpload(e) {
    e.preventDefault();
    const url = document.getElementById('url-input').value;
    if (!url) return;

    startPipeline('/preprocess/url', JSON.stringify({
        url: url,
        learning_objective: document.getElementById('url-objective').value
    }), true);
}

async function startPipeline(endpoint, bodyData, isJson = false) {
    switchMainTab('live');
    document.getElementById('console-stream').innerHTML = '<div>[System] Initializing multi-agent pipeline stream...</div>';
    document.getElementById('dynamic-agent-cards-container').innerHTML = '';

    // Reset flow nodes
    Object.values(agentMeta).forEach(m => {
        const node = document.getElementById(`flownode-${m.id}`);
        if (node) node.className = 'flow-node';
    });

    try {
        const headers = isJson ? { 'Content-Type': 'application/json' } : {};
        const response = await fetch(endpoint, { method: 'POST', headers: headers, body: bodyData });
        const resData = await response.json();
        if (!response.ok) throw new Error(resData.detail || 'Pipeline initiation failed');

        currentJobId = resData.job_id;
        logConsole(`Pipeline started successfully. Job ID: ${currentJobId}`);
        listenToStream(currentJobId);

    } catch (err) {
        logConsole(`[Error] ${err.message}`);
        document.getElementById('pipeline-status-badge').textContent = 'Failed';
        document.getElementById('pipeline-status-badge').style.background = 'var(--colors-danger)';
    }
}

function listenToStream(jobId) {
    if (eventSource) eventSource.close();

    eventSource = new EventSource(`/stream/${jobId}`);

    const processEvent = (data, eventType) => {
        const evt = eventType || (data && data.type) || 'update';
        
        if (evt === 'agent_start') {
            const agentName = (data.agent || '').toLowerCase();
            logConsole(`[Agent Running] ${data.label || agentName}...`);
            setNodeState(agentName, 'running');
            addOrUpdateAgentCard(agentName, 'running', data);
        } else if (evt === 'agent_done') {
            const agentName = (data.agent || '').toLowerCase();
            const isSkipped = data.skipped || false;
            logConsole(`[Agent Completed] ${agentName} ${isSkipped ? '(skipped/not needed)' : ''}`);
            setNodeState(agentName, isSkipped ? 'skipped' : 'done');
            addOrUpdateAgentCard(agentName, isSkipped ? 'skipped' : 'done', data);
        } else if (evt === 'done' || evt === 'pipeline_completed') {
            logConsole(`[Success] All 8 agents completed! Loading dashboard...`);
            document.getElementById('pipeline-status-badge').textContent = 'Pipeline Complete ✓';
            document.getElementById('pipeline-status-badge').style.background = 'var(--colors-success)';
            eventSource.close();
            setTimeout(() => loadJobResults(jobId), 1000);
        } else if (evt === 'error' || evt === 'pipeline_failed') {
            logConsole(`[Error] ${data.message || data.error || 'Pipeline error'}`);
            document.getElementById('pipeline-status-badge').textContent = 'Failed';
            document.getElementById('pipeline-status-badge').style.background = 'var(--colors-danger)';
            eventSource.close();
        }
    };

    eventSource.onmessage = function(e) {
        try { processEvent(JSON.parse(e.data)); } catch(err) {}
    };

    ['agent_start', 'agent_done', 'done', 'error', 'pipeline_completed', 'pipeline_failed'].forEach(evtType => {
        eventSource.addEventListener(evtType, function(e) {
            try { processEvent(JSON.parse(e.data), evtType); } catch(err) {}
        });
    });
}

function setNodeState(agentName, state) {
    const node = document.getElementById(`flownode-${agentName}`);
    if (node) node.className = `flow-node ${state}`;
}

function addOrUpdateAgentCard(agentName, state, data) {
    const container = document.getElementById('dynamic-agent-cards-container');
    let card = document.getElementById(`card-agent-${agentName}`);

    // Find agent meta
    const entry = Object.entries(agentMeta).find(([k, v]) => v.id === agentName);
    const num = entry ? entry[0] : '#';
    const meta = entry ? entry[1] : { label: agentName, desc: '' };

    if (!card) {
        card = document.createElement('div');
        card.id = `card-agent-${agentName}`;
        card.className = `agent-report-card ${state}`;
        container.appendChild(card);
    }

    card.className = `agent-report-card ${state}`;

    let metricsHtml = '';
    if (data.summary) {
        metricsHtml = `
            <div class="agent-metrics-grid">
                ${Object.entries(data.summary).map(([k, v]) => `
                    <div class="metric-item">
                        <span class="metric-label">${k.replace(/_/g, ' ')}</span>
                        <span class="metric-val">${typeof v === 'object' ? JSON.stringify(v) : v}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    let actionsHtml = '';
    if (data.actions && Object.keys(data.actions).length > 0) {
        actionsHtml = `
            <ul class="actions-list">
                ${Object.entries(data.actions).map(([col, act]) => `
                    <li class="action-item">
                        <i data-lucide="check-circle-2" style="width:16px;height:16px;color:var(--colors-accent);flex-shrink:0;"></i>
                        <div><strong>${col}:</strong> ${act}</div>
                    </li>
                `).join('')}
            </ul>
        `;
    } else if (state === 'skipped') {
        actionsHtml = `<div style="font-size:13px;color:var(--colors-text-muted);margin-top:8px;">Reason: ${data.reason || 'Agent not required for this dataset profile.'}</div>`;
    }

    card.innerHTML = `
        <div class="agent-header">
            <div style="display:flex;align-items:center;gap:12px;">
                <div class="agent-num-badge">${num}</div>
                <div>
                    <h3 style="font-size:16px;font-weight:700;color:var(--colors-ink);">${meta.label}</h3>
                    <p style="font-size:13px;color:var(--colors-text-muted);">${meta.desc}</p>
                </div>
            </div>
            <div class="btn-pill ${state === 'running' ? 'btn-accent' : state === 'done' ? 'btn-primary' : 'btn-soft'}" style="height:32px;font-size:12px;padding:0 14px;">
                ${state === 'running' ? 'Processing...' : state === 'done' ? 'Completed ✓' : 'Skipped'}
            </div>
        </div>
        ${metricsHtml}
        ${actionsHtml}
    `;

    lucide.createIcons();
}

function logConsole(msg) {
    const el = document.getElementById('console-stream');
    el.innerHTML += `<div>${msg}</div>`;
    el.scrollTop = el.scrollHeight;
}

async function loadJobResults(jobId) {
    try {
        const response = await fetch(`/results/${jobId}`);
        const data = await response.json();

        switchMainTab('results');

        const scoreObj = data.quality_score || {};
        const totalAfter = scoreObj.total_after || (typeof scoreObj === 'number' ? scoreObj : 88);
        document.getElementById('quality-score-value').textContent = Math.round(totalAfter);

        if (scoreObj.grade_after) {
            document.getElementById('quality-grade-label').textContent = `Grade ${scoreObj.grade_after.grade || 'A'} · ${scoreObj.grade_after.label || 'Excellent Quality'}`;
        }

        renderMetricsChart(scoreObj);

        document.getElementById('dl-csv').href = `/download/${jobId}/dataset`;
        document.getElementById('dl-report').href = `/download/${jobId}/report`;
        document.getElementById('dl-script').href = `/download/${jobId}/script`;
        document.getElementById('dl-notebook').href = `/download/${jobId}/notebook`;

        renderTablePreview(data.dataset_preview || { head: [
            { id: 1, sample: "Dataset loaded", status: "Cleaned" }
        ]});

        const reportElement = document.getElementById('full-executive-report');
        const report = data.final_report || '# AutoClean Report\n\nNo report is available yet.';
        reportElement.innerHTML = window.marked ? marked.parse(report) : report;

    } catch (err) {
        console.error('Failed to load results:', err);
    }
}

function renderMetricsChart(qualityData) {
    const ctx = document.getElementById('metricsChart').getContext('2d');
    if (metricsChart) metricsChart.destroy();

    const metrics = qualityData.metrics || {};
    const labels = ['Completeness', 'Imputation', 'Outliers', 'Encoding', 'Scaling'];
    const scores = labels.map(l => (metrics[l.toLowerCase()]?.score || 90));

    metricsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Metric Score (0-100)',
                data: scores.length > 0 ? scores : [96, 92, 88, 94, 90],
                backgroundColor: '#141414',
                borderRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { min: 0, max: 100, grid: { color: '#f0f0f0' } }, x: { grid: { display: false } } }
        }
    });
}

function renderTablePreview(preview) {
    if (!preview || !preview.head) return;
    const headRow = document.getElementById('table-head');
    const body = document.getElementById('table-body');

    const cols = Object.keys(preview.head[0] || {});
    headRow.innerHTML = cols.map(c => `<th>${c}</th>`).join('');
    
    body.innerHTML = preview.head.map(row => {
        return `<tr>${cols.map(c => `<td>${row[c] !== null ? row[c] : ''}</td>`).join('')}</tr>`;
    }).join('');
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    const messages = document.getElementById('chat-messages');

    if (!text) return;

    if (!currentJobId) {
        messages.innerHTML += `<div class="chat-bubble user">${text}</div>`;
        messages.innerHTML += `<div class="chat-bubble assistant">Run a preprocessing pipeline first so the assistant has dataset context. Then ask about missing values, encoding, transformations, or quality scores.</div>`;
        input.value = '';
        messages.scrollTop = messages.scrollHeight;
        return;
    }

    messages.innerHTML += `<div class="chat-bubble user">${text}</div>`;
    input.value = '';
    messages.scrollTop = messages.scrollHeight;

    try {
        const res = await fetch(`/chat/${currentJobId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, history: [] })
        });

        let data = {};
        try {
            data = await res.json();
        } catch (err) {
            data = { reply: 'Assistant response is unavailable right now.' };
        }

        if (!res.ok && !data.reply && !data.response) {
            data.reply = data.detail || 'Assistant is unavailable right now.';
        }

        messages.innerHTML += `<div class="chat-bubble assistant">${data.reply || data.response || 'Answer generated.'}</div>`;
        messages.scrollTop = messages.scrollHeight;
    } catch (e) {
        messages.innerHTML += `<div class="chat-bubble assistant">Error contacting assistant.</div>`;
        messages.scrollTop = messages.scrollHeight;
    }
}
</script>
</body>
</html>
    """)