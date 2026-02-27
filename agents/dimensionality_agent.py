import pandas as pd
import numpy as np
from core.state import AgentState
from core.llm import get_llm
from langchain_core.messages import HumanMessage
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif, f_regression

_current_job_id = None

def set_job_id(job_id: str):
    global _current_job_id
    _current_job_id = job_id

def emit(event_type: str, data: dict):
    if _current_job_id:
        from api.stream import push_event_sync
        push_event_sync(_current_job_id, event_type, data)


def should_reduce(df: pd.DataFrame, objective: str) -> tuple:
    num_features = df.shape[1]
    num_rows = df.shape[0]
    ratio = num_rows / num_features
    reasons = []

    if num_features < 10:
        return False, f"Only {num_features} features — reduction not needed"

    if num_features >= 10:
        reasons.append(f"High feature count: {num_features}")

    if ratio < 10:
        reasons.append(f"Low row-to-feature ratio: {ratio:.1f}")

    return len(reasons) > 0, ", ".join(reasons) if reasons else "Sufficient features"


def get_reduction_strategy(df_info: dict, objective: str) -> dict:
    llm = get_llm()
    prompt = f"""
You are an expert data scientist deciding on dimensionality reduction.

Learning Objective: {objective}

Dataset info:
- Number of features: {df_info['n_features']}
- Number of rows: {df_info['n_rows']}
- Row to feature ratio: {df_info['ratio']:.1f}
- Feature names: {df_info['feature_names']}
- Contains binary/encoded columns: {df_info['has_binary']}

Available strategies:
- pca: Principal Component Analysis — reduces to n components explaining 95% variance
  (best when features are correlated, loses interpretability)
- select_k_best: Keep top K most important features using statistical tests
  (best when interpretability matters, keeps original feature names)
- none: No dimensionality reduction needed
  (best when feature count is manageable and interpretability is important)

Important rules:
- If features < 15, prefer none or select_k_best over pca
- If task is classification use select_k_best with f_classif
- If task is regression use select_k_best with f_regression
- If many correlated features exist, prefer pca
- Always preserve interpretability when possible

Return ONLY a Python dictionary like this:
{{"strategy": "select_k_best", "k": 8, "reason": "preserves interpretability for classification"}}
or
{{"strategy": "pca", "n_components": 0.95, "reason": "many correlated features"}}
or
{{"strategy": "none", "reason": "feature count is manageable"}}
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


def apply_pca(df: pd.DataFrame, target_col: str, n_components: float) -> tuple:
    feature_cols = [c for c in df.columns if c != target_col]
    X = df[feature_cols].values

    pca = PCA(n_components=n_components)
    X_reduced = pca.fit_transform(X)

    pca_cols = [f"PC{i+1}" for i in range(X_reduced.shape[1])]
    df_reduced = pd.DataFrame(X_reduced, columns=pca_cols, index=df.index)

    if target_col and target_col in df.columns:
        df_reduced[target_col] = df[target_col].values

    variance_explained = pca.explained_variance_ratio_.cumsum()[-1]
    return df_reduced, pca_cols, float(variance_explained)


def apply_select_k_best(df: pd.DataFrame, target_col: str,
                         k: int, objective: str) -> tuple:
    feature_cols = [c for c in df.columns if c != target_col]

    if k >= len(feature_cols):
        k = len(feature_cols)

    X = df[feature_cols].values
    y = df[target_col].values if target_col in df.columns else None

    if y is None:
        return df, feature_cols, 1.0

    score_func = f_regression if "regression" in objective.lower() else f_classif

    selector = SelectKBest(score_func=score_func, k=k)
    selector.fit(X, y)

    selected_mask = selector.get_support()
    selected_features = [feature_cols[i] for i, selected in
                         enumerate(selected_mask) if selected]

    cols_to_keep = selected_features + ([target_col] if target_col in df.columns else [])
    df_reduced = df[cols_to_keep].copy()

    scores = dict(zip(feature_cols, selector.scores_))
    scores = {k: round(float(v), 4) for k, v in scores.items()}

    return df_reduced, selected_features, scores


def find_target_column(df: pd.DataFrame, profiling_report: dict,
                        objective: str) -> str:
    potential_targets = profiling_report.get("potential_target_columns", [])

    if "surviv" in objective.lower() and "Survived" in df.columns:
        return "Survived"

    if "classification" in objective.lower():
        for t in potential_targets:
            if t["type"] == "binary classification" and t["column"] in df.columns:
                return t["column"]

    if "regression" in objective.lower():
        num_cols = df.select_dtypes(include='number').columns.tolist()
        if num_cols:
            return num_cols[-1]

    return potential_targets[0]["column"] if potential_targets else df.columns[-1]


def dimensionality_node(state: AgentState) -> AgentState:
    print("Dimensionality reduction agent running...")

    # EMIT START
    emit("agent_start", {"agent": "dimensionality", "label": "Dimensionality Reduction"})

    df = state.get("processed_dataframe")
    profiling_report = state.get("profiling_report")

    if df is None or profiling_report is None:
        state["errors"] = state.get("errors", []) + ["Dimensionality: Missing dataframe or profiling report"]
        emit("agent_done", {
            "agent": "dimensionality",
            "skipped": True,
            "reason": "Missing dataframe or profiling report"
        })
        return state

    # Check if reduction is needed
    needed, reason = should_reduce(df, state["learning_objective"])

    if not needed:
        print(f"  Dimensionality reduction not needed — {reason}")
        state["dimensionality_report"] = {
            "status": "skipped",
            "reason": reason,
            "actions_taken": {}
        }
        state["current_agent"] = "dimensionality"

        # EMIT DONE — skipped
        emit("agent_done", {
            "agent": "dimensionality",
            "skipped": True,
            "reason": reason
        })
        return state

    # Build dataset info for LLM
    num_cols = df.select_dtypes(include='number').columns.tolist()
    has_binary = any(df[c].nunique() == 2 for c in num_cols)

    df_info = {
        "n_features": df.shape[1],
        "n_rows": df.shape[0],
        "ratio": df.shape[0] / df.shape[1],
        "feature_names": df.columns.tolist(),
        "has_binary": has_binary
    }

    print(f"  Features: {df.shape[1]}, Rows: {df.shape[0]}")
    print("  Asking LLM for dimensionality reduction strategy...")

    strategy_info = get_reduction_strategy(df_info, state["learning_objective"])
    strategy = strategy_info.get("strategy", "none")
    print(f"  Strategy decided: {strategy_info}")

    target_col = find_target_column(df, profiling_report, state["learning_objective"])
    print(f"  Target column identified: {target_col}")

    actions_taken = {}
    shape_before = df.shape

    if strategy == "pca":
        n_components = strategy_info.get("n_components", 0.95)
        df_reduced, new_cols, variance = apply_pca(df, target_col, n_components)
        state["processed_dataframe"] = df_reduced
        actions_taken = {
            "method": "PCA",
            "components": len(new_cols),
            "variance_explained": f"{variance:.2%}",
            "new_columns": new_cols
        }
        print(f"  PCA applied — {shape_before[1]} → {df_reduced.shape[1]} features, "
              f"variance explained: {variance:.2%}")

    elif strategy == "select_k_best":
        k = strategy_info.get("k", max(5, df.shape[1] // 2))
        df_reduced, selected, scores = apply_select_k_best(
            df, target_col, k, state["learning_objective"]
        )
        state["processed_dataframe"] = df_reduced
        actions_taken = {
            "method": "SelectKBest",
            "k": k,
            "selected_features": selected,
            "feature_scores": scores
        }
        print(f"  SelectKBest applied — {shape_before[1]} → {df_reduced.shape[1]} features")
        print(f"  Selected features: {selected}")

    else:
        state["processed_dataframe"] = df
        actions_taken = {"method": "none", "reason": strategy_info.get("reason", "Not needed")}
        print(f"  No reduction applied — {strategy_info.get('reason')}")

    state["dimensionality_report"] = {
        "status": "completed",
        "strategy": strategy,
        "strategy_reason": strategy_info.get("reason", ""),
        "actions_taken": actions_taken,
        "shape_before": shape_before,
        "shape_after": state["processed_dataframe"].shape
    }
    state["current_agent"] = "dimensionality"

    # EMIT DONE
    emit("agent_done", {
        "agent": "dimensionality",
        "summary": {
            "strategy": strategy,
            "features_before": shape_before[1],
            "features_after": state["processed_dataframe"].shape[1],
            "reason": strategy_info.get("reason", "")
        },
        "actions": {k: str(v) for k, v in actions_taken.items()}
    })

    return state