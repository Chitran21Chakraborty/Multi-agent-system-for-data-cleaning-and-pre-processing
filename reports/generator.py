import os
import pandas as pd
from datetime import datetime
from core.state import AgentState
from core.llm import get_llm
from langchain_core.messages import HumanMessage


def build_executive_summary(state: AgentState) -> str:
    """Use LLM to write an executive summary of the entire preprocessing."""
    llm = get_llm()

    agents_run = state.get("agents_to_run", [])
    profiling = state.get("profiling_report", {})
    imputation = state.get("imputation_report", {})
    encoding = state.get("encoding_report", {})
    transformation = state.get("transformation_report", {})
    outlier = state.get("outlier_report", {})
    dimensionality = state.get("dimensionality_report", {})
    sampling = state.get("sampling_report", {})

    original_shape = profiling.get("shape", {})
    final_shape = state.get("processed_dataframe").shape if state.get("processed_dataframe") is not None else "N/A"

    prompt = f"""
You are an expert data scientist writing an executive summary of a data preprocessing pipeline.

Dataset: {state.get('dataset_path', 'Unknown')}
Learning Objective: {state.get('learning_objective', 'Unknown')}
Original Shape: {original_shape}
Final Shape: {final_shape}
Agents Run: {agents_run}

Key Actions Performed:
- Imputation: {imputation.get('actions_taken', 'Skipped') if imputation else 'Skipped'}
- Encoding: {encoding.get('actions_taken', 'Skipped') if encoding else 'Skipped'}
- Outlier Handling: {outlier.get('actions_taken', 'Skipped') if outlier else 'Skipped'}
- Transformation: {transformation.get('actions_taken', 'Skipped') if transformation else 'Skipped'}
- Dimensionality: {dimensionality.get('actions_taken', 'Skipped') if dimensionality else 'Skipped'}
- Sampling: {sampling.get('action_taken', 'Skipped') if sampling else 'Skipped'}

Write a concise executive summary (150-200 words) covering:
1. What the dataset looked like originally
2. Key issues found and how they were handled
3. What the final preprocessed dataset looks like
4. Whether it is ready for the stated learning objective

Write in clear professional language suitable for a data science report.
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


def format_report_markdown(state: AgentState, summary: str) -> str:
    """Format the complete report as markdown."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    profiling = state.get("profiling_report", {})
    imputation = state.get("imputation_report", {})
    encoding = state.get("encoding_report", {})
    transformation = state.get("transformation_report", {})
    outlier = state.get("outlier_report", {})
    dimensionality = state.get("dimensionality_report", {})
    sampling = state.get("sampling_report", {})
    df_final = state.get("processed_dataframe")

    summary = clean_summary(summary)
    agents_run = state.get('agents_to_run', [])
    report = f"""# AutoClean Preprocessing Report

> A clear, reproducible record of the decisions made while preparing your dataset for modeling.

## Report Details

| Field | Value |
|---|---|
| Generated | {now} |
| Dataset | `{os.path.basename(str(state.get('dataset_path', 'Unknown')) )}` |
| Learning objective | {state.get('learning_objective', 'Unknown')} |
| Processing stages applied | {', '.join(agents_run) if agents_run else 'None'} |

---

## Executive Summary
{summary}

---

## 1. Data Profiling

| Metric | Value |
|--------|-------|
| Original Rows | {profiling.get('shape', {}).get('rows', 'N/A')} |
| Original Columns | {profiling.get('shape', {}).get('columns', 'N/A')} |
| Numerical Columns | {len(profiling.get('numerical_columns', {}))} |
| Categorical Columns | {len(profiling.get('categorical_columns', {}))} |
| Duplicate Rows | {profiling.get('duplicate_rows', 0)} |
| Columns with Missing Values | {len(profiling.get('missing_values', {}))} |

### Missing Values
{format_missing_table(profiling.get('missing_values', {}))}

### LLM Data Insights
{profiling.get('llm_insights', 'No insights available')}

---

## 2. Imputation
{format_agent_section(imputation, 'actions_taken')}

---

## 3. Outlier Handling
{format_agent_section(outlier, 'actions_taken')}

---

## 4. Categorical Encoding
{format_agent_section(encoding, 'actions_taken')}

---

## 5. Feature Transformation
{format_agent_section(transformation, 'actions_taken')}

---

## 6. Dimensionality Reduction
{format_dimensionality_section(dimensionality)}

---

## 7. Sampling
{format_sampling_section(sampling)}

---

## 8. Final Dataset Summary

| Metric | Value |
|--------|-------|
| Final Rows | {df_final.shape[0] if df_final is not None else 'N/A'} |
| Final Columns | {df_final.shape[1] if df_final is not None else 'N/A'} |
| Final Column Names | {', '.join(df_final.columns.tolist()) if df_final is not None else 'N/A'} |
| Missing Values Remaining | {int(df_final.isnull().sum().sum()) if df_final is not None else 'N/A'} |
| Data Types | All Numerical |

---

## 9. Errors & Warnings
{format_messages('Errors', state.get('errors', []))}

{format_messages('Warnings', state.get('warnings', []))}

---
*Report generated by AutoClean*
"""
    return report


def clean_summary(summary: str) -> str:
    """Remove duplicate heading text when the LLM adds its own title."""
    cleaned = (summary or "No executive summary was generated.").strip()
    for heading in ("**Executive Summary**", "## Executive Summary", "### Executive Summary"):
        if cleaned.lower().startswith(heading.lower()):
            cleaned = cleaned[len(heading):].lstrip(" :\n")
            break
    return cleaned


def format_messages(label: str, messages: list) -> str:
    if not messages:
        return f"**{label}:** None"
    return "**{}:**\n{}".format(
        label,
        "\n".join(f"- {message}" for message in messages)
    )


def format_missing_table(missing: dict) -> str:
    if not missing:
        return "No missing values found"
    lines = ["| Column | Missing Count | Percentage |",
             "|--------|--------------|------------|"]
    for col, info in missing.items():
        lines.append(f"| {col} | {info['count']} | {info['percentage']}% |")
    return "\n".join(lines)


def format_agent_section(report: dict, actions_key: str) -> str:
    if not report:
        return "**Status:** Skipped by orchestrator"
    if report.get("status") == "skipped":
        return f"**Status:** Skipped  \n**Reason:** {report.get('reason', 'Not needed')}"
    actions = report.get(actions_key, {})
    if not actions:
        return "**Status:** Completed  \nNo actions were required."
    lines = ["**Status:** Completed", "", "| Column | Action |", "|---|---|"]
    for col, action in actions.items():
        lines.append(f"| {col} | {action} |")
    return "\n".join(lines)


def format_dimensionality_section(report: dict) -> str:
    if not report:
        return "Skipped by orchestrator"
    if report.get("status") == "skipped":
        return f"Skipped — {report.get('reason', 'Not needed')}"
    actions = report.get("actions_taken", {})
    method = actions.get("method", "N/A")
    if method == "none":
        return f"No reduction applied — {actions.get('reason', '')}"
    lines = [f"**Method:** {method}"]
    if method == "PCA":
        lines.append(f"**Components:** {actions.get('components', 'N/A')}")
        lines.append(f"**Variance Explained:** {actions.get('variance_explained', 'N/A')}")
    elif method == "SelectKBest":
        lines.append(f"**Features Selected:** {actions.get('k', 'N/A')}")
        lines.append(f"**Selected Features:** {actions.get('selected_features', 'N/A')}")
    return "\n".join(lines)


def format_sampling_section(report: dict) -> str:
    if not report:
        return "Skipped by orchestrator"
    if report.get("status") == "skipped":
        return f"Skipped — {report.get('reason', 'Not needed')}"
    balance = report.get("balance_before", {})
    lines = [
        f"**Target Column:** {report.get('target_column', 'N/A')}",
        f"**Strategy:** {report.get('strategy', 'N/A')}",
        f"**Reason:** {report.get('strategy_reason', 'N/A')}",
        f"**Class Distribution Before:** {balance.get('class_counts', 'N/A')}",
        f"**Imbalance Ratio:** {balance.get('imbalance_ratio', 'N/A')}",
        f"**Action:** {report.get('action_taken', 'N/A')}",
        f"**Shape Before:** {report.get('shape_before', 'N/A')}",
        f"**Shape After:** {report.get('shape_after', 'N/A')}"
    ]
    return "\n".join(lines)


def generate_preprocessing_script(state: AgentState) -> str:
    """Generate a reproducible Python script from the pipeline decisions."""
    imputation = state.get("imputation_report", {})
    encoding = state.get("encoding_report", {})
    transformation = state.get("transformation_report", {})
    outlier = state.get("outlier_report", {})

    imp_actions = imputation.get("actions_taken", {}) if imputation else {}
    enc_strategies = encoding.get("strategies_used", {}) if encoding else {}
    trans_strategies = transformation.get("strategies_used", {}) if transformation else {}
    out_strategies = outlier.get("strategies_used", {}) if outlier else {}

    script = f'''"""
Auto-generated Preprocessing Script
Generated by Multi-Agent Data Preprocessing System
Dataset: {state.get('dataset_path', 'Unknown')}
Learning Objective: {state.get('learning_objective', 'Unknown')}
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

# Load dataset
df = pd.read_csv("{state.get('dataset_path', 'your_dataset.csv')}")
print(f"Loaded: {{df.shape[0]}} rows, {{df.shape[1]}} columns")

# -- 1. IMPUTATION --
{generate_imputation_code(imp_actions)}

# -- 2. ENCODING --
{generate_encoding_code(enc_strategies)}

# -- 3. OUTLIER HANDLING --
{generate_outlier_code(out_strategies, outlier)}

# -- 4. FEATURE TRANSFORMATION --
{generate_transformation_code(trans_strategies)}

print(f"Final shape: {{df.shape}}")
print("Preprocessing complete!")

# Save output
df.to_csv("preprocessed_output.csv", index=False, encoding="utf-8")
'''
    return script


def generate_imputation_code(actions: dict) -> str:
    lines = []
    for col, action in actions.items():
        if "median" in action.lower():
            val = action.split("(")[1].rstrip(")")
            lines.append(f'df["{col}"] = df["{col}"].fillna({val})')
        elif "mean" in action.lower():
            val = action.split("(")[1].rstrip(")")
            lines.append(f'df["{col}"] = df["{col}"].fillna({val})')
        elif "mode" in action.lower():
            val = action.split("(")[1].rstrip(")")
            lines.append(f'df["{col}"] = df["{col}"].fillna("{val}")')
        elif "dropped" in action.lower() and "column" in action.lower():
            lines.append(f'df = df.drop(columns=["{col}"])')
        elif "dropped" in action.lower() and "rows" in action.lower():
            lines.append(f'df = df.dropna(subset=["{col}"])')
    return "\n".join(lines) if lines else "# No imputation needed"


def generate_encoding_code(strategies: dict) -> str:
    lines = []
    onehot_cols = []
    for col, strategy in strategies.items():
        if strategy == "label":
            lines.append(f'df["{col}"] = df["{col}"].astype("category").cat.codes')
        elif strategy == "onehot":
            onehot_cols.append(col)
        elif strategy == "drop":
            lines.append(f'df = df.drop(columns=["{col}"])')
        elif strategy == "frequency":
            lines.append(f'freq_map = df["{col}"].value_counts(normalize=True).to_dict()')
            lines.append(f'df["{col}"] = df["{col}"].map(freq_map)')
    if onehot_cols:
        cols_str = str(onehot_cols)
        lines.append(f'df = pd.get_dummies(df, columns={cols_str}, dtype=int)')
    return "\n".join(lines) if lines else "# No encoding needed"


def generate_outlier_code(strategies: dict, outlier_report: dict) -> str:
    lines = []
    outlier_info = outlier_report.get("outlier_info", {}) if outlier_report else {}
    for col, strategy in strategies.items():
        if strategy == "winsorize" and col in outlier_info:
            lower = outlier_info[col]["lower_bound"]
            upper = outlier_info[col]["upper_bound"]
            lines.append(f'df["{col}"] = df["{col}"].clip(lower={lower}, upper={upper})')
        elif strategy == "log_transform":
            lines.append(f'df["{col}"] = np.log(df["{col}"] + 1)')
    return "\n".join(lines) if lines else "# No outlier handling needed"


def generate_transformation_code(strategies: dict) -> str:
    lines = []
    standard_cols = [c for c, s in strategies.items() if s == "standard_scaler"]
    minmax_cols = [c for c, s in strategies.items() if s == "minmax_scaler"]
    robust_cols = [c for c, s in strategies.items() if s == "robust_scaler"]

    if standard_cols:
        lines.append(f'scaler = StandardScaler()')
        lines.append(f'df[{standard_cols}] = scaler.fit_transform(df[{standard_cols}])')
    if minmax_cols:
        lines.append(f'scaler = MinMaxScaler()')
        lines.append(f'df[{minmax_cols}] = scaler.fit_transform(df[{minmax_cols}])')
    if robust_cols:
        lines.append(f'scaler = RobustScaler()')
        lines.append(f'df[{robust_cols}] = scaler.fit_transform(df[{robust_cols}])')

    log_cols = [c for c, s in strategies.items() if s == "log_transform"]
    for col in log_cols:
        lines.append(f'df["{col}"] = np.log(df["{col}"] + 1)')

    return "\n".join(lines) if lines else "# No transformation needed"


def report_generator_node(state: AgentState) -> AgentState:
    print("Generating report...")

    os.makedirs("outputs", exist_ok=True)

    # Generate executive summary
    print("  Writing executive summary...")
    summary = build_executive_summary(state)

    # Build full markdown report
    report_md = format_report_markdown(state, summary)
    state["final_report"] = report_md

    # Save report
    report_path = "outputs/preprocessing_report.md"
    with open(report_path, "w", encoding="utf-8", errors="replace") as f:
        f.write(report_md)
    print(f"  Report saved to {report_path}")

    # Generate and save preprocessing script
    print("  Generating reproducible preprocessing script...")
    script = generate_preprocessing_script(state)
    state["preprocessing_script"] = script

    script_path = "outputs/preprocessing_script.py"
    with open(script_path, "w", encoding="utf-8", errors="replace") as f:
        f.write(script)
    print(f"  Script saved to {script_path}")

    # Save cleaned dataset
    df_final = state.get("processed_dataframe")
    if df_final is not None:
        dataset_path = "outputs/preprocessed_dataset.csv"
        df_final.to_csv(dataset_path, index=False, encoding="utf-8")
        state["output_dataset_path"] = dataset_path
        print(f"  Cleaned dataset saved to {dataset_path}")

    return state