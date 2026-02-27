from core.graph import build_graph
import json

graph = build_graph()

initial_state = {
    "dataset_path": "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv",
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

print("\n--- DIMENSIONALITY REPORT ---")
report = result.get("dimensionality_report")

if report is None:
    print("\nStatus: SKIPPED by orchestrator (not enough features to warrant reduction)")
    print("This is correct behavior — Titanic only has 11 features")
    print(f"\nFinal Columns: {result['processed_dataframe'].columns.tolist()}")
    print(f"Final Shape: {result['processed_dataframe'].shape}")
else:
    print(f"\nStatus: {report['status']}")
    print(f"\nStrategy: {report.get('strategy', 'N/A')}")
    print(f"\nReason: {report.get('strategy_reason', report.get('reason', 'N/A'))}")
    print(f"\nActions Taken: {json.dumps(report['actions_taken'], indent=2)}")
    print(f"\nShape Before: {report.get('shape_before', 'N/A')}")
    print(f"Shape After: {report.get('shape_after', 'N/A')}")
    print(f"\nFinal Columns: {result['processed_dataframe'].columns.tolist()}")

print(f"\nErrors: {result['errors']}")