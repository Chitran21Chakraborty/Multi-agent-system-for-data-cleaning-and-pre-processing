from core.state import AgentState

def report_generator_node(state: AgentState) -> AgentState:
    print("Generating report...")
    state["final_report"] = "Report placeholder"
    return state