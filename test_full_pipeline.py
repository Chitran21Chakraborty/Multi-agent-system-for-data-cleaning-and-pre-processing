from core.graph import build_graph

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

print("\n" + "="*50)
print("PIPELINE COMPLETE")
print("="*50)
print(f"Original shape: (891, 12)")
print(f"Final shape: {result['processed_dataframe'].shape}")
print(f"Agents run: {result['agents_to_run']}")
print(f"Errors: {result['errors']}")
print(f"\nOutputs saved:")
print(f"  - outputs/preprocessing_report.md")
print(f"  - outputs/preprocessing_script.py")
print(f"  - outputs/preprocessed_dataset.csv")
print("\nFirst 5 rows of cleaned data:")
print(result['processed_dataframe'].head())