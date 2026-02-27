import pandas as pd
import numpy as np
from core.state import AgentState
from core.llm import get_llm
from langchain_core.messages import HumanMessage
from collections import Counter

_current_job_id = None

def set_job_id(job_id: str):
    global _current_job_id
    _current_job_id = job_id

def emit(event_type: str, data: dict):
    if _current_job_id:
        from api.stream import push_event_sync
        push_event_sync(_current_job_id, event_type, data)


def analyze_class_balance(df: pd.DataFrame, target_col: str) -> dict:
    if target_col not in df.columns:
        return {}

    counts = df[target_col].value_counts().to_dict()
    total = len(df)
    percentages = {str(k): round(v / total * 100, 2) for k, v in counts.items()}

    minority_count = min(counts.values())
    majority_count = max(counts.values())
    imbalance_ratio = round(majority_count / minority_count, 2)

    return {
        "class_counts": {str(k): int(v) for k, v in counts.items()},
        "class_percentages": percentages,
        "imbalance_ratio": imbalance_ratio,
        "is_imbalanced": imbalance_ratio > 1.5,
        "minority_class": str(min(counts, key=counts.get)),
        "majority_class": str(max(counts, key=counts.get)),
        "minority_count": int(minority_count),
        "majority_count": int(majority_count)
    }


def get_sampling_strategy(balance_info: dict, dataset_info: dict, objective: str) -> dict:
    llm = get_llm()
    prompt = f"""
You are an expert data scientist deciding on sampling strategies.

Learning Objective: {objective}

Dataset info:
- Total rows: {dataset_info['total_rows']}
- Number of features: {dataset_info['n_features']}

Class balance info:
- Class counts: {balance_info.get('class_counts', 'N/A')}
- Class percentages: {balance_info.get('class_percentages', 'N/A')}
- Imbalance ratio: {balance_info.get('imbalance_ratio', 'N/A')}
- Is imbalanced: {balance_info.get('is_imbalanced', False)}

Available strategies:
- oversample: Randomly duplicate minority class samples
  (simple, good for small datasets)
- undersample: Randomly remove majority class samples
  (use when dataset is large enough to afford losing data)
- smote: Synthetic Minority Oversampling Technique — generate synthetic samples
  (best for moderate imbalance, requires enough minority samples)
- none: No sampling needed
  (use when classes are balanced or task is not classification)

Rules:
- If imbalance_ratio < 1.5: always use none
- If total_rows < 500 and imbalanced: prefer oversample (not smote)
- If total_rows >= 500 and imbalanced: prefer smote
- If regression task: always use none
- Imbalance ratio > 3 is severe and needs handling

Return ONLY a Python dictionary like this:
{{"strategy": "smote", "reason": "moderate class imbalance ratio of 1.9"}}
or
{{"strategy": "none", "reason": "classes are sufficiently balanced"}}
No extra text, only the dictionary.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return parse_strategy_dict(response.content)


def parse_strategy_dict(response: str) -> dict:
    try:
        start = response.find("{")
        end = response.find("}") + 1
        if start != -1 and end != 0:
            dict_str = response[start:end]
            return eval(dict_str)
    except Exception:
        pass
    return {"strategy": "none", "reason": "Could not parse LLM response"}


def apply_oversample(df: pd.DataFrame, target_col: str, balance_info: dict) -> tuple:
    minority_class = balance_info["minority_class"]
    majority_count = balance_info["majority_count"]

    minority_df = df[df[target_col].astype(str) == minority_class]
    n_to_add = majority_count - len(minority_df)
    oversampled = minority_df.sample(n=n_to_add, replace=True, random_state=42)

    df_balanced = pd.concat([df, oversampled], ignore_index=True)
    df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)

    return df_balanced, f"Oversampled minority class from {len(minority_df)} to {majority_count}"


def apply_undersample(df: pd.DataFrame, target_col: str, balance_info: dict) -> tuple:
    minority_count = balance_info["minority_count"]
    majority_class = balance_info["majority_class"]

    minority_df = df[df[target_col].astype(str) != majority_class]
    majority_df = df[df[target_col].astype(str) == majority_class]

    majority_downsampled = majority_df.sample(n=minority_count, random_state=42)
    df_balanced = pd.concat([minority_df, majority_downsampled], ignore_index=True)
    df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)

    return df_balanced, f"Undersampled majority class from {len(majority_df)} to {minority_count}"


def apply_smote(df: pd.DataFrame, target_col: str) -> tuple:
    try:
        from imblearn.over_sampling import SMOTE

        feature_cols = [c for c in df.columns if c != target_col]
        X = df[feature_cols].values
        y = df[target_col].values

        smote = SMOTE(random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X, y)

        df_balanced = pd.DataFrame(X_resampled, columns=feature_cols)
        df_balanced[target_col] = y_resampled

        return df_balanced, "SMOTE applied — synthetic samples generated"

    except ImportError:
        return None, "SMOTE unavailable — falling back to oversample"


def find_target_column(df: pd.DataFrame, profiling_report: dict, objective: str) -> str:
    potential_targets = profiling_report.get("potential_target_columns", [])

    if "surviv" in objective.lower() and "Survived" in df.columns:
        return "Survived"

    if "classification" in objective.lower():
        for t in potential_targets:
            if t["type"] == "binary classification" and t["column"] in df.columns:
                return t["column"]

    return potential_targets[0]["column"] if potential_targets else df.columns[-1]


def sampling_node(state: AgentState) -> AgentState:
    print("Sampling agent running...")

    # EMIT START
    emit("agent_start", {"agent": "sampling", "label": "Sampling & Balancing"})

    df = state.get("processed_dataframe")
    profiling_report = state.get("profiling_report")

    if df is None or profiling_report is None:
        state["errors"] = state.get("errors", []) + ["Sampling: Missing dataframe or profiling report"]
        emit("agent_done", {
            "agent": "sampling",
            "skipped": True,
            "reason": "Missing dataframe or profiling report"
        })
        return state

    objective = state["learning_objective"]

    # Skip for regression
    if "regression" in objective.lower():
        print("  Regression task — sampling not applicable")
        state["sampling_report"] = {
            "status": "skipped",
            "reason": "Regression task — sampling not needed",
            "actions_taken": {}
        }
        state["current_agent"] = "sampling"

        # EMIT DONE — skipped
        emit("agent_done", {
            "agent": "sampling",
            "skipped": True,
            "reason": "Regression task — class balancing not applicable"
        })
        return state

    # Find target column
    target_col = find_target_column(df, profiling_report, objective)
    print(f"  Target column: {target_col}")

    # Analyze class balance
    balance_info = analyze_class_balance(df, target_col)

    if not balance_info:
        print("  Could not analyze class balance — skipping")
        state["sampling_report"] = {
            "status": "skipped",
            "reason": "Could not identify target column",
            "actions_taken": {}
        }
        state["current_agent"] = "sampling"

        # EMIT DONE — skipped
        emit("agent_done", {
            "agent": "sampling",
            "skipped": True,
            "reason": "Could not identify target column"
        })
        return state

    print(f"  Class distribution: {balance_info['class_counts']}")
    print(f"  Imbalance ratio: {balance_info['imbalance_ratio']}")

    dataset_info = {
        "total_rows": df.shape[0],
        "n_features": df.shape[1]
    }

    print("  Asking LLM for sampling strategy...")
    strategy_info = get_sampling_strategy(balance_info, dataset_info, objective)
    strategy = strategy_info.get("strategy", "none")
    print(f"  Strategy decided: {strategy_info}")

    shape_before = df.shape
    action_taken = ""

    if strategy == "oversample":
        df_balanced, action_taken = apply_oversample(df, target_col, balance_info)
        state["processed_dataframe"] = df_balanced

    elif strategy == "undersample":
        df_balanced, action_taken = apply_undersample(df, target_col, balance_info)
        state["processed_dataframe"] = df_balanced

    elif strategy == "smote":
        df_balanced, action_taken = apply_smote(df, target_col)
        if df_balanced is None:
            df_balanced, action_taken = apply_oversample(df, target_col, balance_info)
        state["processed_dataframe"] = df_balanced

    else:
        action_taken = strategy_info.get("reason", "No sampling needed")
        print(f"  No sampling applied — {action_taken}")

    shape_after = state["processed_dataframe"].shape

    state["sampling_report"] = {
        "status": "completed",
        "target_column": target_col,
        "strategy": strategy,
        "strategy_reason": strategy_info.get("reason", ""),
        "balance_before": balance_info,
        "action_taken": action_taken,
        "shape_before": shape_before,
        "shape_after": shape_after
    }
    state["current_agent"] = "sampling"

    print(f"  Sampling complete — shape before: {shape_before}, after: {shape_after}")

    # EMIT DONE
    emit("agent_done", {
        "agent": "sampling",
        "summary": {
            "target_column": target_col,
            "strategy": strategy,
            "imbalance_ratio": balance_info["imbalance_ratio"],
            "shape_before": f"{shape_before[0]} × {shape_before[1]}",
            "shape_after": f"{shape_after[0]} × {shape_after[1]}"
        },
        "actions": {target_col: action_taken}
    })

    return state