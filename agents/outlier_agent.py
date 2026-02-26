from core.state import AgentState

def outlier_node(state: AgentState) -> AgentState:
    print("Outlier agent running...")
    state["current_agent"] = "outlier"
    state["outlier_report"] = {"status": "placeholder"}
    return state