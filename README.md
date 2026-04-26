#  Multi-Agent Data Preprocessing System

An autonomous LLM-powered data preprocessing pipeline that analyzes CSV datasets and applies intelligent preprocessing decisions using a multi-agent architecture orchestrated by LangGraph.

---

##  Overview

This system uses multiple specialized AI agents, each responsible for a specific preprocessing task. A central **Orchestrator Agent** analyzes the dataset and decides which agents to run. Each agent consults a **LLaMA 3.3 70B** language model (via Groq) to make context-aware decisions rather than applying fixed rules.

The system features a **real-time streaming web UI** where users can watch each agent's decisions appear live as the pipeline runs.

---

##  Architecture

```
CSV Dataset
     ↓
┌─────────────────┐
│   Orchestrator  │  ← Analyzes data, selects agents to run
└────────┬────────┘
         ↓
┌────────────────────────────────────────────────┐
│                LangGraph Pipeline              │
│                                                │
│   Profiling →  Imputation →  Outlier    │
│  →  Encoding →  Transformation            │
│  →  Dimensionality → Sampling            │
└────────────────────────────────────────────────┘
         ↓
┌─────────────────┐
│ Report Generator│  ← Executive summary + reproducible script
└─────────────────┘
         ↓
   Clean Dataset   Report   Python Script
```

### Agent Descriptions

| Agent | Responsibility |
|-------|---------------|
| **Orchestrator** | Loads dataset, profiles it, decides which agents to run |
| **Profiling** | Statistical analysis — missing values, skewness, outliers, cardinality |
| **Imputation** | Fills missing values using mean / median / mode / drop strategies |
| **Outlier** | Detects and handles outliers via winsorization, log transform, or row drop |
| **Encoding** | Encodes categorical columns — one-hot, label, frequency, or drop |
| **Transformation** | Scales numerical features — StandardScaler, RobustScaler, MinMaxScaler, log |
| **Dimensionality** | Reduces features via PCA or SelectKBest when needed |
| **Sampling** | Balances class imbalance via SMOTE, oversample, or undersample |

---

##  Project Structure

```
data_prep_agent/
├── agents/
│   ├── orchestrator.py          # Dataset loading + agent routing
│   ├── profiling_agent.py       # Statistical profiling
│   ├── imputation_agent.py      # Missing value handling
│   ├── outlier_agent.py         # Outlier detection & handling
│   ├── encoding_agent.py        # Categorical encoding
│   ├── transformation_agent.py  # Feature scaling
│   ├── dimensionality_agent.py  # Dimensionality reduction
│   └── sampling_agent.py        # Class balancing
├── core/
│   ├── state.py                 # Shared pipeline state (TypedDict)
│   ├── graph.py                 # LangGraph pipeline definition
│   └── llm.py                   # LLM connection (Groq)
├── api/
│   ├── main.py                  # FastAPI endpoints
│   ├── stream.py                # Server-Sent Events (SSE) streaming
│   └── ui.py                    # Web interface (dark theme)
├── reports/
│   └── generator.py             # Report + script generation
├── outputs/                     # Generated files per job
├── uploads/                     # Uploaded CSV files
├── .env                         # API keys
└── requirements.txt
```

---

##  Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js (optional, for docx generation)
- A free [Groq API key](https://console.groq.com)

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/data_prep_agent.git
cd data_prep_agent
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

### 5. Start the server

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Open the web interface

```
http://localhost:8000/ui
```

---

##  Usage

1. Open `http://localhost:8000/ui`
2. Upload a CSV file or provide a CSV URL
3. Select or type a learning objective (e.g. `binary classification`, `regression`)
4. Click **Run Pipeline**
5. Watch each agent report its findings in real-time
6. Download the preprocessed dataset, full report, or Python script

---

##  API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ui` | Web interface |
| `POST` | `/preprocess/file` | Upload CSV + run pipeline |
| `POST` | `/preprocess/url` | CSV URL + run pipeline |
| `GET` | `/stream/{job_id}` | SSE stream for live updates |
| `GET` | `/results/{job_id}` | Get full job results |
| `GET` | `/download/{job_id}/dataset` | Download preprocessed CSV |
| `GET` | `/download/{job_id}/report` | Download markdown report |
| `GET` | `/download/{job_id}/script` | Download Python script |

Interactive API docs available at `http://localhost:8000/docs`

---

##  Requirements

```
fastapi
uvicorn
langchain
langchain-groq
langgraph
pandas
numpy
scikit-learn
sse-starlette
python-multipart
python-dotenv
pydantic
```

Install all with:

```bash
pip install -r requirements.txt
```

---

##  Output Files

After each run, three files are saved to `outputs/{job_id}/`:

- **`preprocessed_dataset.csv`** — Clean, ML-ready dataset
- **`preprocessing_report.md`** — Full report with agent decisions, LLM insights, and dataset statistics
- **`preprocessing_script.py`** — Standalone reproducible Python script with all transformations applied

---
##  Edge Deployment (Jetson AGX Thor)

This system is designed to run on edge hardware. To switch from Groq cloud API to a local LLM on Jetson Thor, change only one file:

**`core/llm.py`** — replace:

```python
# Cloud (Groq)
from langchain_groq import ChatGroq
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
```

with:

```python
# Local (Ollama on Jetson)
from langchain_community.llms import Ollama
llm = Ollama(model="llama3:70b")
```

Then on the Jetson:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3:70b
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

##  Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | LLaMA 3.3 70B via Groq API |
| Agent Orchestration | LangGraph |
| Backend | FastAPI |
| Streaming | Server-Sent Events (SSE) |
| Data Processing | Pandas, NumPy, Scikit-learn |
| Frontend | Vanilla JS + CSS (dark theme) |

---

##  Example Results

**Titanic Dataset (891 rows, 12 columns)**
- Agents run: profiling, imputation, encoding, transformation, outlier
- Missing values handled: Age (median), Cabin (dropped), Embarked (mode)
- Encoding: Sex (label), Embarked (one-hot), Name/Ticket (dropped)
- Final shape: 891 × 11, 0 missing values

**Air Quality Dataset (185 rows, 9 columns)**
- Agents run: profiling, imputation, outlier, transformation
- Missing values handled: PM 2.5 (median)
- Outliers: 6 columns treated, 2 rows removed
- Final shape: 183 × 9, fully scaled

---

##  License

MIT License — free to use for academic and commercial purposes.

---

##  Author

Built as a semester project demonstrating autonomous multi-agent systems for data preprocessing with edge AI deployment capabilities.
