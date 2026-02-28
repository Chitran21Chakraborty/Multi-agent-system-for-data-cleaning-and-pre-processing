import pandas as pd
import numpy as np
from core.state import AgentState
from core.llm import get_llm
from langchain_core.messages import HumanMessage
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

_current_job_id = None

def set_job_id(job_id: str):
    global _current_job_id
    _current_job_id = job_id

def emit(event_type: str, data: dict):
    if _current_job_id:
        from api.stream import push_event_sync
        push_event_sync(_current_job_id, event_type, data)


def get_transformation_strategy(num_cols_info: dict, objective: str) -> dict:
    llm = get_llm()
    prompt = f"""
You are an expert data scientist deciding feature scaling and transformation strategies.

Learning Objective: {objective}

Numerical columns to transform:
{format_num_info(num_cols_info)}

For each column, decide the best transformation strategy:
- standard_scaler: Standardize to mean=0, std=1 (best for normally distributed data)
- minmax_scaler: Scale to [0,1] range (best for bounded data, neural networks)
- robust_scaler: Scale using median and IQR (best for data with outliers)
- log_transform: Apply log transformation (best for right-skewed data)
- keep: Keep as-is (best for binary columns, target columns, or ID columns)

Important rules:
- PassengerId or any ID column: always keep
- Binary columns (only 0 and 1 values): always keep
- Target column (Survived): always keep
- Highly skewed columns (skewness > 1): prefer log_transform or robust_scaler
- Columns with outliers: prefer robust_scaler
- For classification tasks: standard_scaler or robust_scaler usually best

Return ONLY a Python dictionary like this:
{{"Age": "standard_scaler", "Fare": "robust_scaler", "PassengerId": "keep"}}
No explanations, only the dictionary.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return parse_strategy_dict(response.content)


def format_num_info(num_cols_info: dict) -> str:
    lines = []
    for col, info in num_cols_info.items():
        lines.append(
            f"- {col}: mean={info['mean']}, std={info['std']}, "
            f"skewness={info['skewness']}, "
            f"outliers={info['outliers_iqr']}, "
            f"range=[{info['min']}, {info['max']}]"
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


def apply_transformations(df: pd.DataFrame, strategies: dict) -> tuple:
    df = df.copy()
    actions_taken = {}
    scalers_used = {}

    for col, strategy in strategies.items():
        if col not in df.columns:
            continue

        values = df[[col]].values

        if strategy == "standard_scaler":
            scaler = StandardScaler()
            df[col] = scaler.fit_transform(values).flatten()
            scalers_used[col] = "StandardScaler"
            actions_taken[col] = (
                f"Standard scaled (mean={round(float(scaler.mean_[0]),4)}, "
                f"std={round(float(scaler.scale_[0]),4)})"
            )

        elif strategy == "minmax_scaler":
            scaler = MinMaxScaler()
            df[col] = scaler.fit_transform(values).flatten()
            scalers_used[col] = "MinMaxScaler"
            actions_taken[col] = (
                f"MinMax scaled to [0,1] "
                f"(original range [{round(float(scaler.data_min_[0]),4)}, "
                f"{round(float(scaler.data_max_[0]),4)}])"
            )

        elif strategy == "robust_scaler":
            scaler = RobustScaler()
            df[col] = scaler.fit_transform(values).flatten()
            scalers_used[col] = "RobustScaler"
            actions_taken[col] = "Robust scaled using median and IQR"

        elif strategy == "log_transform":
            min_val = df[col].min()
            if min_val <= 0:
                shift = abs(min_val) + 1
                df[col] = np.log(df[col] + shift)
                actions_taken[col] = f"Log transformed with shift ({shift})"
            else:
                df[col] = np.log(df[col])
                actions_taken[col] = "Log transformed"

        elif strategy == "keep":
            actions_taken[col] = "Kept as-is"

    return df, actions_taken, scalers_used


def count_outliers_iqr(series: pd.Series) -> int:
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    return int(((series < Q1 - 1.5 * IQR) | (series > Q3 + 1.5 * IQR)).sum())


def transformation_node(state: AgentState) -> AgentState:
    print("Transformation agent running...")

    # EMIT START
    emit("agent_start", {"agent": "transformation", "label": "Feature Transformation"})

    df = state.get("processed_dataframe")
    profiling_report = state.get("profiling_report")

    if df is None or profiling_report is None:
        state["errors"] = state.get("errors", []) + ["Transformation: Missing dataframe or profiling report"]
        emit("agent_done", {
            "agent": "transformation",
            "skipped": True,
            "reason": "Missing dataframe or profiling report"
        })
        return state

    num_cols = df.select_dtypes(include='number').columns.tolist()

    if not num_cols:
        print("  No numerical columns found — skipping transformation")
        state["transformation_report"] = {
            "status": "skipped",
            "reason": "No numerical columns found",
            "actions_taken": {}
        }
        state["current_agent"] = "transformation"

        # EMIT DONE — skipped
        emit("agent_done", {
            "agent": "transformation",
            "skipped": True,
            "reason": "No numerical columns found"
        })
        return state

    # Build num cols info — use profiling report where available
    num_cols_info = {}
    profiled_nums = profiling_report.get("numerical_columns", {})

    for col in num_cols:
        if col in profiled_nums:
            num_cols_info[col] = profiled_nums[col]
        else:
            num_cols_info[col] = {
                "mean": round(float(df[col].mean()), 4),
                "std": round(float(df[col].std()), 4),
                "min": round(float(df[col].min()), 4),
                "max": round(float(df[col].max()), 4),
                "skewness": round(float(df[col].skew()), 4),
                "outliers_iqr": int(count_outliers_iqr(df[col]))
            }

    print(f"  Numerical columns to transform: {num_cols}")

    # Capture before distributions
    from agents.utils import capture_distributions
    dist_before = capture_distributions(df, num_cols[:4])

    print("  Asking LLM for transformation strategy...")
    strategies = get_transformation_strategy(num_cols_info, state["learning_objective"])
    print(f"  Strategies decided: {strategies}")

    # Apply transformations
    df_transformed, actions_taken, scalers_used = apply_transformations(df, strategies)

    state["processed_dataframe"] = df_transformed
    state["transformation_report"] = {
        "status": "completed",
        "strategies_used": strategies,
        "actions_taken": actions_taken,
        "scalers_used": scalers_used,
        "shape": df_transformed.shape
    }
    state["current_agent"] = "transformation"

    print(f"  Transformation complete — {len(actions_taken)} columns transformed")
    print(f"  Actions: {actions_taken}")

    # EMIT DONE
    from agents.utils import capture_distributions
    dist_after = capture_distributions(df_transformed, list(dist_before.keys()))

    emit("agent_done", {
        "agent": "transformation",
        "summary": {
            "columns_transformed": len(actions_taken),
            "standard_scaled": len([s for s in strategies.values() if s == "standard_scaler"]),
            "robust_scaled": len([s for s in strategies.values() if s == "robust_scaler"]),
            "log_transformed": len([s for s in strategies.values() if s == "log_transform"]),
            "kept_as_is": len([s for s in strategies.values() if s == "keep"])
        },
        "actions": actions_taken,
        "distributions": {
            "before": dist_before,
            "after":  dist_after
        }
    })

    return state