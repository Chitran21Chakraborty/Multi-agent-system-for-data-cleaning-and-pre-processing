from core.state import AgentState

def encoding_node(state: AgentState) -> AgentState:
    print("Encoding agent running...")
    state["current_agent"] = "encoding"
    state["encoding_report"] = {"status": "placeholder"}
    return state