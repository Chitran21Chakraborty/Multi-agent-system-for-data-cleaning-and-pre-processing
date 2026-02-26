from typing import TypedDict, Optional, Any
import pandas as pd

class AgentState(TypedDict):
    # --- Input ---
    dataset_path: str                      # path to uploaded CSV
    learning_objective: str                # e.g. "binary classification"
    
    # --- Data ---
    dataframe: Optional[Any]               # the actual pandas DataFrame
    processed_dataframe: Optional[Any]     # DataFrame after all transformations
    
    # --- Agent Outputs ---
    profiling_report: Optional[dict]       # output from profiling agent
    imputation_report: Optional[dict]      # output from imputation agent
    outlier_report: Optional[dict]         # output from outlier agent
    encoding_report: Optional[dict]        # output from encoding agent
    transformation_report: Optional[dict]  # output from transformation agent
    dimensionality_report: Optional[dict]  # output from dimensionality agent
    sampling_report: Optional[dict]        # output from sampling agent
    
    # --- Orchestrator Decisions ---
    agents_to_run: Optional[list]          # orchestrator decides which agents to run
    current_agent: Optional[str]           # which agent is currently running
    
    # --- Final Output ---
    final_report: Optional[str]            # human readable markdown report
    output_dataset_path: Optional[str]     # path to cleaned dataset
    preprocessing_script: Optional[str]    # auto generated Python script
    
    # --- Error Handling ---
    errors: Optional[list]                 # any errors encountered
    warnings: Optional[list]              # any warnings to report