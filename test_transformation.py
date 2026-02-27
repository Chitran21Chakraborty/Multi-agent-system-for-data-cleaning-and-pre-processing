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

print("\n--- TRANSFORMATION REPORT ---")
report = result["transformation_report"]
print(f"\nStatus: {report['status']}")
print(f"\nStrategies Used: {json.dumps(report['strategies_used'], indent=2)}")
print(f"\nActions Taken: {json.dumps(report['actions_taken'], indent=2)}")
print(f"\nScalers Used: {report['scalers_used']}")
print(f"\nFinal Shape: {report['shape']}")
print(f"\nSample of transformed data:")
print(result['processed_dataframe'].head())
print(f"\nErrors: {result['errors']}")