import pandas as pd
import numpy as np
from core.state import AgentState
from core.llm import get_llm
from langchain_core.messages import HumanMessage

# SSE streaming
_current_job_id = None

def set_job_id(job_id: str):
    global _current_job_id
    _current_job_id = job_id

def emit(event_type: str, data: dict):
    if _current_job_id:
        from api.stream import push_event_sync
        push_event_sync(_current_job_id, event_type, data)


def run_profiling(df: pd.DataFrame) -> dict:
    report = {}

    report["shape"] = {"rows": df.shape[0], "columns": df.shape[1]}
    report["column_names"] = df.columns.tolist()
    report["dtypes"] = df.dtypes.astype(str).to_dict()

    missing = df.isnull().sum()
    missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
    report["missing_values"] = {
        col: {"count": int(missing[col]), "percentage": float(missing_pct[col])}
        for col in df.columns if missing[col] > 0
    }

    report["duplicate_rows"] = int(df.duplicated().sum())

    num_cols = df.select_dtypes(include='number').columns.tolist()
    report["numerical_columns"] = {}
    for col in num_cols:
        report["numerical_columns"][col] = {
            "mean": round(float(df[col].mean()), 4),
            "median": round(float(df[col].median()), 4),
            "std": round(float(df[col].std()), 4),
            "min": round(float(df[col].min()), 4),
            "max": round(float(df[col].max()), 4),
            "skewness": round(float(df[col].skew()), 4),
            "kurtosis": round(float(df[col].kurt()), 4),
            "outliers_iqr": int(count_outliers_iqr(df[col]))
        }

    cat_cols = df.select_dtypes(include='object').columns.tolist()
    report["categorical_columns"] = {}
    for col in cat_cols:
        report["categorical_columns"][col] = {
            "unique_values": int(df[col].nunique()),
            "top_5_values": df[col].value_counts().head(5).to_dict(),
            "cardinality": classify_cardinality(df[col].nunique())
        }

    report["potential_target_columns"] = identify_potential_targets(df)

    return report


def count_outliers_iqr(series: pd.Series) -> int:
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    return ((series < Q1 - 1.5 * IQR) | (series > Q3 + 1.5 * IQR)).sum()


def classify_cardinality(n_unique: int) -> str:
    if n_unique <= 2:
        return "binary"
    elif n_unique <= 10:
        return "low"
    elif n_unique <= 50:
        return "medium"
    else:
        return "high"


def identify_potential_targets(df: pd.DataFrame) -> list:
    potential = []
    for col in df.columns:
        n_unique = df[col].nunique()
        if n_unique == 2:
            potential.append({"column": col, "type": "binary classification"})
        elif 2 < n_unique <= 10:
            potential.append({"column": col, "type": "multiclass classification"})
    return potential


def get_llm_insights(profile: dict, objective: str) -> str:
    llm = get_llm()
    prompt = f"""
You are an expert data scientist. Based on the following dataset profile, provide 
concise and actionable insights relevant to the learning objective.

Learning Objective: {objective}

Dataset Profile:
- Shape: {profile['shape']}
- Missing Values: {profile['missing_values']}
- Duplicate Rows: {profile['duplicate_rows']}
- Numerical Columns: {list(profile['numerical_columns'].keys())}
- Categorical Columns: {list(profile['categorical_columns'].keys())}
- Potential Target Columns: {profile['potential_target_columns']}

Numerical Stats Summary:
{summarize_numerical(profile['numerical_columns'])}

Provide:
1. Key observations about data quality
2. Potential issues that need preprocessing
3. Recommendations for the preprocessing pipeline
Keep it concise — max 200 words.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


def summarize_numerical(num_cols: dict) -> str:
    lines = []
    for col, stats in num_cols.items():
        lines.append(
            f"  {col}: skewness={stats['skewness']}, "
            f"outliers={stats['outliers_iqr']}"
        )
    return "\n".join(lines)


def profiling_node(state: AgentState) -> AgentState:
    print("Running profiling agent...")

    # Emit start event
    emit("agent_start", {"agent": "profiling", "label": "Data Profiling"})

    df = state.get("dataframe")
    if df is None:
        from agents.orchestrator import load_dataset
        df = load_dataset(state["dataset_path"])
        state["dataframe"] = df
        state["processed_dataframe"] = df.copy()

    # Run profiling
    profile = run_profiling(df)

    # Get LLM insights
    print("  Getting LLM insights on data profile...")
    insights = get_llm_insights(profile, state["learning_objective"])
    profile["llm_insights"] = insights

    state["profiling_report"] = profile
    state["current_agent"] = "profiling"

    print(f"  Profiling complete — {len(profile['numerical_columns'])} numerical, "
          f"{len(profile['categorical_columns'])} categorical columns analyzed")
    print(f"  Missing values found in: {list(profile['missing_values'].keys())}")
    print(f"  Duplicate rows: {profile['duplicate_rows']}")

    # Emit done event with full summary
    emit("agent_done", {
        "agent": "profiling",
        "summary": {
            "rows": profile["shape"]["rows"],
            "columns": profile["shape"]["columns"],
            "missing_columns": len(profile["missing_values"]),
            "duplicate_rows": profile["duplicate_rows"],
            "numerical": len(profile["numerical_columns"]),
            "categorical": len(profile["categorical_columns"]),
            "insights": insights[:400]
        }
    })

    return state