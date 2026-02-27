import pandas as pd
import numpy as np
from core.state import AgentState
from core.llm import get_llm
from langchain_core.messages import HumanMessage

_current_job_id = None

def set_job_id(job_id: str):
    global _current_job_id
    _current_job_id = job_id

def emit(event_type: str, data: dict):
    if _current_job_id:
        from api.stream import push_event_sync
        push_event_sync(_current_job_id, event_type, data)


def get_imputation_strategy(missing_info: dict, col_stats: dict,
                             cat_stats: dict, objective: str) -> dict:
    llm = get_llm()
    prompt = f"""
You are an expert data scientist deciding imputation strategies for missing values.

Learning Objective: {objective}

Columns with missing values:
{format_missing_info(missing_info, col_stats, cat_stats)}

For each column with missing values, decide the best imputation strategy.
Available strategies:
- mean: Replace with column mean (use for numerical, low skewness)
- median: Replace with column median (use for numerical, high skewness or outliers)
- mode: Replace with most frequent value (use for categorical)
- constant: Replace with a fixed value like "Unknown" (use for high missing % categorical)
- drop_column: Drop the entire column (use when missing % is very high and column is not useful)
- drop_rows: Drop rows with missing values (use when missing % is very low)

Return ONLY a Python dictionary like this example:
{{"Age": "median", "Cabin": "drop_column", "Embarked": "mode"}}

No explanations, only the dictionary.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return parse_strategy_dict(response.content)


def format_missing_info(missing_info: dict, num_stats: dict, cat_stats: dict) -> str:
    lines = []
    for col, info in missing_info.items():
        col_type = "numerical" if col in num_stats else "categorical"
        lines.append(f"- {col}: {info['percentage']}% missing, type={col_type}")
        if col in num_stats:
            stats = num_stats[col]
            lines.append(f"  skewness={stats['skewness']}, outliers={stats['outliers_iqr']}")
        elif col in cat_stats:
            stats = cat_stats[col]
            lines.append(f"  unique_values={stats['unique_values']}, cardinality={stats['cardinality']}")
    return "\n".join(lines)


def parse_strategy_dict(response: str) -> dict:
    try:
        start = response.find("{")
        end = response.find("}") + 1
        if start != -1 and end != 0:
            dict_str = response[start:end]
            return eval(dict_str)
    except Exception:
        pass
    return {}


def apply_imputation(df: pd.DataFrame, strategies: dict) -> tuple:
    df = df.copy()
    actions_taken = {}
    cols_to_drop = []

    for col, strategy in strategies.items():
        if col not in df.columns:
            continue

        if strategy == "mean":
            fill_value = df[col].mean()
            df[col] = df[col].fillna(fill_value)
            actions_taken[col] = f"Filled with mean ({round(fill_value, 4)})"

        elif strategy == "median":
            fill_value = df[col].median()
            df[col] = df[col].fillna(fill_value)
            actions_taken[col] = f"Filled with median ({round(fill_value, 4)})"

        elif strategy == "mode":
            fill_value = df[col].mode()[0]
            df[col] = df[col].fillna(fill_value)
            actions_taken[col] = f"Filled with mode ({fill_value})"

        elif strategy == "constant":
            df[col] = df[col].fillna("Unknown")
            actions_taken[col] = "Filled with constant (Unknown)"

        elif strategy == "drop_column":
            cols_to_drop.append(col)
            actions_taken[col] = "Column dropped due to high missing percentage"

        elif strategy == "drop_rows":
            before = len(df)
            df = df.dropna(subset=[col])
            after = len(df)
            actions_taken[col] = f"Dropped {before - after} rows with missing values"

    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    return df, actions_taken


def imputation_node(state: AgentState) -> AgentState:
    print("Imputation agent running...")

    # EMIT START
    emit("agent_start", {"agent": "imputation", "label": "Missing Value Imputation"})

    profiling_report = state.get("profiling_report")
    df = state.get("processed_dataframe")

    if df is None or profiling_report is None:
        state["errors"] = state.get("errors", []) + ["Imputation: Missing dataframe or profiling report"]
        emit("agent_done", {
            "agent": "imputation",
            "skipped": True,
            "reason": "Missing dataframe or profiling report"
        })
        return state

    missing_info = profiling_report.get("missing_values", {})

    if not missing_info:
        print("  No missing values found — skipping imputation")
        state["imputation_report"] = {
            "status": "skipped",
            "reason": "No missing values in dataset",
            "actions_taken": {}
        }
        state["current_agent"] = "imputation"

        # EMIT DONE — skipped
        emit("agent_done", {
            "agent": "imputation",
            "skipped": True,
            "reason": "No missing values in dataset"
        })
        return state

    print(f"  Missing values found in: {list(missing_info.keys())}")
    print("  Asking LLM for imputation strategy...")

    strategies = get_imputation_strategy(
        missing_info,
        profiling_report.get("numerical_columns", {}),
        profiling_report.get("categorical_columns", {}),
        state["learning_objective"]
    )

    print(f"  Strategies decided: {strategies}")

    # Apply imputation
    df_imputed, actions_taken = apply_imputation(df, strategies)

    remaining_missing = df_imputed.isnull().sum()
    remaining_missing = remaining_missing[remaining_missing > 0].to_dict()

    shape_before = df.shape
    shape_after = df_imputed.shape

    state["processed_dataframe"] = df_imputed
    state["imputation_report"] = {
        "status": "completed",
        "strategies_used": strategies,
        "actions_taken": actions_taken,
        "remaining_missing": remaining_missing,
        "shape_before": shape_before,
        "shape_after": shape_after
    }
    state["current_agent"] = "imputation"

    print(f"  Imputation complete — shape before: {shape_before}, after: {shape_after}")
    print(f"  Actions: {actions_taken}")

    # EMIT DONE
    emit("agent_done", {
        "agent": "imputation",
        "summary": {
            "columns_treated": len(strategies),
            "remaining_missing": len(remaining_missing),
            "shape_before": f"{shape_before[0]} × {shape_before[1]}",
            "shape_after": f"{shape_after[0]} × {shape_after[1]}"
        },
        "actions": actions_taken
    })

    return state