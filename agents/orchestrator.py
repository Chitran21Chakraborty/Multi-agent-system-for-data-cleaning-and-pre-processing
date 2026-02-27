import os
import pandas as pd
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


def load_dataset(state: AgentState) -> AgentState:
    """Load the CSV dataset into a DataFrame."""
    try:
        df = pd.read_csv(state["dataset_path"])
        state["dataframe"] = df
        state["processed_dataframe"] = df.copy()
        print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Dataset loading error: {str(e)}"]
    return state


def analyze_and_route(state: AgentState) -> AgentState:
    """Use LLM to analyze the dataset and decide which agents to run."""
    df = state.get("dataframe")
    if df is None:
        state["errors"] = state.get("errors", []) + ["No dataframe available"]
        state["agents_to_run"] = []
        return state

    summary = build_data_summary(df)
    objective = state["learning_objective"]

    llm = get_llm()

    prompt = f"""
You are an expert data scientist and orchestrator of a data preprocessing pipeline.

You have been given a dataset with the following profile:
{summary}

The machine learning objective is: {objective}

Based on the dataset profile and the learning objective, decide which preprocessing agents should run.
Available agents and what they do:
- profiling: Always run first. Generates detailed statistics about the dataset.
- imputation: Run if there are missing values in the dataset.
- outlier: Run if numerical columns likely contain outliers.
- encoding: Run if there are categorical columns that need encoding.
- transformation: Run if numerical columns are skewed or need scaling.
- dimensionality: Run if there are many features (10+) and reduction may help.
- sampling: Run if the dataset is imbalanced (for classification) or very large.

Rules:
- Always include profiling as the first agent.
- Only include agents that are genuinely needed based on the data profile.
- Return ONLY a Python list of agent names in the order they should run.
- Example: ["profiling", "imputation", "encoding", "transformation"]
- Do not include explanations, only the list.
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    agents_to_run = parse_agents_list(response.content)

    print(f"Orchestrator decided to run: {agents_to_run}")
    state["agents_to_run"] = agents_to_run
    state["current_agent"] = "orchestrator"
    return state


def build_data_summary(df: pd.DataFrame) -> str:
    """Build a concise data summary for the LLM."""
    summary = []
    summary.append(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")

    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]
    if len(missing_cols) > 0:
        summary.append(f"Missing values found in columns: {missing_cols.to_dict()}")
    else:
        summary.append("No missing values found")

    num_cols = df.select_dtypes(include='number').columns.tolist()
    cat_cols = df.select_dtypes(include='object').columns.tolist()
    summary.append(f"Numerical columns ({len(num_cols)}): {num_cols}")
    summary.append(f"Categorical columns ({len(cat_cols)}): {cat_cols}")

    dupes = df.duplicated().sum()
    summary.append(f"Duplicate rows: {dupes}")

    if num_cols:
        skewness = df[num_cols].skew().to_dict()
        summary.append(f"Skewness of numerical columns: {skewness}")

    return "\n".join(summary)


def parse_agents_list(response: str) -> list:
    """Parse LLM response to extract list of agents."""
    valid_agents = ["profiling", "imputation", "outlier", "encoding",
                    "transformation", "dimensionality", "sampling"]
    try:
        start = response.find("[")
        end = response.find("]") + 1
        if start != -1 and end != 0:
            list_str = response[start:end]
            agents = eval(list_str)
            agents = [a.strip().lower() for a in agents if a.strip().lower() in valid_agents]
            if "profiling" not in agents:
                agents.insert(0, "profiling")
            return agents
    except Exception:
        pass
    return valid_agents


def orchestrator_node(state: AgentState) -> AgentState:
    print("Orchestrator running...")

    # EMIT START
    emit("agent_start", {"agent": "orchestrator", "label": "Orchestrator"})

    # Load dataset
    state = load_dataset(state)

    if state.get("errors"):
        emit("agent_done", {
            "agent": "orchestrator",
            "skipped": True,
            "reason": state["errors"][-1]
        })
        return state

    # Analyze and decide agents
    state = analyze_and_route(state)

    df = state.get("dataframe")

    # EMIT DONE
    emit("agent_done", {
        "agent": "orchestrator",
        "summary": {
            "rows": df.shape[0] if df is not None else 0,
            "columns": df.shape[1] if df is not None else 0,
            "agents_selected": len(state.get("agents_to_run", [])),
            "pipeline": " → ".join(state.get("agents_to_run", []))
        },
        "actions": {
            agent: "scheduled" for agent in state.get("agents_to_run", [])
        }
    })

    return state