from core.graph import build_graph

graph = build_graph()

initial_state = {
    "dataset_path": "uploads/titanic.csv",
    "learning_objective": "binary classification - predict passenger survival",
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

print("\n--- ORCHESTRATOR TEST COMPLETE ---")
print(f"Dataset shape: {result['dataframe'].shape}")
print(f"Agents selected: {result['agents_to_run']}")
print(f"Errors: {result['errors']}")