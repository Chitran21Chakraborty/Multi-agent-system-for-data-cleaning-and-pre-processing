from core.state import AgentState

def imputation_node(state: AgentState) -> AgentState:
    print("Imputation agent running...")
    state["current_agent"] = "imputation"
    state["imputation_report"] = {"status": "placeholder"}
    return state