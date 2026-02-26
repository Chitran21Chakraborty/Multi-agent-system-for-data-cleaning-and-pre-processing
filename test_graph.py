from core.graph import build_graph

graph = build_graph()

# Test with dummy state
initial_state = {
    "dataset_path": "test.csv",
    "learning_objective": "binary classification",
    "dataframe": None,
    "processed_dataframe": None,
    "profiling_report": None,
    "imputation_report": None,
    "outlier_report": None,
    "encoding_report": None,
    "transformation_report": None,
    "dimensionality_report": None,
    "sampling_report": None,
    "agents_to_run": None,
    "current_agent": None,
    "final_report": None,
    "output_dataset_path": None,
    "preprocessing_script": None,
    "errors": [],
    "warnings": []
}

result = graph.invoke(initial_state)
print("\n--- GRAPH RUN COMPLETE ---")
print(f"Agents that ran: {result['agents_to_run']}")
print(f"Final report: {result['final_report']}")