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

print("\n--- SAMPLING REPORT ---")
report = result.get("sampling_report")

if report is None:
    print("Status: SKIPPED by orchestrator")
else:
    print(f"\nStatus: {report['status']}")
    print(f"\nTarget Column: {report.get('target_column', 'N/A')}")
    print(f"\nStrategy: {report.get('strategy', 'N/A')}")
    print(f"\nReason: {report.get('strategy_reason', 'N/A')}")
    print(f"\nClass Balance Before:")
    print(json.dumps(report.get('balance_before', {}), indent=2))
    print(f"\nAction Taken: {report.get('action_taken', 'N/A')}")
    print(f"\nShape Before: {report.get('shape_before', 'N/A')}")
    print(f"Shape After: {report.get('shape_after', 'N/A')}")

print(f"\nFinal Dataset Shape: {result['processed_dataframe'].shape}")
print(f"Final Columns: {result['processed_dataframe'].columns.tolist()}")
print(f"\nErrors: {result['errors']}")