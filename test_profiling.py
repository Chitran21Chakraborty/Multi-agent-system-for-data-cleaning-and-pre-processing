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

print("\n--- PROFILING REPORT ---")
report = result["profiling_report"]

print(f"\nShape: {report['shape']}")
print(f"\nMissing Values: {json.dumps(report['missing_values'], indent=2)}")
print(f"\nDuplicate Rows: {report['duplicate_rows']}")
print(f"\nNumerical Columns: {list(report['numerical_columns'].keys())}")
print(f"\nCategorical Columns: {list(report['categorical_columns'].keys())}")
print(f"\nPotential Targets: {report['potential_target_columns']}")
print(f"\nLLM Insights:\n{report['llm_insights']}")
print(f"\nErrors: {result['errors']}")