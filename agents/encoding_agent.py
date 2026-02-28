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


def get_encoding_strategy(cat_cols_info: dict, objective: str) -> dict:
    llm = get_llm()
    prompt = f"""
You are an expert data scientist deciding encoding strategies for categorical columns.

Learning Objective: {objective}

Categorical columns to encode:
{format_cat_info(cat_cols_info)}

For each column, decide the best encoding strategy:
- onehot: One-hot encoding (best for low cardinality, no ordinal relationship)
- label: Label encoding (best for binary or ordinal categories)
- drop: Drop the column (if it's an ID, free text, or not useful e.g. Name, Ticket)
- frequency: Replace with frequency count (best for high cardinality)
- keep: Keep as-is (if already numerical or will not be used)

Important rules:
- Name, Ticket, and similar free-text ID columns should always be dropped
- Binary columns like Sex should use label encoding
- Low cardinality columns like Embarked should use onehot
- High cardinality columns (unique > 20) should use frequency or drop

Return ONLY a Python dictionary like this:
{{"Sex": "label", "Embarked": "onehot", "Name": "drop", "Ticket": "drop"}}
No explanations, only the dictionary.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return parse_strategy_dict(response.content)


def format_cat_info(cat_cols_info: dict) -> str:
    lines = []
    for col, info in cat_cols_info.items():
        lines.append(
            f"- {col}: unique_values={info['unique_values']}, "
            f"cardinality={info['cardinality']}, "
            f"top_values={list(info['top_5_values'].keys())[:3]}"
        )
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


def apply_encoding(df: pd.DataFrame, strategies: dict) -> tuple:
    df = df.copy()
    actions_taken = {}
    cols_to_drop = []
    new_columns_created = []

    for col, strategy in strategies.items():
        if col not in df.columns:
            continue

        if strategy == "onehot":
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=False)
            dummies = dummies.astype(int)
            df = pd.concat([df, dummies], axis=1)
            cols_to_drop.append(col)
            new_cols = dummies.columns.tolist()
            new_columns_created.extend(new_cols)
            actions_taken[col] = f"One-hot encoded → {new_cols}"

        elif strategy == "label":
            unique_vals = df[col].unique()
            mapping = {val: idx for idx, val in enumerate(sorted(
                [v for v in unique_vals if pd.notna(v)])
            )}
            df[col] = df[col].map(mapping)
            actions_taken[col] = f"Label encoded → {mapping}"

        elif strategy == "frequency":
            freq_map = df[col].value_counts(normalize=True).to_dict()
            df[col] = df[col].map(freq_map)
            actions_taken[col] = f"Frequency encoded ({len(freq_map)} unique values)"

        elif strategy == "drop":
            cols_to_drop.append(col)
            actions_taken[col] = "Dropped (not useful for ML)"

        elif strategy == "keep":
            actions_taken[col] = "Kept as-is"

    existing_cols_to_drop = [c for c in cols_to_drop if c in df.columns]
    df = df.drop(columns=existing_cols_to_drop)

    return df, actions_taken, new_columns_created


def classify_cardinality(n_unique: int) -> str:
    if n_unique <= 2:
        return "binary"
    elif n_unique <= 10:
        return "low"
    elif n_unique <= 50:
        return "medium"
    else:
        return "high"


def encoding_node(state: AgentState) -> AgentState:
    print("Encoding agent running...")

    # EMIT START
    emit("agent_start", {"agent": "encoding", "label": "Categorical Encoding"})

    df = state.get("processed_dataframe")
    profiling_report = state.get("profiling_report")

    if df is None or profiling_report is None:
        state["errors"] = state.get("errors", []) + ["Encoding: Missing dataframe or profiling report"]
        emit("agent_done", {
            "agent": "encoding",
            "skipped": True,
            "reason": "Missing dataframe or profiling report"
        })
        return state

    # Capture original df BEFORE any changes
    original_df = df.copy()

    # Get current categorical columns
    cat_cols = df.select_dtypes(include='object').columns.tolist()

    if not cat_cols:
        print("  No categorical columns found — skipping encoding")
        state["encoding_report"] = {
            "status": "skipped",
            "reason": "No categorical columns found",
            "actions_taken": {}
        }
        state["current_agent"] = "encoding"

        emit("agent_done", {
            "agent": "encoding",
            "skipped": True,
            "reason": "No categorical columns found"
        })
        return state

    # Build cat info from profiling report + current df state
    cat_cols_info = {}
    profiled_cats = profiling_report.get("categorical_columns", {})
    for col in cat_cols:
        if col in profiled_cats:
            cat_cols_info[col] = profiled_cats[col]
        else:
            cat_cols_info[col] = {
                "unique_values": df[col].nunique(),
                "cardinality": classify_cardinality(df[col].nunique()),
                "top_5_values": df[col].value_counts().head(5).to_dict()
            }

    print(f"  Categorical columns to encode: {cat_cols}")
    print("  Asking LLM for encoding strategy...")

    strategies = get_encoding_strategy(cat_cols_info, state["learning_objective"])
    print(f"  Strategies decided: {strategies}")

    # Record shape before encoding
    shape_before = df.shape

    # Apply encoding
    df_encoded, actions_taken, new_columns = apply_encoding(df, strategies)

    shape_after = df_encoded.shape

    state["processed_dataframe"] = df_encoded
    state["encoding_report"] = {
        "status": "completed",
        "strategies_used": strategies,
        "actions_taken": actions_taken,
        "new_columns_created": new_columns,
        "shape_before": shape_before,
        "shape_after": shape_after
    }
    state["current_agent"] = "encoding"

    print(f"  Encoding complete — shape before: {shape_before}, after: {shape_after}")
    print(f"  New columns created: {new_columns}")

    # Capture BEFORE and AFTER distributions for charts
    from agents.utils import capture_distributions
    encoded_cols = list(actions_taken.keys())[:4]
    dist_before = capture_distributions(original_df, encoded_cols)
    dist_after  = capture_distributions(df_encoded, encoded_cols)

    # EMIT DONE
    emit("agent_done", {
        "agent": "encoding",
        "summary": {
            "columns_encoded":     len(strategies),
            "new_columns_created": len(new_columns),
            "shape_before": f"{shape_before[0]} × {shape_before[1]}",
            "shape_after":  f"{shape_after[0]} × {shape_after[1]}"
        },
        "actions": actions_taken,
        "distributions": {
            "before": dist_before,
            "after":  dist_after
        }
    })

    return state