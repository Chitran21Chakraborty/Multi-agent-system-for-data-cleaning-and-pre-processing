import os
import uuid
import shutil
import asyncio
import threading
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.graph import build_graph
from api.ui import router as ui_router
from api.stream import router as stream_router, push_event_sync
from reports.quality_score import compute_quality_score
from reports.notebook_generator import generate_notebook
from core.llm import get_llm

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import json



# ── PYDANTIC MODELS ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

class URLRequest(BaseModel):
    url: str
    learning_objective: str


# ── APP INIT ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AutoClean API",
    description="Autonomous LLM-powered data preprocessing pipeline",
    version="1.0.0"
)

app.include_router(ui_router)
app.include_router(stream_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

jobs = {}


# ── STATE INIT ────────────────────────────────────────────────────────────────
def get_initial_state(dataset_path: str, learning_objective: str) -> dict:
    return {
        "dataset_path": dataset_path,
        "learning_objective": learning_objective,
        "dataframe": None,
        "processed_dataframe": None,
        "profiling_report": None,
        "imputation_report": None,
        "outlier_report": None,
        "encoding_report": None,
        "transformation_report": None,
        "dimensionality_report": None,
        "sampling_report": None,
        "agents_to_run": None,
        "current_agent": None,
        "final_report": None,
        "output_dataset_path": None,
        "preprocessing_script": None,
        "errors": [],
        "warnings": []
    }


# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "AutoClean",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "GET /ui": "Web interface",
            "POST /preprocess/file": "Upload a CSV file and preprocess it",
            "POST /preprocess/url": "Provide a CSV URL and preprocess it",
            "GET /results/{job_id}": "Get results for a job",
            "GET /download/{job_id}/dataset": "Download preprocessed dataset",
            "GET /download/{job_id}/report": "Download preprocessing report",
            "GET /download/{job_id}/script": "Download preprocessing script",
            "GET /download/{job_id}/notebook": "Download Jupyter notebook",
            "POST /chat/{job_id}": "Chat about your dataset"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "autoclean"}


@app.post("/preprocess/file")
async def preprocess_file(
    file: UploadFile = File(...),
    learning_objective: str = Form(...)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    job_id = str(uuid.uuid4())[:8]
    os.makedirs("uploads", exist_ok=True)
    os.makedirs(f"outputs/{job_id}", exist_ok=True)

    file_path = f"uploads/{job_id}_{file.filename}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    def run_in_background():
        try:
            result = run_pipeline(file_path, learning_objective, job_id)
            response_data = build_response(result, job_id)
            jobs[job_id] = response_data
            push_event_sync(job_id, "done", response_data)
        except Exception as e:
            push_event_sync(job_id, "error", {"message": str(e)})

    thread = threading.Thread(target=run_in_background)
    thread.start()

    return {"job_id": job_id, "status": "started"}


@app.post("/preprocess/url")
async def preprocess_url(request: URLRequest):
    job_id = str(uuid.uuid4())[:8]
    os.makedirs(f"outputs/{job_id}", exist_ok=True)

    def run_in_background():
        try:
            result = run_pipeline(request.url, request.learning_objective, job_id)
            response_data = build_response(result, job_id)
            jobs[job_id] = response_data
            push_event_sync(job_id, "done", response_data)
        except Exception as e:
            push_event_sync(job_id, "error", {"message": str(e)})

    thread = threading.Thread(target=run_in_background)
    thread.start()

    return {"job_id": job_id, "status": "started"}


@app.get("/results/{job_id}")
def get_results(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


# ── DOWNLOAD ROUTES ───────────────────────────────────────────────────────────
@app.get("/download/{job_id}/dataset")
def download_dataset(job_id: str):
    path = f"outputs/{job_id}/preprocessed_dataset.csv"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Dataset not found")
    return FileResponse(path, media_type="text/csv",
                        filename="preprocessed_dataset.csv")


@app.get("/download/{job_id}/report")
def download_report(job_id: str):
    path = f"outputs/{job_id}/preprocessing_report.md"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(path, media_type="text/markdown",
                        filename="preprocessing_report.md")


@app.get("/download/{job_id}/script")
def download_script(job_id: str):
    path = f"outputs/{job_id}/preprocessing_script.py"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Script not found")
    return FileResponse(path, media_type="text/plain",
                        filename="preprocessing_script.py")


@app.get("/download/{job_id}/notebook")
def download_notebook(job_id: str):
    path = f"outputs/{job_id}/preprocessing_notebook.ipynb"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Notebook not found")
    return FileResponse(path, media_type="application/json",
                        filename="preprocessing_notebook.ipynb")


def normalize_question(text: str) -> str:
    return (text or "").strip().lower()


def contains_any(text: str, terms: list[str]) -> bool:
    q = normalize_question(text)
    return any(term.lower() in q for term in terms)


def build_agent_explanation(result: dict, agent_name: str) -> str:
    agent_map = {
        "imputation": ("imputation_report", ["imputation", "missing", "null", "fill"]),
        "outlier": ("outlier_report", ["outlier", "extreme", "anomaly"]),
        "encoding": ("encoding_report", ["encoding", "categorical", "one-hot", "label"]),
        "transformation": ("transformation_report", ["transform", "scale", "scaling", "normalize"]),
        "dimensionality": ("dimensionality_report", ["dimensionality", "pca", "feature reduction"]),
        "sampling": ("sampling_report", ["sampling", "oversample", "undersample", "smote", "imbalance"]),
    }
    key, _ = agent_map.get(agent_name, (None, []))
    report = result.get(key, {}) if key else {}
    status = report.get("status")
    reason = report.get("reason") or "No action was required by the pipeline logic."

    if agent_name == "imputation":
        profiling = result.get("profiling_report", {}) or {}
        missing = profiling.get("missing_values", {}) or {}
        if not missing:
            return "The imputation agent was skipped because the profiling stage found no missing values in the dataset, so there was nothing to fill."
        if status == "skipped":
            return f"The imputation agent was skipped because the dataset profile did not require an imputation pass for this run: {reason}."
        return f"The imputation agent did not need to change the dataset because the missing-value profile was already acceptable: {reason}."

    if agent_name == "outlier":
        if status == "skipped":
            return f"The outlier agent was skipped because no significant outliers were detected in the numeric columns for this dataset: {reason}."
        return f"The outlier agent did not need to modify the data because the distribution stayed within acceptable bounds: {reason}."

    if status == "skipped":
        return f"The {agent_name} agent was skipped because the dataset profile did not require that preprocessing step: {reason}."
    return f"The {agent_name} agent did not perform a major change because the dataset already met the conditions for this step: {reason}."


def build_skip_explanation(result: dict, question: str) -> str:
    q = normalize_question(question)
    if "imputation" in q or "missing" in q or "null" in q:
        return build_agent_explanation(result, "imputation")
    if "outlier" in q or "anomaly" in q or "extreme" in q:
        return build_agent_explanation(result, "outlier")
    if "encoding" in q or "categorical" in q:
        return build_agent_explanation(result, "encoding")
    if "transform" in q or "scale" in q or "scaling" in q:
        return build_agent_explanation(result, "transformation")
    if "feature" in q and ("reduce" in q or "dim" in q or "pca" in q):
        return build_agent_explanation(result, "dimensionality")
    if "sample" in q or "oversample" in q or "undersample" in q or "imbalance" in q:
        return build_agent_explanation(result, "sampling")
    return "The selected preprocessing agent was skipped because the dataset profile did not require that step for this run."


def build_irrelevant_response(question: str) -> str:
    q = normalize_question(question)
    if not q:
        return "I can explain the preprocessing pipeline and dataset behavior for this job. Ask about missing values, outliers, encoding, scaling, or why an agent was skipped."
    if contains_any(q, ["weather", "football", "movie", "politics", "travel", "stock", "recipe", "joke", "math equation", "capital of", "who is", "history"]):
        return "I can help only with this dataset and its preprocessing pipeline. Ask about missing values, outliers, encoding, scaling, agent decisions, or dataset quality."
    return "I’m focused on this dataset’s preprocessing workflow. Ask me about the agents, missing values, outlier handling, encoding, transformations, or reporting results."


def build_dataset_summary_response(result: dict, question: str) -> str | None:
    q = normalize_question(question)
    summary = result.get("summary", {}) or {}
    profiling = result.get("profiling_report", {}) or {}
    columns = summary.get("final_columns") or []
    original_shape = summary.get("original_shape", {}) or {}
    final_shape = summary.get("final_shape", {}) or {}
    quality = result.get("quality_score", {}) or {}

    if "column" in q or "feature" in q:
        if columns:
            return f"The processed dataset has {len(columns)} columns: {', '.join(columns[:12])}{'...' if len(columns) > 12 else ''}."
        return "I could not find a column list in the current dataset report."

    if "row" in q or "shape" in q or "size" in q:
        return f"The dataset started at {original_shape.get('rows', '?')} rows × {original_shape.get('columns', '?')} columns and ended at {final_shape.get('rows', '?')} rows × {final_shape.get('columns', '?')} columns."

    if "missing" in q or "null" in q:
        missing = profiling.get("missing_values", {}) or {}
        if not missing:
            return "There are no missing values in the current dataset profile, so the imputation step was skipped."
        return f"Missing values were found in {len(missing)} column(s): {', '.join(list(missing)[:5])}{'...' if len(missing) > 5 else ''}."

    if "quality" in q or "score" in q:
        after = quality.get("total_after")
        if after is not None:
            return f"The quality score after preprocessing is {after} out of 100, with grade {quality.get('grade_after', {}).get('label', 'N/A')}."
        return "The dataset quality report is not available yet."

    if "target" in q and "objective" in q:
        return f"The learning objective is {result.get('learning_objective', 'not specified')}."

    return None


# ── CHAT ROUTE ────────────────────────────────────────────────────────────────
@app.post("/chat/{job_id}")
async def chat_with_data(job_id: str, request: ChatRequest):
    if job_id not in jobs:
        return {
            "reply": "I don’t have a completed preprocessing job for this dataset yet. Run a pipeline first, then ask me about missing values, encoding choices, transformations, quality, or feature recommendations."
        }

    result = jobs[job_id]

    profiling      = result.get("profiling_report", {}) or {}
    imputation     = result.get("imputation_report", {}) or {}
    outlier        = result.get("outlier_report", {}) or {}
    encoding       = result.get("encoding_report", {}) or {}
    transformation = result.get("transformation_report", {}) or {}
    quality        = result.get("quality_score", {}) or {}
    summary        = result.get("summary", {}) or {}
    orig_shape     = summary.get("original_shape", {})
    final_shape    = summary.get("final_shape", {})
    columns        = summary.get("final_columns", [])

    def fmt(d):
        return json.dumps(d, indent=2, default=str)[:800] if d else "N/A"

    system_prompt = f"""You are an expert data science assistant helping an ML engineer understand their dataset and preprocessing pipeline.

DATASET CONTEXT:
- Original shape: {orig_shape.get('rows','?')} rows x {orig_shape.get('columns','?')} columns
- Final shape: {final_shape.get('rows','?')} rows x {final_shape.get('columns','?')} columns
- Learning objective: {result.get('learning_objective', 'N/A')}
- Final columns: {', '.join(columns[:20]) if columns else 'N/A'}

DATA QUALITY SCORE:
- Before: {quality.get('total_before','?')} ({quality.get('grade_before',{}).get('label','')})
- After:  {quality.get('total_after','?')} ({quality.get('grade_after',{}).get('label','')})
- Improvement: +{quality.get('improvement','?')}

PROFILING SUMMARY:
- Numerical columns: {len(profiling.get('numerical_columns', {}))}
- Categorical columns: {len(profiling.get('categorical_columns', {}))}
- Missing values found: {len(profiling.get('missing_values', {}))}
- Duplicate rows: {profiling.get('duplicate_rows', 0)}
- Insights: {profiling.get('insights', 'N/A')[:400]}

IMPUTATION ACTIONS:
{fmt(imputation.get('actions_taken'))}

OUTLIER ACTIONS:
{fmt(outlier.get('actions_taken'))}

ENCODING ACTIONS:
{fmt(encoding.get('actions_taken'))}

TRANSFORMATION ACTIONS:
{fmt(transformation.get('actions_taken'))}

INSTRUCTIONS:
- Answer questions specifically about THIS dataset and pipeline
- Be concise but technical — the user is an ML engineer
- If asked about a specific column, use the context above
- If asked for recommendations, give concrete actionable advice
- Use markdown for code snippets
- Keep answers under 200 words unless more detail is needed
"""

    llm = get_llm()
    messages = [SystemMessage(content=system_prompt)]

    for msg in request.history[-6:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=request.message))

    q = request.message.strip()
    q_lower = normalize_question(q)

    dataset_summary = build_dataset_summary_response(result, q)
    if dataset_summary:
        return {"reply": dataset_summary}

    if contains_any(q_lower, ["why", "skipped", "not run", "not needed", "did not run"]) and any(agent in q_lower for agent in ["imputation", "outlier", "encoding", "transformation", "dimensionality", "sampling"]):
        return {"reply": build_skip_explanation(result, q)}

    if not any(keyword in q_lower for keyword in ["dataset", "column", "feature", "agent", "missing", "outlier", "encoding", "transform", "scale", "quality", "preprocess", "imputation", "sampling", "null", "target", "row", "shape", "distribution", "value", "rows", "columns", "features"]):
        return {"reply": build_irrelevant_response(q)}

    response = llm.invoke(messages)
    reply = getattr(response, "content", str(response))
    if isinstance(reply, str):
        reply = reply.replace("[Rule Engine Fallback]", "").strip()

    if not reply or len(reply) < 20 and "rule-based" in reply.lower():
        reply = "I’m using the dataset profile to answer this question. Ask me about missing values, outlier handling, encoding choices, the preprocessing steps, or why an agent was skipped."

    return {"reply": reply}



# ── PIPELINE ──────────────────────────────────────────────────────────────────
def run_pipeline(dataset_path: str, learning_objective: str, job_id: str) -> dict:
    import agents.orchestrator as orch
    import agents.profiling_agent as pa
    import agents.imputation_agent as ia
    import agents.outlier_agent as oa
    import agents.encoding_agent as ea
    import agents.transformation_agent as ta
    import agents.dimensionality_agent as da
    import agents.sampling_agent as sa

    for mod in [orch, pa, ia, oa, ea, ta, da, sa]:
        mod.set_job_id(job_id)

    graph = build_graph()
    initial_state = get_initial_state(dataset_path, learning_objective)
    result = graph.invoke(initial_state)

    # Save outputs
    df_final = result.get("processed_dataframe")
    if df_final is not None:
        df_final.to_csv(f"outputs/{job_id}/preprocessed_dataset.csv",
                        index=False, encoding="utf-8")

    report = result.get("final_report", "")
    if report:
        with open(f"outputs/{job_id}/preprocessing_report.md", "w",
                  encoding="utf-8", errors="replace") as f:
            f.write(report)

    script = result.get("preprocessing_script", "")
    if script:
        with open(f"outputs/{job_id}/preprocessing_script.py", "w",
                  encoding="utf-8", errors="replace") as f:
            f.write(script)

    # Compute quality score
    result["quality_score"] = compute_quality_score(result)

    # Generate notebook
    notebook_json = generate_notebook(result, job_id, dataset_path, learning_objective)
    with open(f"outputs/{job_id}/preprocessing_notebook.ipynb", "w",
              encoding="utf-8") as f:
        f.write(notebook_json)

    return result


# ── RESPONSE BUILDERS ──────────────────────────────────────────────────────────
def build_response(result: dict, job_id: str) -> dict:
    df_final  = result.get("processed_dataframe")
    profiling = result.get("profiling_report", {})

    # Build dataset preview (first 8 rows)
    dataset_preview = None
    if df_final is not None:
        try:
            preview_df = df_final.head(8)
            dataset_preview = {
                "head": preview_df.fillna("").astype(str).to_dict(orient="records"),
                "columns": df_final.columns.tolist()
            }
        except Exception:
            dataset_preview = None

    return {
        "job_id": job_id,
        "status": "completed",
        "errors": result.get("errors", []),
        "quality_score": result.get("quality_score", {}),
        "learning_objective": result.get("learning_objective", ""),
        "final_report": result.get("final_report", ""),
        "profiling_report":      result.get("profiling_report"),
        "imputation_report":     result.get("imputation_report"),
        "outlier_report":        result.get("outlier_report"),
        "encoding_report":       result.get("encoding_report"),
        "transformation_report": result.get("transformation_report"),
        "dimensionality_report": result.get("dimensionality_report"),
        "sampling_report":       result.get("sampling_report"),
        "dataset_preview": dataset_preview,
        "summary": {
            "original_shape": profiling.get("shape", {}),
            "final_shape": {
                "rows": df_final.shape[0],
                "columns": df_final.shape[1]
            } if df_final is not None else {},
            "agents_run": result.get("agents_to_run", []),
            "final_columns": df_final.columns.tolist() if df_final is not None else []
        },
        "downloads": {
            "dataset":  f"/download/{job_id}/dataset",
            "report":   f"/download/{job_id}/report",
            "script":   f"/download/{job_id}/script",
            "notebook": f"/download/{job_id}/notebook"
        }
    }

