from core.state import AgentState

def transformation_node(state: AgentState) -> AgentState:
    print("Transformation agent running...")
    state["current_agent"] = "transformation"
    state["transformation_report"] = {"status": "placeholder"}
    return state