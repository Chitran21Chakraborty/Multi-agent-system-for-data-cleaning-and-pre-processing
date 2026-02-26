from core.state import AgentState

def sampling_node(state: AgentState) -> AgentState:
    print("Sampling agent running...")
    state["current_agent"] = "sampling"
    state["sampling_report"] = {"status": "placeholder"}
    return state