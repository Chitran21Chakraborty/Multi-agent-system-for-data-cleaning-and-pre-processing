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
    title="Multi-Agent Data Preprocessing System",
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
        "message": "Multi-Agent Data Preprocessing System",
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


# ── CHAT ROUTE ────────────────────────────────────────────────────────────────
@app.post("/chat/{job_id}")
async def chat_with_data(job_id: str, request: ChatRequest):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

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

    response = llm.invoke(messages)
    return {"reply": response.content}



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


# ── RESPONSE BUILDER ──────────────────────────────────────────────────────────
def build_response(result: dict, job_id: str) -> dict:
    df_final  = result.get("processed_dataframe")
    profiling = result.get("profiling_report", {})

    return {
        "job_id": job_id,
        "status": "completed",
        "errors": result.get("errors", []),
        "quality_score": result.get("quality_score", {}),
        "learning_objective": result.get("learning_objective", ""),
        "profiling_report":      result.get("profiling_report"),
        "imputation_report":     result.get("imputation_report"),
        "outlier_report":        result.get("outlier_report"),
        "encoding_report":       result.get("encoding_report"),
        "transformation_report": result.get("transformation_report"),
        "dimensionality_report": result.get("dimensionality_report"),
        "sampling_report":       result.get("sampling_report"),
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