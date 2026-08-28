# Multi-Agent Data Preprocessing System

## 1. Project Summary

This project is an LLM-powered CSV data preprocessing system. It uses specialized agents coordinated by LangGraph to inspect a dataset, select appropriate preprocessing operations, apply those operations, and generate reproducible artifacts.

The application accepts either an uploaded CSV file or a CSV URL. It can perform profiling, missing-value imputation, outlier handling, categorical encoding, numerical transformation, dimensionality reduction, and class balancing. The selected work depends on the dataset and the requested learning objective, such as classification or regression.

The system produces:

- A preprocessed CSV dataset.
- A Markdown preprocessing report.
- A generated Python preprocessing script.
- A generated Jupyter notebook.
- A quality score describing the result.
- A browser UI with live agent progress and charts.
- A chat endpoint for asking questions about a completed job.

The project is currently a FastAPI service with a vanilla HTML/CSS/JavaScript frontend.

## 2. Main Technologies

- Python 3.10 or newer.
- FastAPI for HTTP APIs.
- Uvicorn for the application server.
- LangGraph for the stateful agent pipeline.
- LangChain and LangChain Groq for LLM calls.
- Groq with the default LLaMA 3.3 70B model.
- pandas and NumPy for data processing.
- scikit-learn for scaling, PCA, feature selection, and statistics.
- imbalanced-learn for optional SMOTE support.
- Pydantic for API request models.
- Server-Sent Events through `sse-starlette` for live progress.
- nbformat for notebook generation.
- Chart.js 4.4.0 for frontend charts.
- Google Fonts using Inter and JetBrains Mono in the UI.

## 3. Repository Structure

```text
.
├── agents/
│   ├── __init__.py
│   ├── dimensionality_agent.py
│   ├── encoding_agent.py
│   ├── imputation_agent.py
│   ├── orchestrator.py
│   ├── outlier_agent.py
│   ├── profiling_agent.py
│   ├── sampling_agent.py
│   ├── transformation_agent.py
│   └── utils.py
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── stream.py
│   └── ui.py
├── core/
│   ├── __init__.py
│   ├── graph.py
│   ├── llm.py
│   └── state.py
├── outputs/
│   ├── preprocessed_dataset.csv
│   ├── preprocessing_report.md
│   ├── preprocessing_script.py
│   └── <job_id>/
├── reports/
│   ├── __init__.py
│   ├── generator.py
│   ├── notebook_generator.py
│   ├── quality_score.py
│   └── templates/
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py
├── uploads/
├── Procfile
├── README.md
├── requirements.txt
├── run.txt
└── test_*.py
```

### Important files

- `agents/orchestrator.py`: loads a CSV, summarizes it, and chooses agents.
- `agents/profiling_agent.py`: calculates dataset-quality statistics and asks for insights.
- `agents/imputation_agent.py`: handles missing values.
- `agents/outlier_agent.py`: detects and handles numeric outliers.
- `agents/encoding_agent.py`: processes object/categorical columns.
- `agents/transformation_agent.py`: scales or log-transforms numeric columns.
- `agents/dimensionality_agent.py`: optionally applies PCA or SelectKBest.
- `agents/sampling_agent.py`: handles classification imbalance.
- `agents/utils.py`: shared distribution and chart-data helpers.
- `core/state.py`: shared `AgentState` definition.
- `core/graph.py`: LangGraph node and routing definition.
- `core/llm.py`: Groq LLM construction and retry behavior.
- `api/main.py`: API endpoints, background jobs, and pipeline execution.
- `api/stream.py`: in-memory SSE event storage and streaming.
- `api/ui.py`: inline HTML, CSS, and JavaScript frontend.
- `reports/generator.py`: report and script generation.
- `reports/quality_score.py`: heuristic before/after quality scoring.
- `reports/notebook_generator.py`: generated notebook creation.

## 4. End-to-End Data Flow

1. The user uploads a CSV through the browser or submits a CSV URL through the API.
2. The API creates an eight-character job ID.
3. For an upload, the file is saved under `uploads/{job_id}_{filename}`.
4. An output directory is created under `outputs/{job_id}`.
5. Processing starts in a background thread.
6. `run_pipeline()` creates an initial `AgentState`, assigns the job ID, builds the LangGraph, and invokes it.
7. The orchestrator loads the CSV into both `dataframe` and `processed_dataframe`.
8. The orchestrator summarizes the data and asks the LLM which agents should run.
9. Profiling is normally forced to run first.
10. The selected agents run sequentially through LangGraph.
11. Each agent reads and updates the shared state and emits progress events.
12. The report generator creates the report and reproducible script.
13. The pipeline computes the quality score and generates a notebook.
14. Job-scoped artifacts are written to `outputs/{job_id}`.
15. The completed response is stored in the process-local `jobs` dictionary.
16. The server emits a final SSE `done` event.
17. The browser displays the result, charts, quality score, and download links.

If the orchestrator selects no processing agents, the graph routes directly to report generation.

## 5. Shared Pipeline State

`core/state.py` defines the `AgentState` dictionary used by every graph node.

### Input fields

- `dataset_path`: local file path or CSV URL.
- `learning_objective`: requested task, for example classification or regression.

### Data fields

- `dataframe`: original loaded pandas DataFrame.
- `processed_dataframe`: working DataFrame modified by agents.

### Agent report fields

- `profiling_report`.
- `imputation_report`.
- `outlier_report`.
- `encoding_report`.
- `transformation_report`.
- `dimensionality_report`.
- `sampling_report`.

### Routing fields

- `agents_to_run`: selected agent names.
- `current_agent`: current pipeline position.

### Output fields

- `final_report`: generated report content.
- `output_dataset_path`: path to the generated CSV.
- `preprocessing_script`: generated Python code.

### Diagnostic fields

- `errors`: pipeline errors.
- `warnings`: non-fatal warnings.

Agents return the state dictionary after updating it. The working DataFrame is passed from one selected agent to the next.

## 6. LangGraph Pipeline

`core/graph.py` defines these nodes:

1. `orchestrator`
2. `profiling`
3. `imputation`
4. `outlier`
5. `encoding`
6. `transformation`
7. `dimensionality`
8. `sampling`
9. `report_generator`

The orchestrator chooses the route. The routing helper `route_after_orchestrator()` decides whether to run the selected agents or go directly to reporting. `route_after_agent()` advances through the selected list and eventually routes to `report_generator`.

The intended logical order is profiling, imputation, outlier handling, encoding, transformation, dimensionality reduction, sampling, and reporting. Only agents selected by the orchestrator are executed.

## 7. Agent Details

### 7.1 Orchestrator

File: `agents/orchestrator.py`

Responsibilities:

- Load local CSV files or CSV URLs with `pandas.read_csv()`.
- Build a compact data summary.
- Ask the LLM which preprocessing agents should run.
- Ensure profiling is included.
- Emit `agent_start` and `agent_done` events.

The summary includes:

- Dataset shape.
- Missing-value counts.
- Numeric and object columns.
- Duplicate-row count.
- Numeric skewness.

The LLM is expected to return a Python-list-like response. `parse_agents_list()` extracts bracketed text, evaluates it using `eval()`, filters valid agent names, and falls back to all agents when parsing fails.

### 7.2 Profiling Agent

File: `agents/profiling_agent.py`

The profiling agent calculates:

- Number of rows and columns.
- Column names.
- Data types.
- Missing counts and percentages.
- Duplicate-row count.
- Numeric descriptive statistics.
- IQR-based outlier counts.
- Categorical cardinality.
- Top five values for categorical fields.
- Potential target columns.

It asks the LLM for up to 200 words of data-quality and preprocessing advice. Potential targets are inferred from columns with two values or three to ten values. The report stores the profile and LLM insights.

The agent emits counts for numeric and categorical columns, columns with missing values, duplicates, and truncated insights.

### 7.3 Imputation Agent

File: `agents/imputation_agent.py`

The agent skips clean datasets and records a skipped report when there are no missing values.

The LLM can select one of these strategies:

- `mean`
- `median`
- `mode`
- `constant`
- `drop_column`
- `drop_rows`

Behavior:

- Mean, median, and mode fill missing values using pandas operations.
- Constant imputation always uses the string `Unknown`.
- `drop_column` removes the selected column.
- `drop_rows` removes rows missing the selected column.

The report includes selected strategies, actions, remaining missing values, and before/after shapes.

### 7.4 Outlier Agent

File: `agents/outlier_agent.py`

The agent detects outliers in numeric columns using both IQR and z-score counts. It skips when no IQR outliers are detected.

The LLM can choose:

- `winsorize`
- `log_transform`
- `drop_rows`
- `keep`

Behavior:

- Winsorization clips values to IQR lower and upper bounds.
- Log transformation applies a natural logarithm, shifting non-positive data when necessary.
- Row dropping removes values outside IQR bounds.
- Keep leaves values unchanged.

The report captures before/after distributions for up to four affected columns.

### 7.5 Encoding Agent

File: `agents/encoding_agent.py`

The agent processes current object-dtype columns. It skips when no object columns remain.

The LLM can choose:

- `onehot`
- `label`
- `frequency`
- `drop`
- `keep`

Behavior:

- One-hot encoding uses `pd.get_dummies()` with `drop_first=False` and removes the original column.
- Label encoding maps sorted non-null unique values to integer indexes.
- Frequency encoding replaces values with normalized frequencies.
- Drop removes the column.
- Keep leaves the column unchanged.

Distributions are captured for up to four columns.

### 7.6 Transformation Agent

File: `agents/transformation_agent.py`

The agent processes current numeric columns and skips when none remain.

The LLM can choose:

- `standard_scaler`
- `minmax_scaler`
- `robust_scaler`
- `log_transform`
- `keep`

The implementation uses:

- `StandardScaler` for mean-centered standardization.
- `MinMaxScaler` for range scaling.
- `RobustScaler` for scaling based on robust statistics.
- A shifted natural log for log transformation when values are non-positive.

Distributions are captured for up to four numeric columns.

### 7.7 Dimensionality Agent

File: `agents/dimensionality_agent.py`

Dimensionality reduction is considered only when the dataset has at least ten columns. A low row-to-feature ratio is an additional reason to consider reduction. Datasets with fewer than ten columns are skipped.

The LLM can select:

- `pca`
- `select_k_best`
- `none`

PCA behavior:

- Excludes the inferred target column.
- Applies PCA.
- Creates columns named `PC1`, `PC2`, and so on.
- Appends the target column afterward.

SelectKBest behavior:

- Uses `f_classif` for classification.
- Uses `f_regression` when the objective contains `regression`.

Target inference recognizes Titanic's `Survived` field, binary classification targets, the last numeric column for regression, or the first potential target.

### 7.8 Sampling Agent

File: `agents/sampling_agent.py`

The sampling agent skips objectives containing `regression`, because class balancing is intended for classification.

It calculates:

- Class counts.
- Class percentages.
- Imbalance ratio.
- Minority and majority classes.

A ratio above 1.5 is treated as imbalanced.

The LLM can choose:

- `oversample`
- `undersample`
- `smote`
- `none`

Oversampling and undersampling use deterministic `random_state=42`. SMOTE uses `imblearn.over_sampling.SMOTE`; if the import or operation is unavailable, the implementation falls back to oversampling.

The report includes target selection, strategy, class balance, action, and before/after shape.

### 7.9 Shared Agent Utilities

File: `agents/utils.py`

`sample_distribution()` creates normalized histogram data for numeric fields or top-value distributions for categorical fields. `capture_distributions()` applies this helper to selected columns for use by the UI.

## 8. LLM Configuration

File: `core/llm.py`

The LLM is constructed with `ChatGroq`.

Environment variables:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Configuration defaults:

- Model: `llama-3.3-70b-versatile`.
- Temperature: `0.1`.
- Request timeout: `60` seconds.
- Maximum output tokens: `1024`.

`python-dotenv` loads environment variables from `.env`.

`RetryLLM` retries rate-limit, timeout, connection, and HTTP 502/503/504 errors for standard `invoke()` calls.

- Rate-limit retries wait 30 seconds multiplied by the attempt number.
- Other retryable errors wait 10 seconds multiplied by the attempt number.
- The wrapper permits up to four retries.
- Streaming retries only rate-limit errors.
- `call_llm_with_retry()` remains as a backwards-compatible helper.

The README also describes replacing Groq with Ollama for Jetson hardware by changing `core/llm.py`. Ollama-specific runtime setup is not included in `requirements.txt`.

## 9. API Endpoints

All main endpoints are in `api/main.py`. The UI route is registered from `api/ui.py`, and the streaming route is registered from `api/stream.py`.

### `GET /`

Returns service information including service name, version, running status, and endpoint descriptions.

### `GET /ui`

Returns the complete browser application as inline HTML, CSS, and JavaScript.

### `POST /preprocess/file`

Accepts multipart form data:

- Required CSV file upload.
- Required `learning_objective` field.

Behavior:

- Rejects filenames that do not end in `.csv` with HTTP 400.
- Saves the upload under `uploads/{job_id}_{filename}`.
- Creates `outputs/{job_id}`.
- Starts a background processing thread.
- Immediately returns:

```json
{
  "job_id": "abcdefgh",
  "status": "started"
}
```

### `POST /preprocess/url`

Accepts a JSON `URLRequest`:

```json
{
  "url": "https://example.com/data.csv",
  "learning_objective": "binary classification"
}
```

The job starts in the background and returns the same started response shape as the file endpoint. The URL is later passed to `pandas.read_csv()`.

### `GET /stream/{job_id}`

Returns an SSE stream for live progress. Events include:

- `agent_start`
- `agent_done`
- `done`
- `error`
- Periodic `ping` events

The stream polls every 0.2 seconds and stops after 300 seconds or after completion/error.

### `GET /results/{job_id}`

Returns the completed job response. It returns HTTP 404 until the job completes successfully or if the process has lost the job record.

### `GET /download/{job_id}/dataset`

Downloads `outputs/{job_id}/preprocessed_dataset.csv` as `text/csv`. Returns HTTP 404 when the file does not exist.

### `GET /download/{job_id}/report`

Downloads the Markdown report as `text/markdown`.

### `GET /download/{job_id}/script`

Downloads the generated Python script as `text/plain`.

### `GET /download/{job_id}/notebook`

Downloads the generated Jupyter notebook as `application/json`.

### `POST /chat/{job_id}`

Accepts a `ChatRequest` containing a message and optional history:

```json
{
  "message": "Why was this column removed?",
  "history": []
}
```

The endpoint requires a completed job. It builds LLM context from the dataset shape, learning objective, final columns, quality score, profiling, and agent actions. At most the last six history entries are included. The response is:

```json
{
  "reply": "..."
}
```

Unknown jobs return HTTP 404.

### CORS

CORS allows all origins, methods, and headers using `allow_origins=["*"]`.

## 10. Background Jobs and Streaming

Jobs are started in background threads so the initial API request returns immediately. Job data, event lists, and locks are kept in process memory.

`push_event_sync()` serializes values that are not directly JSON serializable, including NumPy values, pandas values, sets, and tuples.

Successful jobs are saved in the module-level `jobs` dictionary and emit a `done` event. Failed jobs emit an `error` event but do not create a completed result entry.

The frontend connects with:

```text
EventSource(/stream/{job_id})
```

## 11. Web UI

File: `api/ui.py`

The UI is a single inline HTML response with CSS and JavaScript. It supports:

- Selecting or dragging and dropping a CSV file.
- Selecting preset learning objectives.
- Entering a custom learning objective.
- Starting a preprocessing job.
- Watching agent cards update live.
- Viewing quality score and data-shape information.
- Viewing final columns.
- Viewing distribution charts.
- Downloading the dataset, report, script, and notebook.
- Chatting about a completed job.

Chart.js 4.4.0 is loaded from a CDN. The browser currently exposes file upload, but does not expose the CSV URL endpoint.

Important UI behavior:

- When backend distribution data is absent, the UI generates simulated random charts.
- The profiling correlation heatmap is random; the backend does not compute a real correlation matrix.
- Chat responses use a manually formatted Markdown renderer.

## 12. Reports and Generated Artifacts

### Report generator

File: `reports/generator.py`

`build_executive_summary()` asks the LLM for a 150 to 200 word summary.

`format_report_markdown()` creates sections for:

- Profiling.
- Imputation.
- Outliers.
- Encoding.
- Transformation.
- Dimensionality.
- Sampling.
- Final data.
- Errors.
- Warnings.

`generate_preprocessing_script()` creates a pandas/scikit-learn script based on recorded strategies.

The report generator writes pipeline-level files to:

```text
outputs/preprocessed_dataset.csv
outputs/preprocessing_report.md
outputs/preprocessing_script.py
```

`run_pipeline()` additionally writes job-specific copies under:

```text
outputs/{job_id}/preprocessed_dataset.csv
outputs/{job_id}/preprocessing_report.md
outputs/{job_id}/preprocessing_script.py
```

### Quality score

File: `reports/quality_score.py`

`compute_quality_score()` scores four dimensions, each worth 25 points:

- Completeness.
- Outlier health.
- Feature readiness.
- Class balance.

It returns before/after totals, improvement, letter grades, colors, dimensions, and explanatory details.

Grade thresholds:

- Excellent: score at least 90.
- Good: score at least 75.
- Fair: score at least 60.
- Poor: below 60.

The quality score is heuristic and should not be treated as a formal statistical validation.

### Notebook generator

File: `reports/notebook_generator.py`

`generate_notebook()` creates an nbformat 4 notebook containing cells for:

- Imports.
- Data loading.
- Profiling.
- Imputation.
- Outlier handling.
- Encoding.
- Transformation.
- Dimensionality reduction.
- Sampling.
- Final overview.
- Plots.
- Saving the result.

The notebook is saved as:

```text
outputs/{job_id}/preprocessing_notebook.ipynb
```

The notebook loads the basename of the original dataset rather than necessarily using the original absolute path.

## 13. Installation and Running

### Prerequisites

- Python 3.10 or newer.
- A Groq API key.
- Node.js is optional and may be used for DOCX generation described by project documentation.

### Setup

From the project root:

```bash
python -m venv venv
```

Windows:

```bash
venv\\Scripts\\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Start the development server:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Open the application:

```text
http://localhost:8000/ui
```

Open interactive API documentation:

```text
http://localhost:8000/docs
```

### Deployment

The `Procfile` contains:

```text
web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

This is intended for a platform that provides the `PORT` environment variable.

`run.txt` contains development commands, including variants that reload only selected source directories.

## 14. Dependencies

Pinned dependencies in `requirements.txt` include:

- `fastapi==0.116.1`
- `uvicorn[standard]==0.35.0`
- `python-multipart==0.0.22`
- `sse-starlette==2.1.3`
- `langchain==0.3.27`
- `langchain-groq==0.3.7`
- `langchain-core==0.3.74`
- `langgraph==0.6.4`
- `pandas==2.2.2`
- `numpy==1.26.4`
- `scikit-learn==1.5.1`
- `python-dotenv==1.1.1`
- `xgboost==3.2.0`
- `nbformat==5.10.4`
- `httpx==0.27.2`
- `groq==0.31.0`
- `pydantic==2.11.7`
- `langchain-community==0.3.27`
- `langgraph-checkpoint==2.1.1`

Important dependency gap: `sampling_agent.py` imports `imblearn.over_sampling.SMOTE`, but `imbalanced-learn` is not listed in `requirements.txt`. Without that package, SMOTE falls back to regular oversampling.

## 15. Tests

The root-level test files are executable scripts rather than conventional pytest tests. Most invoke the real pipeline and print results.

- `test_connection.py`: directly tests Groq with a hard-coded model and prints a response.
- `test_orchestrator.py`: runs the graph using `uploads/titanic.csv`, then prints shape, selected agents, and errors.
- `test_full_pipeline.py`: runs the full graph using a Titanic URL and prints final output information.
- `test_profiling.py`: prints profiling report fields.
- `test_imputation.py`: prints strategies, actions, and shapes.
- `test_outlier.py`: prints outlier handling results.
- `test_encoding.py`: prints encoding results and final columns.
- `test_transformation.py`: prints transformation results and sample data.
- `test_dimensionality.py`: prints dimensionality behavior.
- `test_sampling.py`: prints sampling behavior and final shape.
- `test_graph.py`: invokes the graph with `test.csv` and prints the final report.
- `tests/test_pipeline.py`: currently exists but is empty.

The scripts generally require network access, a valid Groq API key, appropriate input data, and all runtime dependencies. There are no formal fixtures, mocks, assertions, or conventional test functions in the current test suite.

## 16. Known Limitations and Risks

### Security

- LLM responses are parsed with Python `eval()` in the orchestrator and several agents. Malformed or hostile model output could execute arbitrary Python in the service process.
- Uploaded filenames are interpolated directly into upload paths.
- There is no explicit upload-size limit.
- CSV URL input is not explicitly validated.
- There is no authentication or authorization.
- There is no rate limiting.
- CORS allows every origin.

### Concurrency and persistence

- Agent job IDs are stored in module-level `_current_job_id` variables. Concurrent runs can overwrite each other's IDs and send events to the wrong stream.
- `jobs`, SSE event lists, and locks are process-local.
- Data is lost when the process restarts.
- Multiple worker processes do not share job state or events.
- Failed background jobs are visible through SSE only; their result endpoint remains 404.

### Reproducibility and behavior

- The LLM controls routing and strategy selection, so execution is nondeterministic and depends on model output.
- The quality score is heuristic. For example, completing outlier handling automatically adds eight points regardless of the final outlier count.
- Profiling primarily uses numeric and object dtype detection; other pandas dtypes are not classified as categorical.
- Generated artifacts are not always identical to the live pipeline:
  - Dimensionality decisions are not included in the generated Python script.
  - Some generated log transforms use `+1` even when live code calculates a different shift.
  - The notebook profiling section reads `insights`, while the profiling agent stores `llm_insights`.
- The UI can show simulated distributions when the backend does not provide data.
- The UI correlation heatmap is random and is not based on calculated correlations.
- The generated notebook may not find the original dataset because it uses only the dataset basename.

## 17. Current Local Status

The FastAPI application has been started successfully in the local development environment and is available at:

```text
http://localhost:8000/ui
```

The root API and interactive documentation are also expected at:

```text
http://localhost:8000/
http://localhost:8000/docs
```

A valid `GROQ_API_KEY` is required for LLM-backed preprocessing jobs and chat requests, even though the basic web service can start without making a pipeline request.

## 18. Typical Usage

1. Start the server.
2. Open `/ui`.
3. Upload a CSV file.
4. Select or enter a learning objective.
5. Start the pipeline.
6. Watch the SSE agent updates.
7. Review the quality score and final columns.
8. Download the cleaned CSV, report, Python script, or notebook.
9. Ask questions through the chat panel after completion.

## 19. Suggested Improvements

These are engineering improvements indicated by the current implementation:

- Replace `eval()` with strict JSON parsing and schema validation.
- Sanitize uploaded filenames and use generated safe paths.
- Add upload-size, URL, authentication, authorization, and rate-limit controls.
- Move jobs and SSE events to shared persistent storage for production deployments.
- Avoid module-level job ID state; pass job context explicitly through the graph.
- Add `imbalanced-learn` to `requirements.txt` if SMOTE is intended to be supported.
- Add formal pytest tests with mocked LLM responses.
- Compute a real correlation matrix for the profiling UI.
- Make generated scripts and notebooks use the exact same transformations as the live pipeline.
- Fix the notebook profiling field name mismatch.
- Make generated notebooks reference an accessible input path or embed the uploaded data location.
- Add structured logging and a persistent job status model.
- Add validation for generated code and LLM-selected strategies.
