# agents/utils.py
import pandas as pd
import numpy as np

def sample_distribution(series: pd.Series, bins: int = 12) -> dict:
    """Sample a column into histogram bins for frontend charting."""
    try:
        s = series.dropna()
        if len(s) == 0:
            return {"labels": [], "values": []}

        # For numerical: bin into histogram
        if pd.api.types.is_numeric_dtype(s):
            counts, edges = np.histogram(s, bins=bins)
            labels = [f"{round(float(e), 2)}" for e in edges[:-1]]
            values = [int(c) for c in counts]

        # For categorical: top N value counts
        else:
            vc = s.value_counts().head(bins)
            labels = [str(k) for k in vc.index]
            values = [int(v) for v in vc.values]

        # Normalize to 0-1
        mx = max(values) if values else 1
        normalized = [round(v / mx, 4) for v in values]
        return {"labels": labels, "values": normalized}

    except Exception:
        return {"labels": [], "values": []}


def capture_distributions(df: pd.DataFrame, cols: list, bins: int = 12) -> dict:
    """Capture distributions for a list of columns."""
    result = {}
    for col in cols:
        if col in df.columns:
            result[col] = sample_distribution(df[col], bins)
    return result