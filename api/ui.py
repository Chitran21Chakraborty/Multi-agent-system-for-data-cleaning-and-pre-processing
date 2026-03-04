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
<title>Multi-Agent Preprocessing</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
:root {
    --bg:       #060810;
    --bg2:      #0b0f1a;
    --bg3:      #0f1420;
    --border:   #1a2035;
    --border2:  #252d45;
    --text:     #c8d0e0;
    --muted:    #4a5570;
    --blue:     #4d9fff;
    --green:    #00d68f;
    --amber:    #ffb74d;
    --red:      #ff5252;
    --purple:   #b388ff;
}

* { margin:0; padding:0; box-sizing:border-box; }

body {
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(77,159,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(77,159,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

/* ── HEADER ──────────────────────────────────────────────── */
header {
    position: relative;
    z-index: 10;
    padding: 14px 32px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 16px;
    background: rgba(11,15,26,0.95);
    backdrop-filter: blur(12px);
}
.logo { display: flex; align-items: center; gap: 10px; }
.logo-icon {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, #4d9fff, #b388ff);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
}
header h1 { font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; color: #e8edf8; font-weight: 600; letter-spacing: -0.3px; }
.badges { display: flex; gap: 8px; margin-left: 4px; }
.badge { padding: 3px 10px; border-radius: 4px; font-size: 0.65rem; font-weight: 600; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.3px; }
.badge-blue   { background: rgba(77,159,255,0.1);  color: #4d9fff;  border: 1px solid rgba(77,159,255,0.2); }
.badge-green  { background: rgba(0,214,143,0.1);   color: #00d68f;  border: 1px solid rgba(0,214,143,0.2); }
.badge-purple { background: rgba(179,136,255,0.1); color: #b388ff;  border: 1px solid rgba(179,136,255,0.2); }
.header-right { margin-left: auto; display: flex; align-items: center; gap: 12px; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); box-shadow: 0 0 6px var(--green); animation: blink-dot 2s infinite; }
@keyframes blink-dot { 0%,100%{opacity:1} 50%{opacity:0.3} }
.status-text { font-size: 0.7rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; }

/* ── LAYOUT ──────────────────────────────────────────────── */
.main { display: grid; grid-template-columns: 320px 1fr; flex: 1; height: calc(100vh - 57px); position: relative; z-index: 1; }

/* ── LEFT PANEL ──────────────────────────────────────────── */
.left {
    background: var(--bg2);
    border-right: 1px solid var(--border);
    padding: 20px 16px;
    overflow-y: scroll;
    overflow-x: hidden;
    display: flex;
    flex-direction: column;
    gap: 18px;
    height: calc(100vh - 57px);
    overscroll-behavior: contain;
}
.left::-webkit-scrollbar { width: 4px; }
.left::-webkit-scrollbar-track { background: transparent; }
.left::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

.section-label { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 2.5px; color: var(--muted); font-weight: 700; font-family: 'JetBrains Mono', monospace; margin-bottom: 8px; }

.upload-label {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    border: 1px dashed var(--border2); border-radius: 10px; padding: 20px 12px;
    text-align: center; cursor: pointer; transition: all 0.25s; background: var(--bg);
    gap: 8px; position: relative; overflow: hidden;
}
.upload-label::before { content: ''; position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 0%, rgba(77,159,255,0.06), transparent 70%); opacity: 0; transition: opacity 0.3s; }
.upload-label:hover::before { opacity: 1; }
.upload-label:hover { border-color: var(--blue); }
.upload-label.has-file { border-color: var(--green); border-style: solid; background: rgba(0,214,143,0.04); }
.upload-label.has-file::before { background: radial-gradient(ellipse at 50% 0%, rgba(0,214,143,0.06), transparent 70%); opacity: 1; }
.upload-icon { font-size: 1.8rem; }
.upload-label p { font-size: 0.75rem; color: var(--muted); }
.upload-label .link { color: var(--blue); font-weight: 600; }
.upload-label.has-file .link { color: var(--green); }

.file-chip { display: none; align-items: center; gap: 6px; background: rgba(0,214,143,0.08); border: 1px solid rgba(0,214,143,0.2); border-radius: 6px; padding: 6px 10px; font-size: 0.72rem; color: var(--green); font-family: 'JetBrains Mono', monospace; }
.file-chip.show { display: flex; }
.file-chip-icon { font-size: 0.9rem; }

.presets { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin-bottom: 8px; }
.preset { padding: 7px 6px; background: var(--bg); border: 1px solid var(--border2); border-radius: 6px; color: var(--muted); cursor: pointer; font-size: 0.7rem; text-align: center; transition: all 0.2s; font-weight: 500; }
.preset:hover { border-color: var(--blue); color: var(--blue); background: rgba(77,159,255,0.05); }
.preset.selected { border-color: var(--blue); color: var(--blue); background: rgba(77,159,255,0.08); }

.obj-input { width: 100%; padding: 9px 12px; background: var(--bg); border: 1px solid var(--border2); border-radius: 6px; color: var(--text); font-size: 0.8rem; outline: none; transition: border 0.2s; font-family: 'Inter', sans-serif; }
.obj-input:focus { border-color: var(--blue); }
.obj-input::placeholder { color: var(--muted); }

.error-box { background: rgba(255,82,82,0.08); border: 1px solid rgba(255,82,82,0.3); border-radius: 6px; padding: 9px 12px; color: #ff5252; font-size: 0.75rem; display: none; font-family: 'JetBrains Mono', monospace; }

.run-btn { width: 100%; padding: 11px; background: linear-gradient(135deg, #1a6b3a, #238636); color: #fff; border: 1px solid rgba(46,160,67,0.5); border-radius: 8px; font-size: 0.85rem; font-weight: 700; cursor: pointer; transition: all 0.2s; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.5px; position: relative; overflow: hidden; }
.run-btn::after { content: ''; position: absolute; inset: 0; background: linear-gradient(135deg, rgba(255,255,255,0.05), transparent); }
.run-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(35,134,54,0.3); }
.run-btn:disabled { background: var(--border); border-color: var(--border); color: var(--muted); cursor: not-allowed; transform: none; box-shadow: none; }

/* ── PIPELINE FLOW SIDEBAR ───────────────────────────────── */
.pipeline-flow { display: flex; flex-direction: column; }
.flow-item { display: flex; align-items: flex-start; gap: 10px; }
.flow-connector { display: flex; flex-direction: column; align-items: center; flex-shrink: 0; }
.flow-dot { width: 24px; height: 24px; border-radius: 50%; border: 1.5px solid var(--border2); background: var(--bg); display: flex; align-items: center; justify-content: center; font-size: 0.7rem; transition: all 0.4s; flex-shrink: 0; }
.flow-dot.running { border-color: var(--blue); background: rgba(77,159,255,0.1); animation: flow-pulse 1.5s infinite; }
.flow-dot.done    { border-color: var(--green); background: rgba(0,214,143,0.1); }
.flow-dot.skipped { border-color: var(--border2); opacity: 0.35; }
@keyframes flow-pulse { 0%,100%{ box-shadow: 0 0 0 0 rgba(77,159,255,0.4); } 50%{ box-shadow: 0 0 0 5px rgba(77,159,255,0); } }
.flow-line { width: 1.5px; height: 24px; background: var(--border2); transition: background 0.6s; }
.flow-line.done { background: var(--green); }
.flow-info { padding-top: 2px; padding-bottom: 24px; flex: 1; }
.flow-name { font-size: 0.78rem; font-weight: 600; color: var(--muted); transition: color 0.4s; }
.flow-name.running { color: var(--blue); }
.flow-name.done    { color: var(--green); }
.flow-status { font-size: 0.64rem; color: var(--muted); margin-top: 1px; font-family: 'JetBrains Mono', monospace; }
.flow-status.running { color: var(--blue); }
.flow-status.done    { color: var(--green); }

/* ── RIGHT PANEL ─────────────────────────────────────────── */
.right { padding: 22px 26px; overflow-y: scroll; background: var(--bg); height: calc(100vh - 57px); overscroll-behavior: contain; -webkit-overflow-scrolling: touch; }
.right::-webkit-scrollbar { width: 4px; }
.right::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }
.right-header { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 2.5px; color: var(--muted); margin-bottom: 16px; font-weight: 700; font-family: 'JetBrains Mono', monospace; display: flex; align-items: center; gap: 8px; }
.right-header::after { content: ''; flex: 1; height: 1px; background: var(--border); }
.cards-container { display: flex; flex-direction: column; gap: 12px; }

/* ── CARDS ───────────────────────────────────────────────── */
.agent-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; padding: 16px 20px; animation: slideUp 0.3s ease; transition: border-color 0.3s, box-shadow 0.3s; position: relative; overflow: hidden; }
.agent-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, rgba(77,159,255,0.3), transparent); opacity: 0; transition: opacity 0.3s; }
.agent-card.active { border-color: rgba(77,159,255,0.4); box-shadow: 0 0 20px rgba(77,159,255,0.05); }
.agent-card.active::before { opacity: 1; }
.agent-card.complete { border-color: rgba(0,214,143,0.25); }
.agent-card.complete::before { background: linear-gradient(90deg, transparent, rgba(0,214,143,0.2), transparent); opacity: 1; }
@keyframes slideUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.card-icon-wrap { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 0.95rem; flex-shrink: 0; }
.icon-blue   { background: rgba(77,159,255,0.1);  border: 1px solid rgba(77,159,255,0.2); }
.icon-green  { background: rgba(0,214,143,0.1);   border: 1px solid rgba(0,214,143,0.2); }
.icon-purple { background: rgba(179,136,255,0.1); border: 1px solid rgba(179,136,255,0.2); }
.icon-amber  { background: rgba(255,183,77,0.1);  border: 1px solid rgba(255,183,77,0.2); }
.card-title { font-size: 0.88rem; font-weight: 600; color: #e8edf8; flex: 1; }
.card-badge { padding: 2px 9px; border-radius: 4px; font-size: 0.62rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.3px; }
.badge-running  { background: rgba(77,159,255,0.1);  color: var(--blue);  border: 1px solid rgba(77,159,255,0.25); }
.badge-complete { background: rgba(0,214,143,0.1);   color: var(--green); border: 1px solid rgba(0,214,143,0.25); }
.badge-skipped  { background: rgba(74,85,112,0.2);   color: var(--muted); border: 1px solid var(--border2); }

.typing-line { font-size: 0.78rem; color: var(--muted); font-style: italic; display: flex; align-items: center; gap: 2px; }
.typing-dot { display: inline-block; animation: blink 1.2s infinite; width: 4px; height: 4px; border-radius: 50%; background: var(--blue); margin: 0 1px; }
.typing-dot:nth-child(2){ animation-delay: 0.2s; }
.typing-dot:nth-child(3){ animation-delay: 0.4s; }
@keyframes blink { 0%,80%,100%{opacity:0.2} 40%{opacity:1} }

.summary-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 7px; margin-bottom: 10px; }
.summary-item { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 9px 11px; }
.summary-key { font-size: 0.6rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px; font-family: 'JetBrains Mono', monospace; }
.summary-val { font-size: 0.85rem; color: #e8edf8; font-weight: 700; font-family: 'JetBrains Mono', monospace; }

.insights-box { background: var(--bg); border: 1px solid var(--border); border-left: 2px solid var(--blue); border-radius: 6px; padding: 10px 14px; font-size: 0.77rem; color: #8895b0; line-height: 1.7; margin-top: 8px; }
.actions-box { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; margin-top: 8px; }
.actions-title { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 1.5px; color: var(--muted); font-family: 'JetBrains Mono', monospace; font-weight: 700; margin-bottom: 8px; }
.action-row { display: flex; align-items: center; gap: 8px; padding: 5px 0; border-bottom: 1px solid var(--border); font-size: 0.74rem; }
.action-row:last-child { border-bottom: none; }
.action-col   { color: #e8edf8; font-family: 'JetBrains Mono', monospace; font-weight: 600; min-width: 80px; }
.action-arrow { color: var(--muted); font-size: 0.7rem; }
.action-val   { color: #8895b0; }

/* ── CHARTS ──────────────────────────────────────────────── */
.chart-section { margin-top: 12px; }
.chart-title { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 1.5px; color: var(--muted); font-family: 'JetBrains Mono', monospace; font-weight: 700; margin-bottom: 8px; }
.charts-row { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }
.chart-wrap { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 10px; }
.chart-col-name { font-size: 0.65rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; margin-bottom: 6px; text-align: center; }
.chart-canvas-wrap { position: relative; height: 90px; }
.chart-legend { display: flex; gap: 10px; justify-content: center; margin-top: 6px; }
.legend-item { display: flex; align-items: center; gap: 4px; font-size: 0.6rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; }
.legend-dot { width: 7px; height: 7px; border-radius: 2px; }

/* ── HEATMAP ─────────────────────────────────────────────── */
.heatmap-grid { display: flex; flex-direction: column; gap: 2px; }
.heatmap-row  { display: flex; gap: 2px; align-items: center; }
.heatmap-label { font-size: 0.55rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; width: 60px; text-align: right; padding-right: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.heatmap-cell { width: 22px; height: 22px; border-radius: 3px; display: flex; align-items: center; justify-content: center; font-size: 0.45rem; font-family: 'JetBrains Mono', monospace; cursor: default; transition: transform 0.2s; }
.heatmap-cell:hover { transform: scale(1.3); z-index: 10; }
.heatmap-col-labels { display: flex; gap: 2px; padding-left: 64px; margin-bottom: 2px; }
.heatmap-col-label { width: 22px; font-size: 0.5rem; color: var(--muted); text-align: center; font-family: 'JetBrains Mono', monospace; writing-mode: vertical-lr; transform: rotate(180deg); height: 42px; overflow: hidden; }

/* ── FLOW DIAGRAM ────────────────────────────────────────── */
.flow-diagram { display: none; background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; padding: 16px 20px; margin-bottom: 14px; overflow-x: auto; flex-shrink: 0; }
.flow-diagram.show { display: block; }
.flow-diagram-title { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 2px; color: var(--muted); font-family: 'JetBrains Mono', monospace; font-weight: 700; margin-bottom: 14px; }
.flow-nodes { display: flex; align-items: center; overflow-x: auto; padding-bottom: 4px; }
.flow-node { display: flex; flex-direction: column; align-items: center; gap: 6px; flex-shrink: 0; }
.flow-node-box { width: 68px; padding: 7px 6px; border-radius: 8px; border: 1.5px solid var(--border2); background: var(--bg); text-align: center; transition: all 0.4s; }
.flow-node-box.node-running { border-color: var(--blue); background: rgba(77,159,255,0.08); box-shadow: 0 0 12px rgba(77,159,255,0.15); }
.flow-node-box.node-done    { border-color: var(--green); background: rgba(0,214,143,0.06); }
.flow-node-box.node-skipped { opacity: 0.35; }
.flow-node-icon  { font-size: 1rem; }
.flow-node-label { font-size: 0.58rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; margin-top: 2px; }
.flow-node-box.node-running .flow-node-label { color: var(--blue); }
.flow-node-box.node-done    .flow-node-label { color: var(--green); }
.flow-node-status { font-size: 0.55rem; font-family: 'JetBrains Mono', monospace; color: var(--muted); height: 14px; }
.node-status-running { color: var(--blue); animation: blink-dot 1s infinite; }
.node-status-done    { color: var(--green); }
.flow-edge { width: 28px; height: 2px; background: var(--border2); position: relative; flex-shrink: 0; transition: background 0.5s; margin-top: -20px; }
.flow-edge.edge-done { background: var(--green); }
.flow-edge::after { content: ''; position: absolute; right: -4px; top: -3px; width: 0; height: 0; border-top: 4px solid transparent; border-bottom: 4px solid transparent; border-left: 5px solid var(--border2); transition: border-color 0.5s; }
.flow-edge.edge-done::after { border-left-color: var(--green); }
.flow-edge.edge-running { background: linear-gradient(90deg, var(--green) 0%, var(--blue) 50%, transparent 100%); background-size: 200% 100%; animation: data-flow 0.8s linear infinite; }
@keyframes data-flow { 0%{ background-position: -100% 0 } 100%{ background-position: 100% 0 } }

/* ── QUALITY SCORE ───────────────────────────────────────── */
.quality-card { background: var(--bg2); border-radius: 14px; padding: 20px; animation: slideUp 0.35s ease; position: relative; overflow: hidden; }
.quality-card::before { content: ''; position: absolute; inset: 0; background: radial-gradient(ellipse at 100% 0%, rgba(0,214,143,0.04), transparent 60%); pointer-events: none; }
.quality-scores { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
.qs-box { flex: 1; background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 14px; text-align: center; }
.qs-box.qs-after { border-width: 2px; }
.qs-label  { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 1.5px; color: var(--muted); font-family: 'JetBrains Mono', monospace; margin-bottom: 8px; }
.qs-number { font-size: 2.8rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; line-height: 1; }
.qs-grade  { font-size: 0.72rem; margin-top: 6px; font-weight: 600; }
.qs-arrow  { font-size: 1.4rem; color: var(--muted); flex-shrink: 0; }
.qs-dims { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.qs-dim-row { display: flex; align-items: center; padding: 9px 14px; border-bottom: 1px solid var(--border); gap: 10px; transition: background 0.2s; }
.qs-dim-row:last-child { border-bottom: none; }
.qs-dim-row:hover { background: rgba(255,255,255,0.01); }
.qs-dim-label  { font-size: 0.78rem; color: #8895b0; flex: 1; }
.qs-dim-bar-wrap { width: 100px; height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; }
.qs-dim-bar    { height: 100%; border-radius: 2px; transition: width 1s ease; }
.qs-dim-scores { display: flex; align-items: center; gap: 6px; min-width: 110px; justify-content: flex-end; }
.qs-dim-before { font-size: 0.68rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; }
.qs-dim-arr    { font-size: 0.65rem; color: var(--muted); }
.qs-dim-after  { font-size: 0.78rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.qs-dim-detail { font-size: 0.64rem; color: var(--muted); min-width: 160px; text-align: right; }

/* ── FINAL RESULT CARD ───────────────────────────────────── */
.result-card { background: linear-gradient(135deg, rgba(0,214,143,0.04), rgba(0,214,143,0.01)); border: 1px solid rgba(0,214,143,0.25); border-radius: 14px; padding: 20px; animation: slideUp 0.35s ease; }
.result-card h3 { font-size: 0.88rem; color: var(--green); margin-bottom: 14px; font-weight: 700; display: flex; align-items: center; gap: 8px; }
.dl-grid { display: grid; gap: 8px; margin-top: 12px; }
.dl-btn { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 12px 8px; background: var(--bg2); border: 1px solid var(--border2); border-radius: 10px; text-decoration: none; color: var(--text); font-size: 0.72rem; transition: all 0.2s; font-weight: 500; }
.dl-btn:hover { border-color: var(--blue); color: var(--blue); background: rgba(77,159,255,0.05); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(77,159,255,0.1); }
.dl-icon { font-size: 1.4rem; }
.col-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 10px; max-height: 80px; overflow-y: auto; }
.col-tag { padding: 2px 8px; background: var(--bg); border: 1px solid var(--border); border-radius: 4px; font-size: 0.62rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; }

/* ── EMPTY STATE ─────────────────────────────────────────── */
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 55vh; gap: 16px; text-align: center; }
.empty-icon-wrap { width: 64px; height: 64px; background: linear-gradient(135deg, rgba(77,159,255,0.1), rgba(179,136,255,0.1)); border: 1px solid rgba(77,159,255,0.15); border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; }
.empty-state h3 { font-size: 0.9rem; color: #4a5570; font-weight: 600; }
.empty-state p  { font-size: 0.78rem; color: #2e3650; line-height: 1.7; max-width: 320px; }

/* ── CHAT FAB ────────────────────────────────────────────── */
.chat-fab {
    display: none;
    position: fixed;
    bottom: 28px;
    right: 28px;
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4d9fff, #b388ff);
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(77,159,255,0.35);
    z-index: 900;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    transition: all 0.3s;
}
.chat-fab.show { display: flex; animation: fab-in 0.4s ease; }
.chat-fab:hover { transform: scale(1.1); box-shadow: 0 6px 28px rgba(77,159,255,0.5); }
@keyframes fab-in { from { opacity: 0; transform: scale(0.5) rotate(-20deg); } to { opacity: 1; transform: scale(1) rotate(0deg); } }

.fab-badge {
    position: absolute;
    top: -3px; right: -3px;
    width: 16px; height: 16px;
    border-radius: 50%;
    background: #00d68f;
    border: 2px solid #060810;
    font-size: 0.5rem;
    display: none;
    align-items: center;
    justify-content: center;
    color: #060810;
    font-weight: 800;
}
.fab-badge.show { display: flex; }

/* ── CHAT PANEL ──────────────────────────────────────────── */
.chat-panel {
    display: none;
    position: fixed;
    bottom: 90px;
    right: 28px;
    width: 380px;
    height: 520px;
    background: #0b0f1a;
    border: 1px solid #1a2035;
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.6);
    z-index: 900;
    flex-direction: column;
    overflow: hidden;
}
.chat-panel.show { display: flex; animation: chat-slide-in 0.3s ease; }
@keyframes chat-slide-in { from { opacity: 0; transform: translateY(20px) scale(0.97); } to { opacity: 1; transform: translateY(0) scale(1); } }

.chat-header { padding: 14px 16px; border-bottom: 1px solid #1a2035; display: flex; align-items: center; gap: 10px; background: #0b0f1a; flex-shrink: 0; }
.chat-header-icon { width: 30px; height: 30px; border-radius: 8px; background: linear-gradient(135deg, rgba(77,159,255,0.2), rgba(179,136,255,0.2)); border: 1px solid rgba(77,159,255,0.2); display: flex; align-items: center; justify-content: center; font-size: 0.9rem; }
.chat-header-info { flex: 1; }
.chat-header-title { font-size: 0.82rem; font-weight: 700; color: #e8edf8; }
.chat-header-sub   { font-size: 0.62rem; color: #4a5570; font-family: 'JetBrains Mono', monospace; }
.chat-close { background: none; border: none; color: #4a5570; cursor: pointer; font-size: 1rem; padding: 4px; transition: color 0.2s; }
.chat-close:hover { color: #e8edf8; }

.chat-messages { flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 10px; }
.chat-messages::-webkit-scrollbar { width: 3px; }
.chat-messages::-webkit-scrollbar-thumb { background: #1a2035; border-radius: 2px; }

.chat-suggestions { display: flex; flex-wrap: wrap; gap: 6px; padding: 0 14px 10px; flex-shrink: 0; }
.suggestion-chip { padding: 5px 10px; background: #060810; border: 1px solid #1a2035; border-radius: 20px; font-size: 0.65rem; color: #4a5570; cursor: pointer; transition: all 0.2s; font-family: 'JetBrains Mono', monospace; white-space: nowrap; }
.suggestion-chip:hover { border-color: #4d9fff; color: #4d9fff; background: rgba(77,159,255,0.05); }

.chat-msg { display: flex; gap: 8px; animation: msg-in 0.25s ease; }
@keyframes msg-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
.chat-msg.user { flex-direction: row-reverse; }

.chat-avatar { width: 26px; height: 26px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; flex-shrink: 0; }
.avatar-ai   { background: rgba(77,159,255,0.1); border: 1px solid rgba(77,159,255,0.2); }
.avatar-user { background: rgba(0,214,143,0.1);  border: 1px solid rgba(0,214,143,0.2); }

.chat-bubble { max-width: 78%; padding: 9px 12px; border-radius: 10px; font-size: 0.76rem; line-height: 1.6; }
.bubble-ai   { background: #0f1420; border: 1px solid #1a2035; color: #c8d0e0; border-radius: 10px 10px 10px 2px; }
.bubble-user { background: rgba(0,214,143,0.08); border: 1px solid rgba(0,214,143,0.15); color: #e8edf8; border-radius: 10px 10px 2px 10px; }

.chat-typing { display: flex; gap: 8px; align-items: flex-end; }
.typing-bubble { background: #0f1420; border: 1px solid #1a2035; border-radius: 10px 10px 10px 2px; padding: 10px 14px; display: flex; gap: 4px; align-items: center; }
.typing-bubble span { width: 5px; height: 5px; border-radius: 50%; background: #4a5570; animation: typing-bounce 1.2s infinite; }
.typing-bubble span:nth-child(2) { animation-delay: 0.2s; }
.typing-bubble span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing-bounce { 0%,80%,100% { transform: translateY(0); background: #4a5570; } 40% { transform: translateY(-5px); background: #4d9fff; } }

.chat-input-wrap { padding: 12px 14px; border-top: 1px solid #1a2035; display: flex; gap: 8px; flex-shrink: 0; background: #0b0f1a; }
.chat-input { flex: 1; background: #060810; border: 1px solid #1a2035; border-radius: 8px; padding: 8px 12px; color: #c8d0e0; font-size: 0.76rem; font-family: 'Inter', sans-serif; outline: none; resize: none; height: 36px; max-height: 100px; transition: border 0.2s; overflow-y: hidden; }
.chat-input:focus { border-color: #4d9fff; }
.chat-input::placeholder { color: #2a3350; }
.chat-send { width: 36px; height: 36px; border-radius: 8px; background: linear-gradient(135deg, #1a6b3a, #238636); border: 1px solid rgba(46,160,67,0.4); color: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; transition: all 0.2s; flex-shrink: 0; }
.chat-send:hover { transform: scale(1.05); box-shadow: 0 2px 12px rgba(35,134,54,0.3); }
.chat-send:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

.chat-bubble code { background: #060810; border: 1px solid #1a2035; border-radius: 4px; padding: 1px 5px; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #4d9fff; }
.chat-bubble pre  { background: #060810; border: 1px solid #1a2035; border-radius: 6px; padding: 8px; margin: 6px 0; overflow-x: auto; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #00d68f; }
</style>
</head>
<body>

<header>
    <div class="logo">
        <div class="logo-icon">🤖</div>
        <h1>DataPrep · MultiAgent</h1>
    </div>
    <div class="badges">
        <span class="badge badge-blue">LLaMA 3.3 · 70B</span>
        <span class="badge badge-green">LangGraph</span>
    </div>
    <div class="header-right">
        <div class="status-dot"></div>
        <span class="status-text">SYSTEM READY</span>
    </div>
</header>

<div class="main">

    <!-- LEFT -->
    <div class="left">
        <div>
            <div class="section-label">Dataset Input</div>
            <label for="fileInput" class="upload-label" id="uploadZone">
                <span class="upload-icon">📂</span>
                <p><span class="link">Click to upload</span> or drag & drop</p>
                <p style="font-size:0.68rem; margin-top:2px;">CSV files supported</p>
            </label>
            <input type="file" id="fileInput" accept=".csv" style="display:none" onchange="handleFile(this)">
            <div class="file-chip" id="fileChip">
                <span class="file-chip-icon">📄</span>
                <span id="fileName">—</span>
            </div>
        </div>

        <div>
            <div class="section-label">Learning Objective</div>
            <div class="presets">
                <div class="preset" onclick="setObj(this,'binary classification')">Binary Class.</div>
                <div class="preset" onclick="setObj(this,'multiclass classification')">Multiclass</div>
                <div class="preset" onclick="setObj(this,'regression')">Regression</div>
                <div class="preset" onclick="setObj(this,'clustering')">Clustering</div>
            </div>
            <input type="text" class="obj-input" id="objInput" placeholder="Or type custom objective...">
        </div>

        <div>
            <div class="error-box" id="errorBox"></div>
            <button class="run-btn" id="runBtn" onclick="startPipeline()">
                ▶ &nbsp;RUN PIPELINE
            </button>
        </div>

        <div id="pipelineSection" style="display:none">
            <div class="section-label">Pipeline Flow</div>
            <div class="pipeline-flow" id="pipelineFlow"></div>
        </div>
    </div>

    <!-- RIGHT -->
    <div class="right">
        <div class="right-header">Agent Output Stream</div>
        <div class="flow-diagram" id="flowDiagram">
            <div class="flow-diagram-title">Execution Pipeline</div>
            <div class="flow-nodes" id="flowNodes"></div>
        </div>
        <div class="cards-container" id="cardsContainer">
            <div class="empty-state">
                <div class="empty-icon-wrap">⚡</div>
                <h3>Ready to Preprocess</h3>
                <p>Upload a CSV file and select a learning objective. Each agent will stream its analysis and decisions here in real-time.</p>
            </div>
        </div>
    </div>
</div>

<!-- FLOATING CHAT BUTTON -->
<button class="chat-fab" id="chatFab" onclick="toggleChat()">
    💬
    <span class="fab-badge" id="fabBadge"></span>
</button>

<!-- CHAT PANEL -->
<div class="chat-panel" id="chatPanel">
    <div class="chat-header">
        <div class="chat-header-icon">🤖</div>
        <div class="chat-header-info">
            <div class="chat-header-title">Ask about your data</div>
            <div class="chat-header-sub" id="chatHeaderSub">Powered by LLaMA 3.3 · Free</div>
        </div>
        <button class="chat-close" onclick="toggleChat()">✕</button>
    </div>
    <div class="chat-messages" id="chatMessages">
        <div class="chat-msg">
            <div class="chat-avatar avatar-ai">🤖</div>
            <div class="chat-bubble bubble-ai">
                Hi! I have full context about your dataset and preprocessing pipeline. Ask me anything!
            </div>
        </div>
    </div>
    <div class="chat-suggestions" id="chatSuggestions">
        <span class="suggestion-chip" onclick="sendSuggestion(this)">Why was this scaler chosen?</span>
        <span class="suggestion-chip" onclick="sendSuggestion(this)">Which features matter most?</span>
        <span class="suggestion-chip" onclick="sendSuggestion(this)">Is my data ready for ML?</span>
        <span class="suggestion-chip" onclick="sendSuggestion(this)">Explain the quality score</span>
    </div>
    <div class="chat-input-wrap">
        <textarea class="chat-input" id="chatInput"
            placeholder="Ask about your dataset..."
            onkeydown="handleChatKey(event)"
            oninput="autoResize(this)"></textarea>
        <button class="chat-send" id="chatSend" onclick="sendChatMessage()">➤</button>
    </div>
</div>

<script>
const AGENTS = {
    orchestrator:   { icon: '🧠', label: 'Orchestrator',  color: 'purple' },
    profiling:      { icon: '🔍', label: 'Profiling',     color: 'blue'   },
    imputation:     { icon: '🩹', label: 'Imputation',    color: 'amber'  },
    outlier:        { icon: '📊', label: 'Outlier',       color: 'red'    },
    encoding:       { icon: '🔤', label: 'Encoding',      color: 'blue'   },
    transformation: { icon: '⚖️', label: 'Transform',    color: 'green'  },
    dimensionality: { icon: '📐', label: 'Dimension',     color: 'purple' },
    sampling:       { icon: '🔁', label: 'Sampling',      color: 'amber'  }
};

let selectedFile = null;
let eventSource  = null;
let agentOrder   = [];
const chartInstances = {};

// ── DRAG & DROP ───────────────────────────────────────────────────────────────
const zone = document.getElementById('uploadZone');
zone.addEventListener('dragover', e => { e.preventDefault(); zone.style.borderColor = 'var(--blue)'; });
zone.addEventListener('dragleave', () => zone.style.borderColor = '');
zone.addEventListener('drop', e => {
    e.preventDefault(); zone.style.borderColor = '';
    const f = e.dataTransfer.files[0];
    if (f?.name.endsWith('.csv')) setFile(f);
});

function handleFile(input) { if (input.files[0]) setFile(input.files[0]); }

function setFile(f) {
    selectedFile = f;
    document.getElementById('fileName').textContent = f.name;
    document.getElementById('fileChip').classList.add('show');
    zone.classList.add('has-file');
    zone.querySelector('.upload-icon').textContent = '✅';
    zone.querySelector('.link').textContent = 'File selected';
}

function setObj(el, text) {
    document.querySelectorAll('.preset').forEach(p => p.classList.remove('selected'));
    el.classList.add('selected');
    document.getElementById('objInput').value = text;
}

function showError(msg) {
    const b = document.getElementById('errorBox');
    b.style.display = 'block';
    b.textContent = '// ERROR: ' + msg;
}
function hideError() { document.getElementById('errorBox').style.display = 'none'; }

// ── FLOW DIAGRAM ──────────────────────────────────────────────────────────────
function buildFlowDiagram(agents) {
    const wrap  = document.getElementById('flowDiagram');
    const nodes = document.getElementById('flowNodes');
    wrap.classList.add('show');
    nodes.innerHTML = '';
    agents.forEach((agent, i) => {
        const info = AGENTS[agent] || { icon: '⚙️', label: agent };
        if (i > 0) {
            const edge = document.createElement('div');
            edge.className = 'flow-edge';
            edge.id = `edge-${agents[i-1]}`;
            nodes.appendChild(edge);
        }
        const node = document.createElement('div');
        node.className = 'flow-node';
        node.id = `fnode-${agent}`;
        node.innerHTML = `
            <div class="flow-node-box" id="fnbox-${agent}">
                <div class="flow-node-icon">${info.icon}</div>
                <div class="flow-node-label">${info.label}</div>
            </div>
            <div class="flow-node-status" id="fnstatus-${agent}">—</div>`;
        nodes.appendChild(node);
    });
}

function setDiagramRunning(agent, agents) {
    const box    = document.getElementById(`fnbox-${agent}`);
    const status = document.getElementById(`fnstatus-${agent}`);
    const idx    = agents.indexOf(agent);
    if (box)    box.classList.add('node-running');
    if (status) { status.textContent = '●'; status.className = 'flow-node-status node-status-running'; }
    if (idx > 0) {
        const e = document.getElementById(`edge-${agents[idx-1]}`);
        if (e) e.classList.add('edge-running');
    }
}

function setDiagramDone(agent, agents, skipped=false) {
    const box    = document.getElementById(`fnbox-${agent}`);
    const status = document.getElementById(`fnstatus-${agent}`);
    const idx    = agents.indexOf(agent);
    if (box)    { box.classList.remove('node-running'); box.classList.add(skipped ? 'node-skipped' : 'node-done'); }
    if (status) { status.textContent = skipped ? '—' : '✓'; status.className = `flow-node-status ${skipped ? '' : 'node-status-done'}`; }
    if (idx > 0) {
        const e = document.getElementById(`edge-${agents[idx-1]}`);
        if (e) { e.classList.remove('edge-running'); if (!skipped) e.classList.add('edge-done'); }
    }
}

// ── SIDEBAR FLOW ──────────────────────────────────────────────────────────────
function buildFlow(agents) {
    agentOrder = agents;
    const flow = document.getElementById('pipelineFlow');
    flow.innerHTML = '';
    document.getElementById('pipelineSection').style.display = 'block';
    agents.forEach((agent, i) => {
        const info   = AGENTS[agent] || { icon: '⚙️', label: agent };
        const isLast = i === agents.length - 1;
        flow.innerHTML += `
            <div class="flow-item" id="flow-${agent}">
                <div class="flow-connector">
                    <div class="flow-dot" id="dot-${agent}">${info.icon}</div>
                    ${!isLast ? `<div class="flow-line" id="line-${agent}"></div>` : ''}
                </div>
                <div class="flow-info">
                    <div class="flow-name" id="fname-${agent}">${info.label}</div>
                    <div class="flow-status" id="fstatus-${agent}">waiting</div>
                </div>
            </div>`;
    });
    buildFlowDiagram(agents);
}

function setFlowRunning(agent) {
    ['dot','fname','fstatus'].forEach(id => {
        const el = document.getElementById(`${id}-${agent}`);
        if (!el) return;
        el.classList.remove('done','skipped');
        el.classList.add('running');
        if (id === 'fstatus') el.textContent = 'running...';
    });
    setDiagramRunning(agent, agentOrder);
}

function setFlowDone(agent, skipped=false) {
    ['dot','fname','fstatus'].forEach(id => {
        const el = document.getElementById(`${id}-${agent}`);
        if (!el) return;
        el.classList.remove('running');
        if (!skipped) el.classList.add('done');
        if (id === 'fstatus') el.textContent = skipped ? 'skipped' : 'done ✓';
    });
    const line = document.getElementById(`line-${agent}`);
    if (line && !skipped) line.classList.add('done');
    setDiagramDone(agent, agentOrder, skipped);
}

// ── CARDS ────────────────────────────────────────────────────────────────────
function addRunningCard(agent) {
    const info      = AGENTS[agent] || { icon: '⚙️', label: agent, color: 'blue' };
    const container = document.getElementById('cardsContainer');
    container.querySelector('.empty-state')?.remove();
    const card      = document.createElement('div');
    card.className  = 'agent-card active';
    card.id         = `card-${agent}`;
    card.innerHTML  = `
        <div class="card-header">
            <div class="card-icon-wrap icon-${info.color}">${info.icon}</div>
            <span class="card-title">${info.label || agent}</span>
            <span class="card-badge badge-running">RUNNING</span>
        </div>
        <div class="typing-line">
            Analyzing
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>`;
    container.appendChild(card);
    card.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

function completeCard(agent, data) {
    const card = document.getElementById(`card-${agent}`);
    if (!card) return;
    const info    = AGENTS[agent] || { icon: '⚙️', label: agent, color: 'blue' };
    const skipped = data.skipped;
    card.className = `agent-card ${skipped ? '' : 'complete'}`;
    card.innerHTML = `
        <div class="card-header">
            <div class="card-icon-wrap icon-${info.color}">${info.icon}</div>
            <span class="card-title">${info.label || agent}</span>
            <span class="card-badge ${skipped ? 'badge-skipped' : 'badge-complete'}">
                ${skipped ? 'SKIPPED' : 'COMPLETE'}
            </span>
        </div>
        ${skipped
            ? `<div class="insights-box">⏭ ${data.reason || 'Not needed for this dataset'}</div>`
            : buildCardBody(agent, data)}`;
    if (!skipped) setTimeout(() => renderCharts(agent, data), 200);
}

function buildCardBody(agent, data) {
    const summary = data.summary || {};
    const items   = Object.entries(summary).filter(([k]) => k !== 'insights');
    let html = '';

    if (items.length > 0) {
        html += '<div class="summary-grid">';
        items.forEach(([k, v]) => {
            html += `<div class="summary-item">
                <div class="summary-key">${k.replace(/_/g,' ')}</div>
                <div class="summary-val">${v}</div>
            </div>`;
        });
        html += '</div>';
    }

    if (data.actions && Object.keys(data.actions).length > 0) {
        html += `<div class="actions-box"><div class="actions-title">Actions Taken</div>`;
        Object.entries(data.actions).forEach(([col, action]) => {
            html += `<div class="action-row">
                <span class="action-col">${col}</span>
                <span class="action-arrow">→</span>
                <span class="action-val">${action}</span>
            </div>`;
        });
        html += '</div>';
    }

    if (summary.insights) html += `<div class="insights-box">💡 ${summary.insights}</div>`;

    if (['imputation','outlier','transformation','encoding'].includes(agent)) {
        html += `<div class="chart-section" id="charts-${agent}">
            <div class="chart-title">Distribution View</div>
            <div class="charts-row" id="chart-row-${agent}"></div>
            <div class="chart-legend">
                <div class="legend-item"><div class="legend-dot" style="background:rgba(77,159,255,0.5)"></div>Before</div>
                <div class="legend-item"><div class="legend-dot" style="background:rgba(0,214,143,0.6)"></div>After</div>
            </div>
        </div>`;
    }

    if (agent === 'profiling') {
        html += `<div class="chart-section" id="heatmap-profiling">
            <div class="chart-title">Feature Correlation Heatmap</div>
            <div id="heatmap-grid"></div>
        </div>`;
    }

    return html;
}

// ── CHARTS ───────────────────────────────────────────────────────────────────
function renderCharts(agent, data) {
    if (agent === 'profiling') { renderHeatmap(data); return; }
    const dists = data.distributions;
    if (!dists || !dists.before || !dists.after) { renderSimulated(agent, data); return; }
    const row  = document.getElementById(`chart-row-${agent}`);
    if (!row) return;
    const cols = Object.keys(dists.before).slice(0, 4);
    if (cols.length === 0) { renderSimulated(agent, data); return; }

    cols.forEach(col => {
        const before = dists.before[col] || { labels: [], values: [] };
        const after  = dists.after[col]  || { labels: [], values: [] };
        const len    = Math.max(before.values.length, after.values.length);
        const bVals  = before.values.concat(Array(Math.max(0, len - before.values.length)).fill(0));
        const aVals  = after.values.concat(Array(Math.max(0, len - after.values.length)).fill(0));
        const labels = before.labels.length ? before.labels : after.labels;

        const wrap = document.createElement('div');
        wrap.className = 'chart-wrap';
        wrap.innerHTML = `
            <div class="chart-col-name">${col}</div>
            <div class="chart-canvas-wrap">
                <canvas id="chart-${agent}-${col.replace(/[\s().]/g,'_')}"></canvas>
            </div>`;
        row.appendChild(wrap);

        const key = `${agent}-${col}`;
        if (chartInstances[key]) chartInstances[key].destroy();
        chartInstances[key] = new Chart(wrap.querySelector('canvas').getContext('2d'), {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    { label: 'Before', data: bVals, backgroundColor: 'rgba(77,159,255,0.45)', borderColor: 'rgba(77,159,255,0.8)', borderWidth: 1, borderRadius: 2 },
                    { label: 'After',  data: aVals, backgroundColor: 'rgba(0,214,143,0.5)',   borderColor: 'rgba(0,214,143,0.9)',  borderWidth: 1, borderRadius: 2 }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                animation: { duration: 900, easing: 'easeOutQuart' },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0b0f1a', borderColor: '#1a2035', borderWidth: 1,
                        titleColor: '#c8d0e0', bodyColor: '#4a5570',
                        titleFont: { family: 'JetBrains Mono', size: 10 },
                        bodyFont:  { family: 'JetBrains Mono', size: 10 },
                        callbacks: {
                            title: items => `bin: ${items[0].label}`,
                            label: item  => ` ${item.dataset.label}: ${(item.raw * 100).toFixed(1)}%`
                        }
                    }
                },
                scales: { x: { display: false }, y: { display: false } }
            }
        });
    });
}

function renderSimulated(agent, data) {
    const actions = data.actions || {};
    const cols    = Object.keys(actions).slice(0, 4);
    const row     = document.getElementById(`chart-row-${agent}`);
    if (!row || cols.length === 0) return;

    cols.forEach(col => {
        const wrap = document.createElement('div');
        wrap.className = 'chart-wrap';
        wrap.innerHTML = `
            <div class="chart-col-name">${col} <span style="font-size:0.55rem;color:var(--muted)">(simulated)</span></div>
            <div class="chart-canvas-wrap">
                <canvas id="chart-${agent}-${col.replace(/[\s().]/g,'_')}"></canvas>
            </div>`;
        row.appendChild(wrap);

        const key = `${agent}-${col}`;
        if (chartInstances[key]) chartInstances[key].destroy();
        const { before, after } = generateDistData(agent, col, actions[col]);
        chartInstances[key] = new Chart(wrap.querySelector('canvas').getContext('2d'), {
            type: 'bar',
            data: {
                labels: before.labels,
                datasets: [
                    { label: 'Before', data: before.values, backgroundColor: 'rgba(77,159,255,0.45)', borderColor: 'rgba(77,159,255,0.8)', borderWidth: 1, borderRadius: 2 },
                    { label: 'After',  data: after.values,  backgroundColor: 'rgba(0,214,143,0.5)',   borderColor: 'rgba(0,214,143,0.9)',  borderWidth: 1, borderRadius: 2 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, animation: { duration: 800 }, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } } }
        });
    });
}

function generateDistData(agent, col, action) {
    const n      = 10;
    const labels = Array.from({length: n}, (_, i) => `b${i}`);
    function bell(center, spread, skew=0) {
        return Array.from({length: n}, (_, i) => {
            const x = (i - center) / spread;
            return Math.max(0, Math.exp(-0.5*x*x) + skew*Math.max(0,x)*0.3 + (Math.random()-0.5)*0.1);
        });
    }
    let before, after;
    if (agent === 'outlier')         { before = { labels, values: bell(3,1.5,1.5) }; after = { labels, values: bell(5,2.2,0) }; }
    else if (agent === 'imputation') { const bv = bell(5,2,0); bv[2]=0; bv[3]=0; before = { labels, values: bv }; after = { labels, values: bell(5,2,0) }; }
    else if (agent === 'transformation') {
        before = { labels, values: action?.includes('Log') ? bell(2,1,2) : bell(3,1.2,0) };
        after  = { labels, values: bell(5,2.5,0) };
    } else { before = { labels, values: bell(4,1.5,0) }; after = { labels, values: bell(5,2,0) }; }
    const maxB = Math.max(...before.values)||1;
    const maxA = Math.max(...after.values)||1;
    before.values = before.values.map(v=>v/maxB);
    after.values  = after.values.map(v=>v/maxA);
    return { before, after };
}

function renderHeatmap(data) {
    const grid = document.getElementById('heatmap-grid');
    if (!grid) return;
    const numCols = data.summary?.numerical || data.summary?.numerical_cols || 6;
    const n       = Math.min(parseInt(numCols)||6, 7);
    if (n < 2) { grid.innerHTML = '<div style="color:var(--muted);font-size:0.72rem;">Not enough numerical columns</div>'; return; }
    const cols   = Array.from({length: n}, (_, i) => `col${i+1}`);
    const matrix = Array.from({length: n}, (_, i) => Array.from({length: n}, (_, j) => i===j ? 1.0 : Math.max(-1, Math.min(1, Math.random()*1.6-0.8))));
    function corrColor(v) {
        if (v >= 0.7)  return `rgba(0,214,143,${0.3+v*0.6})`;
        if (v >= 0.3)  return `rgba(0,214,143,${0.1+v*0.3})`;
        if (v <= -0.7) return `rgba(255,82,82,${0.3+Math.abs(v)*0.6})`;
        if (v <= -0.3) return `rgba(255,82,82,${0.1+Math.abs(v)*0.3})`;
        return `rgba(74,85,112,0.15)`;
    }
    let html = '<div class="heatmap-col-labels">';
    cols.forEach(c => { html += `<div class="heatmap-col-label">${c}</div>`; });
    html += '</div>';
    const heatDiv = document.createElement('div');
    heatDiv.className = 'heatmap-grid';
    matrix.forEach((row, i) => {
        let r = `<div class="heatmap-row"><div class="heatmap-label">${cols[i]}</div>`;
        row.forEach(v => { r += `<div class="heatmap-cell" style="background:${corrColor(v)}" title="${v.toFixed(2)}">${Math.abs(v)>=0.5?v.toFixed(1):''}</div>`; });
        r += '</div>';
        heatDiv.innerHTML += r;
    });
    grid.innerHTML = html;
    grid.appendChild(heatDiv);
    const legend = document.createElement('div');
    legend.style.cssText = 'display:flex;gap:12px;margin-top:8px;align-items:center;';
    legend.innerHTML = `<span style="font-size:0.6rem;color:var(--muted);font-family:JetBrains Mono,monospace;">Correlation:</span>
        <div style="display:flex;align-items:center;gap:4px;">
            <div style="width:40px;height:6px;background:linear-gradient(90deg,rgba(255,82,82,0.8),rgba(74,85,112,0.2),rgba(0,214,143,0.8));border-radius:3px;"></div>
            <span style="font-size:0.58rem;color:var(--muted);font-family:JetBrains Mono,monospace;">-1 → +1</span>
        </div>`;
    grid.appendChild(legend);
}

// ── QUALITY SCORE + FINAL RESULT ──────────────────────────────────────────────
function showFinalResult(data) {
    const container = document.getElementById('cardsContainer');
    const summary   = data.summary || {};
    const orig      = summary.original_shape || {};
    const fin       = summary.final_shape    || {};
    const cols      = summary.final_columns  || [];
    const qs        = data.quality_score     || {};
    const dims      = qs.dimensions          || {};

    // Quality Score card
    const scoreCard = document.createElement('div');
    scoreCard.className = 'quality-card';
    scoreCard.style.border = `1px solid ${qs.grade_after?.color ? qs.grade_after.color+'44' : 'rgba(0,214,143,0.25)'}`;
    const beforeColor = qs.grade_before?.color || '#4a5570';
    const afterColor  = qs.grade_after?.color  || '#00d68f';
    const dimRows = Object.values(dims).map(d => {
        const pct   = (d.after / d.max) * 100;
        const color = d.after >= d.before ? 'var(--green)' : 'var(--red)';
        return `<div class="qs-dim-row">
            <span class="qs-dim-label">${d.label}</span>
            <div class="qs-dim-bar-wrap"><div class="qs-dim-bar" style="width:${pct}%;background:${color}"></div></div>
            <div class="qs-dim-scores">
                <span class="qs-dim-before">${d.before}/${d.max}</span>
                <span class="qs-dim-arr">→</span>
                <span class="qs-dim-after" style="color:${color}">${d.after}/${d.max}</span>
            </div>
            <span class="qs-dim-detail">${d.detail}</span>
        </div>`;
    }).join('');

    scoreCard.innerHTML = `
        <div class="card-header" style="margin-bottom:16px;">
            <div class="card-icon-wrap icon-green">🏆</div>
            <span class="card-title">Data Quality Score</span>
            <span class="card-badge badge-complete">COMPLETE</span>
        </div>
        <div class="quality-scores">
            <div class="qs-box">
                <div class="qs-label">Before</div>
                <div class="qs-number" style="color:${beforeColor}">${qs.total_before ?? '—'}</div>
                <div class="qs-grade"  style="color:${beforeColor}">${qs.grade_before?.label || ''}</div>
            </div>
            <div class="qs-arrow">→</div>
            <div class="qs-box qs-after" style="border-color:${afterColor}">
                <div class="qs-label">After</div>
                <div class="qs-number" style="color:${afterColor}">${qs.total_after ?? '—'}</div>
                <div class="qs-grade"  style="color:${afterColor}">
                    ${qs.grade_after?.label || ''}
                    ${qs.improvement > 0 ? `<span style="margin-left:4px;">(+${qs.improvement})</span>` : ''}
                </div>
            </div>
        </div>
        <div class="qs-dims">${dimRows}</div>`;
    container.appendChild(scoreCard);

    // Final result card
    const resultCard    = document.createElement('div');
    resultCard.className = 'result-card';
    const visibleCols   = cols.slice(0, 12);
    const extraCols     = cols.length - visibleCols.length;

    resultCard.innerHTML = `
        <h3>✅ Preprocessing Complete</h3>
        <div class="summary-grid">
            <div class="summary-item">
                <div class="summary-key">Original Shape</div>
                <div class="summary-val">${orig.rows ?? '?'} × ${orig.columns ?? '?'}</div>
            </div>
            <div class="summary-item">
                <div class="summary-key">Final Shape</div>
                <div class="summary-val">${fin.rows ?? '?'} × ${fin.columns ?? '?'}</div>
            </div>
        </div>
        <div class="col-tags">
            ${visibleCols.map(c => `<span class="col-tag">${c}</span>`).join('')}
            ${extraCols > 0 ? `<span class="col-tag" style="color:var(--blue);border-color:var(--blue)">+${extraCols} more</span>` : ''}
        </div>
        <div class="dl-grid" style="grid-template-columns:repeat(4,1fr);">
            <a href="/download/${data.job_id}/dataset"  class="dl-btn"><span class="dl-icon">📊</span>Dataset</a>
            <a href="/download/${data.job_id}/report"   class="dl-btn"><span class="dl-icon">📄</span>Report</a>
            <a href="/download/${data.job_id}/script"   class="dl-btn"><span class="dl-icon">🐍</span>Script</a>
            <a href="/download/${data.job_id}/notebook" class="dl-btn" style="border-color:rgba(179,136,255,0.3);color:#b388ff;">
                <span class="dl-icon">📓</span>Notebook
            </a>
        </div>`;
    container.appendChild(resultCard);


    setTimeout(() => resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 100);
    document.getElementById('runBtn').disabled = false;
    document.querySelector('.status-text').textContent = 'PIPELINE COMPLETE';

    // Init chat after pipeline done
    initChat(data.job_id);
}

// ── PIPELINE ──────────────────────────────────────────────────────────────────
async function startPipeline() {
    hideError();
    const obj = document.getElementById('objInput').value.trim();
    if (!selectedFile) { showError('No file selected'); return; }
    if (!obj)          { showError('Learning objective required'); return; }

    document.getElementById('runBtn').disabled = true;
    document.getElementById('cardsContainer').innerHTML = '';
    document.querySelector('.status-text').textContent = 'PIPELINE RUNNING';

    const allAgents = ['orchestrator','profiling','imputation','outlier',
                       'encoding','transformation','dimensionality','sampling'];
    buildFlow(allAgents);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('learning_objective', obj);

    let jobId;
    try {
        const res  = await fetch('/preprocess/file', { method: 'POST', body: formData });
        const body = await res.json();                          // read body ONCE
        if (!res.ok) throw new Error(body.detail || 'Failed to start');
        jobId = body.job_id;
        if (!jobId) throw new Error('Server did not return a job_id');
    } catch (err) {
        showError(err.message);
        document.getElementById('runBtn').disabled = false;
        document.querySelector('.status-text').textContent = 'SYSTEM READY';
        return;
    }

    if (eventSource) eventSource.close();

    console.log('[SSE] jobId:', jobId);
    console.log('[SSE] connecting to:', `/stream/${jobId}`);

    eventSource = new EventSource(`/stream/${jobId}`);

    eventSource.onopen = () => {
        console.log('[SSE] connection opened successfully');
    };

    eventSource.addEventListener('agent_start', e => {
        console.log('[SSE] agent_start:', e.data);
        const d = JSON.parse(e.data);
        setFlowRunning(d.agent);
        addRunningCard(d.agent);
    });

    eventSource.addEventListener('agent_done', e => {
        console.log('[SSE] agent_done:', e.data);
        const d = JSON.parse(e.data);
        setFlowDone(d.agent, d.skipped);
        completeCard(d.agent, d);
    });

    eventSource.addEventListener('done', e => {
        const d = JSON.parse(e.data);
        allAgents.forEach(agent => {
            const s = document.getElementById(`fstatus-${agent}`);
            const n = document.getElementById(`fname-${agent}`);
            if (s && s.textContent === 'waiting') {
                s.textContent = 'not needed';
                if (n) n.style.color = 'var(--muted)';
                setDiagramDone(agent, agentOrder, true);
            }
        });
        showFinalResult(d);
        eventSource.close();
    });

    eventSource.addEventListener('ping', () => {});
    eventSource.onerror = (e) => {
        console.error('[SSE] onerror fired:', e);
        console.error('[SSE] readyState:', eventSource.readyState);
        // readyState: 0=CONNECTING, 1=OPEN, 2=CLOSED
        // Only show error if permanently closed (readyState=2)
        // readyState=0 means browser is auto-reconnecting — don't show error yet
        if (eventSource.readyState === EventSource.CLOSED) {
            showError('SSE connection lost');
            document.getElementById('runBtn').disabled = false;
            document.querySelector('.status-text').textContent = 'CONNECTION ERROR';
        } else {
            console.warn('[SSE] transient error, browser will auto-reconnect...');
        }
    };
}


// ── CHAT ──────────────────────────────────────────────────────────────────────
let chatJobId   = null;
let chatHistory = [];
let chatOpen    = false;
let chatReady   = false;

function initChat(jobId) {
    chatJobId = jobId;
    chatReady = true;
    setTimeout(() => {
        const fab   = document.getElementById('chatFab');
        const badge = document.getElementById('fabBadge');
        fab.classList.add('show');
        badge.classList.add('show');
        setTimeout(() => badge.classList.remove('show'), 3000);
        document.getElementById('chatHeaderSub').textContent = 'Ready · Ask about your dataset';
    }, 800);
}

function toggleChat() {
    chatOpen = !chatOpen;
    const panel = document.getElementById('chatPanel');
    const fab   = document.getElementById('chatFab');
    if (chatOpen) {
        panel.classList.add('show');
        fab.innerHTML = '✕<span class="fab-badge" id="fabBadge"></span>';
        setTimeout(() => document.getElementById('chatInput').focus(), 300);
    } else {
        panel.classList.remove('show');
        fab.innerHTML = '💬<span class="fab-badge" id="fabBadge"></span>';
    }
}

function handleChatKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
}

function autoResize(el) {
    el.style.height = '36px';
    el.style.height = Math.min(el.scrollHeight, 100) + 'px';
}

function sendSuggestion(el) {
    document.getElementById('chatInput').value = el.textContent;
    sendChatMessage();
}

function appendMessage(role, content) {
    const messages = document.getElementById('chatMessages');
    const msg      = document.createElement('div');
    msg.className  = `chat-msg ${role}`;
    msg.innerHTML  = `
        <div class="chat-avatar ${role === 'user' ? 'avatar-user' : 'avatar-ai'}">${role === 'user' ? '👤' : '🤖'}</div>
        <div class="chat-bubble ${role === 'user' ? 'bubble-user' : 'bubble-ai'}">${formatMessage(content)}</div>`;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
}

function formatMessage(text) {
    return text
        .replace(/```([\s\S]*?)```/g, '<pre>$1</pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

function showTyping() {
    const messages = document.getElementById('chatMessages');
    const t = document.createElement('div');
    t.className = 'chat-typing';
    t.id = 'chatTyping';
    t.innerHTML = `
        <div class="chat-avatar avatar-ai">🤖</div>
        <div class="typing-bubble"><span></span><span></span><span></span></div>`;
    messages.appendChild(t);
    messages.scrollTop = messages.scrollHeight;
}

function removeTyping() { document.getElementById('chatTyping')?.remove(); }

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const msg   = input.value.trim();
    if (!msg || !chatReady) return;

    input.value = '';
    input.style.height = '36px';
    document.getElementById('chatSend').disabled = true;
    document.getElementById('chatSuggestions').style.display = 'none';

    appendMessage('user', msg);
    chatHistory.push({ role: 'user', content: msg });
    showTyping();

    try {
        const res = await fetch(`/chat/${chatJobId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, history: chatHistory.slice(-6) })
        });
        removeTyping();
        if (!res.ok) throw new Error('Chat request failed');
        const data  = await res.json();
        const reply = data.reply || 'Sorry, I could not generate a response.';
        appendMessage('assistant', reply);
        chatHistory.push({ role: 'assistant', content: reply });
    } catch (err) {
        removeTyping();
        appendMessage('assistant', '⚠️ Error connecting to chat. Make sure the server is running.');
    }

    document.getElementById('chatSend').disabled = false;
    document.getElementById('chatInput').focus();
}
</script>
</body>
</html>
""")