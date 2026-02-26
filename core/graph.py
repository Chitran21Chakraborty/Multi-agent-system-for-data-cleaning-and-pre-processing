from langgraph.graph import StateGraph, END
from core.state import AgentState

# Import all agents
from agents.orchestrator import orchestrator_node
from agents.profiling_agent import profiling_node
from agents.imputation_agent import imputation_node
from agents.outlier_agent import outlier_node
from agents.encoding_agent import encoding_node
from agents.transformation_agent import transformation_node
from agents.dimensionality_agent import dimensionality_node
from agents.sampling_agent import sampling_node
from reports.generator import report_generator_node

# --- Routing Logic ---
def route_after_orchestrator(state: AgentState):
    """Orchestrator decides which agents to run — this picks the first one."""
    agents = state.get("agents_to_run", [])
    if not agents:
        return "report_generator"
    return agents[0]

def route_after_agent(state: AgentState):
    """After each agent runs, move to the next one in the list."""
    agents = state.get("agents_to_run", [])
    current = state.get("current_agent")
    
    if current in agents:
        current_index = agents.index(current)
        next_index = current_index + 1
        if next_index < len(agents):
            return agents[next_index]
    
    return "report_generator"

# --- Build the Graph ---
def build_graph():
    graph = StateGraph(AgentState)
    
    # Add all nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("profiling", profiling_node)
    graph.add_node("imputation", imputation_node)
    graph.add_node("outlier", outlier_node)
    graph.add_node("encoding", encoding_node)
    graph.add_node("transformation", transformation_node)
    graph.add_node("dimensionality", dimensionality_node)
    graph.add_node("sampling", sampling_node)
    graph.add_node("report_generator", report_generator_node)
    
    # Entry point
    graph.set_entry_point("orchestrator")
    
    # Orchestrator routes to first agent
    graph.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "profiling": "profiling",
            "imputation": "imputation",
            "outlier": "outlier",
            "encoding": "encoding",
            "transformation": "transformation",
            "dimensionality": "dimensionality",
            "sampling": "sampling",
            "report_generator": "report_generator"
        }
    )
    
    # Each agent routes to the next
    for agent in ["profiling", "imputation", "outlier", "encoding", 
                  "transformation", "dimensionality", "sampling"]:
        graph.add_conditional_edges(
            agent,
            route_after_agent,
            {
                "profiling": "profiling",
                "imputation": "imputation",
                "outlier": "outlier",
                "encoding": "encoding",
                "transformation": "transformation",
                "dimensionality": "dimensionality",
                "sampling": "sampling",
                "report_generator": "report_generator"
            }
        )
    
    # Report generator ends the pipeline
    graph.add_edge("report_generator", END)
    
    return graph.compile()