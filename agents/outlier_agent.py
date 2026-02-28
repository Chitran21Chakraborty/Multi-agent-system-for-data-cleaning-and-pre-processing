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


def detect_outliers(df: pd.DataFrame) -> dict:
    num_cols = df.select_dtypes(include='number').columns.tolist()
    outlier_info = {}

    for col in num_cols:
        series = df[col].dropna()
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        iqr_outliers = ((series < Q1 - 1.5 * IQR) | (series > Q3 + 1.5 * IQR)).sum()
        z_scores = np.abs((series - series.mean()) / series.std())
        zscore_outliers = (z_scores > 3).sum()

        outlier_info[col] = {
            "iqr_outliers": int(iqr_outliers),
            "zscore_outliers": int(zscore_outliers),
            "iqr_outlier_pct": round(iqr_outliers / len(series) * 100, 2),
            "Q1": round(float(Q1), 4),
            "Q3": round(float(Q3), 4),
            "IQR": round(float(IQR), 4),
            "lower_bound": round(float(Q1 - 1.5 * IQR), 4),
            "upper_bound": round(float(Q3 + 1.5 * IQR), 4)
        }

    return outlier_info


def get_outlier_strategy(outlier_info: dict, objective: str) -> dict:
    llm = get_llm()

    cols_with_outliers = {
        col: info for col, info in outlier_info.items()
        if info["iqr_outliers"] > 0
    }

    if not cols_with_outliers:
        return {}

    prompt = f"""
You are an expert data scientist deciding outlier handling strategies.

Learning Objective: {objective}

Columns with outliers:
{format_outlier_info(cols_with_outliers)}

For each column, decide the best outlier handling strategy:
- winsorize: Cap outliers at the IQR bounds (best for keeping all rows, mild outliers)
- log_transform: Apply log transformation (best for right-skewed data with large outliers)
- drop_rows: Remove rows with outliers (only if outlier % is very small < 2%)
- keep: Keep outliers as-is (if they are legitimate values)

Important rules:
- For ID-like columns (PassengerId, id) always use keep
- For target columns always use keep
- For columns with outlier % > 20% prefer winsorize
- Return ONLY a Python dictionary like this:
{{"Fare": "winsorize", "Age": "keep", "SibSp": "winsorize"}}
No explanations, only the dictionary.
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return parse_strategy_dict(response.content)


def format_outlier_info(outlier_info: dict) -> str:
    lines = []
    for col, info in outlier_info.items():
        lines.append(
            f"- {col}: iqr_outliers={info['iqr_outliers']} ({info['iqr_outlier_pct']}%), "
            f"zscore_outliers={info['zscore_outliers']}, "
            f"bounds=[{info['lower_bound']}, {info['upper_bound']}]"
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


def apply_outlier_handling(df: pd.DataFrame, strategies: dict,
                            outlier_info: dict) -> tuple:
    df = df.copy()
    actions_taken = {}
    rows_before = len(df)

    for col, strategy in strategies.items():
        if col not in df.columns:
            continue

        if strategy == "winsorize":
            lower = outlier_info[col]["lower_bound"]
            upper = outlier_info[col]["upper_bound"]
            df[col] = df[col].clip(lower=lower, upper=upper)
            actions_taken[col] = f"Winsorized to [{lower}, {upper}]"

        elif strategy == "log_transform":
            min_val = df[col].min()
            if min_val <= 0:
                shift = abs(min_val) + 1
                df[col] = np.log(df[col] + shift)
                actions_taken[col] = f"Log transformed with shift ({shift})"
            else:
                df[col] = np.log(df[col])
                actions_taken[col] = "Log transformed"

        elif strategy == "drop_rows":
            lower = outlier_info[col]["lower_bound"]
            upper = outlier_info[col]["upper_bound"]
            before = len(df)
            df = df[(df[col] >= lower) & (df[col] <= upper)]
            after = len(df)
            actions_taken[col] = f"Dropped {before - after} outlier rows"

        elif strategy == "keep":
            actions_taken[col] = "Kept as-is (legitimate values)"

    rows_after = len(df)
    return df, actions_taken, rows_before, rows_after


def outlier_node(state: AgentState) -> AgentState:
    print("Outlier agent running...")

    # EMIT START
    emit("agent_start", {"agent": "outlier", "label": "Outlier Detection"})

    df = state.get("processed_dataframe")

    if df is None:
        state["errors"] = state.get("errors", []) + ["Outlier: No dataframe available"]
        emit("agent_done", {
            "agent": "outlier",
            "skipped": True,
            "reason": "No dataframe available"
        })
        return state

    # Detect outliers
    outlier_info = detect_outliers(df)
    cols_with_outliers = {
        col: info for col, info in outlier_info.items()
        if info["iqr_outliers"] > 0
    }

    print(f"  Columns with outliers: {list(cols_with_outliers.keys())}")

    if not cols_with_outliers:
        print("  No significant outliers found — skipping")
        state["outlier_report"] = {
            "status": "skipped",
            "reason": "No outliers detected",
            "outlier_info": outlier_info,
            "actions_taken": {}
        }
        state["current_agent"] = "outlier"

        emit("agent_done", {
            "agent": "outlier",
            "skipped": True,
            "reason": "No outliers detected in any column"
        })
        return state

    # Capture BEFORE distributions (before any changes)
    from agents.utils import capture_distributions
    outlier_cols_list = list(cols_with_outliers.keys())[:4]
    dist_before_outlier = capture_distributions(df, outlier_cols_list)

    # Get LLM strategy
    print("  Asking LLM for outlier handling strategy...")
    strategies = get_outlier_strategy(outlier_info, state["learning_objective"])
    print(f"  Strategies decided: {strategies}")

    # Apply strategies
    df_cleaned, actions_taken, rows_before, rows_after = apply_outlier_handling(
        df, strategies, outlier_info
    )

    state["processed_dataframe"] = df_cleaned
    state["outlier_report"] = {
        "status": "completed",
        "outlier_info": outlier_info,
        "strategies_used": strategies,
        "actions_taken": actions_taken,
        "rows_before": rows_before,
        "rows_after": rows_after
    }
    state["current_agent"] = "outlier"

    print(f"  Outlier handling complete — rows before: {rows_before}, after: {rows_after}")
    print(f"  Actions: {actions_taken}")

    # Capture AFTER distributions (on cleaned dataframe)
    dist_after = capture_distributions(df_cleaned, outlier_cols_list)

    # EMIT DONE
    emit("agent_done", {
        "agent": "outlier",
        "summary": {
            "columns_with_outliers": len(actions_taken),
            "rows_before": rows_before,
            "rows_after":  df_cleaned.shape[0],
            "rows_removed": rows_before - df_cleaned.shape[0]
        },
        "actions": actions_taken,
        "distributions": {
            "before": dist_before_outlier,
            "after":  dist_after
        }
    })

    return state