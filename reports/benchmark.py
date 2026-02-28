"""
Benchmark module — trains XGBoost before and after preprocessing,
compares model performance to prove preprocessing improved ML-readiness.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import make_scorer, f1_score
import warnings
warnings.filterwarnings("ignore")


# ── TARGET DETECTION ──────────────────────────────────────────────────────────
def auto_detect_target(df: pd.DataFrame, learning_objective: str) -> str | None:
    """
    Auto-detect the most likely target column based on heuristics.
    Priority: common names → lowest cardinality numerical → binary columns
    """
    cols = df.columns.tolist()
    obj  = learning_objective.lower()

    # Common target column names (priority order)
    common_targets = [
        "target", "label", "class", "output", "y",
        "survived", "price", "salary", "income", "revenue",
        "churn", "fraud", "default", "result", "outcome",
        "diagnosis", "disease", "risk", "score", "grade",
        "sales", "demand", "value", "amount", "cost"
    ]

    # Check exact matches first (case-insensitive)
    for name in common_targets:
        for col in cols:
            if col.lower() == name:
                return col

    # Check partial matches
    for name in common_targets:
        for col in cols:
            if name in col.lower():
                return col

    # For classification: find binary column or lowest cardinality
    if "classif" in obj:
        binary_cols = [c for c in cols if df[c].nunique() == 2]
        if binary_cols:
            return binary_cols[-1]  # last binary column usually target

        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if cat_cols:
            # Lowest cardinality categorical
            return min(cat_cols, key=lambda c: df[c].nunique())

    # For regression: find numerical with most variance
    if "regress" in obj:
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if num_cols:
            # Highest variance numerical column (likely the target)
            return max(num_cols, key=lambda c: df[c].std())

    # Fallback: last column
    return cols[-1] if cols else None


# ── DATA PREP ─────────────────────────────────────────────────────────────────
def prepare_xy(df: pd.DataFrame, target_col: str):
    """Prepare X and y, handling missing values and encoding for XGBoost."""
    df = df.copy()

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found")

    y = df[target_col].copy()
    X = df.drop(columns=[target_col])

    # Drop non-numeric columns that can't be easily encoded
    # (XGBoost needs numbers)
    for col in X.columns.tolist():
        if X[col].dtype == "object":
            try:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str).fillna("missing"))
            except Exception:
                X.drop(columns=[col], inplace=True)

    # Fill remaining NaN in X
    X = X.fillna(X.median(numeric_only=True))
    X = X.fillna(0)

    # Encode target if needed
    if y.dtype == "object" or str(y.dtype) == "category":
        le = LabelEncoder()
        y = pd.Series(le.fit_transform(y.astype(str).fillna("missing")), name=target_col)
    else:
        y = y.fillna(y.median())

    return X, y


# ── MODEL SELECTION ───────────────────────────────────────────────────────────
def get_model_and_metrics(learning_objective: str, y: pd.Series):
    """Return the right model and scoring metrics for the objective."""
    try:
        from xgboost import XGBClassifier, XGBRegressor
        xgb_available = True
    except ImportError:
        xgb_available = False

    obj        = learning_objective.lower()
    n_classes  = y.nunique()
    is_binary  = n_classes == 2

    if "regress" in obj:
        if xgb_available:
            from xgboost import XGBRegressor
            model = XGBRegressor(n_estimators=100, max_depth=4,
                                 learning_rate=0.1, random_state=42,
                                 verbosity=0, eval_metric="rmse")
        else:
            from sklearn.ensemble import RandomForestRegressor
            model = RandomForestRegressor(n_estimators=100, random_state=42)

        metrics = {
            "primary": ("R² Score", "r2"),
            "secondary": ("RMSE", "neg_root_mean_squared_error")
        }
        cv = KFold(n_splits=5, shuffle=True, random_state=42)

    elif "cluster" in obj:
        # Treat as classification on auto-detected target
        if xgb_available:
            from xgboost import XGBClassifier
            model = XGBClassifier(n_estimators=100, max_depth=4,
                                  learning_rate=0.1, random_state=42,
                                  verbosity=0, use_label_encoder=False,
                                  eval_metric="logloss")
        else:
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(n_estimators=100, random_state=42)

        avg = "binary" if is_binary else "macro"
        metrics = {
            "primary": ("F1 Score", f"f1_{avg}"),
            "secondary": ("Accuracy", "accuracy")
        }
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    else:
        # Classification (binary or multiclass)
        if xgb_available:
            from xgboost import XGBClassifier
            extra = {} if is_binary else {"num_class": n_classes}
            model = XGBClassifier(n_estimators=100, max_depth=4,
                                  learning_rate=0.1, random_state=42,
                                  verbosity=0, use_label_encoder=False,
                                  eval_metric="logloss", **extra)
        else:
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(n_estimators=100, random_state=42)

        avg = "binary" if is_binary else "macro"
        metrics = {
            "primary": ("F1 Score", f"f1_{avg}"),
            "secondary": ("Accuracy", "accuracy")
        }
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    return model, metrics, cv


# ── CORE BENCHMARK ────────────────────────────────────────────────────────────
def score_dataset(df: pd.DataFrame, target_col: str,
                  learning_objective: str) -> dict:
    """Run 5-fold CV and return scores."""
    X, y = prepare_xy(df, target_col)

    # Limit to 10k rows for speed
    if len(X) > 10_000:
        idx = np.random.choice(len(X), 10_000, replace=False)
        X   = X.iloc[idx].reset_index(drop=True)
        y   = y.iloc[idx].reset_index(drop=True)

    model, metrics, cv = get_model_and_metrics(learning_objective, y)

    primary_name,   primary_scorer   = metrics["primary"]
    secondary_name, secondary_scorer = metrics["secondary"]

    try:
        primary_scores = cross_val_score(
            model, X, y, cv=cv, scoring=primary_scorer, n_jobs=-1
        )
        secondary_scores = cross_val_score(
            model, X, y, cv=cv, scoring=secondary_scorer, n_jobs=-1
        )

        # Handle negative scorers (RMSE)
        primary_mean   = float(np.mean(primary_scores))
        secondary_mean = float(np.mean(np.abs(secondary_scores)))

        return {
            "primary_name":    primary_name,
            "primary_score":   round(primary_mean, 4),
            "primary_std":     round(float(np.std(primary_scores)), 4),
            "secondary_name":  secondary_name,
            "secondary_score": round(secondary_mean, 4),
            "n_features":      X.shape[1],
            "n_samples":       X.shape[0],
            "success":         True,
            "error":           None
        }
    except Exception as e:
        return {
            "primary_name":    metrics["primary"][0],
            "primary_score":   None,
            "secondary_score": None,
            "success":         False,
            "error":           str(e)
        }


# ── MAIN ENTRY POINT ──────────────────────────────────────────────────────────
def run_benchmark(original_path: str, preprocessed_path: str,
                  learning_objective: str,
                  profiling_report: dict = None) -> dict:
    """
    Full benchmark: train on original vs preprocessed, compare results.

    Returns a dict with before/after scores and improvement stats.
    """
    try:
        df_original     = pd.read_csv(original_path)
        df_preprocessed = pd.read_csv(preprocessed_path)
    except Exception as e:
        return {"success": False, "error": f"Could not load datasets: {e}"}

    # Auto-detect target column from original dataset
    target_col = auto_detect_target(df_original, learning_objective)

    if target_col is None:
        return {"success": False, "error": "Could not detect target column"}

    # If target was dropped during preprocessing, use original's target
    # but align the preprocessed X to not include it
    target_in_preprocessed = target_col in df_preprocessed.columns

    # Score BEFORE preprocessing
    before = score_dataset(df_original, target_col, learning_objective)

    # Score AFTER preprocessing
    if target_in_preprocessed:
        after = score_dataset(df_preprocessed, target_col, learning_objective)
    else:
        # Target was encoded/renamed — try to find it
        possible = [c for c in df_preprocessed.columns
                    if target_col.lower() in c.lower()]
        if possible:
            after = score_dataset(df_preprocessed, possible[0], learning_objective)
        else:
            # Re-attach target from original
            df_temp = df_preprocessed.copy()
            # Align index
            min_len = min(len(df_temp), len(df_original))
            df_temp[target_col] = df_original[target_col].iloc[:min_len].values
            after = score_dataset(df_temp, target_col, learning_objective)

    if not before["success"] or not after["success"]:
        return {
            "success": False,
            "error": before.get("error") or after.get("error"),
            "target_column": target_col
        }

    # Compute improvement
    primary_before = before["primary_score"]
    primary_after  = after["primary_score"]

    # For RMSE lower is better, for everything else higher is better
    is_rmse = "RMSE" in before["primary_name"]
    if is_rmse:
        improvement    = round(primary_before - primary_after, 4)
        improved       = improvement > 0
        pct_change     = round((improvement / abs(primary_before)) * 100, 1) if primary_before else 0
    else:
        improvement    = round(primary_after - primary_before, 4)
        improved       = improvement > 0
        pct_change     = round((improvement / abs(primary_before)) * 100, 1) if primary_before else 0

    # Determine model used
    try:
        import xgboost
        model_name = "XGBoost"
    except ImportError:
        model_name = "Random Forest"

    return {
        "success":          True,
        "target_column":    target_col,
        "learning_objective": learning_objective,
        "model_used":       model_name,
        "cv_folds":         5,
        "before": {
            "primary_name":    before["primary_name"],
            "primary_score":   primary_before,
            "primary_std":     before["primary_std"],
            "secondary_name":  before["secondary_name"],
            "secondary_score": before["secondary_score"],
            "n_features":      before["n_features"],
            "n_samples":       before["n_samples"]
        },
        "after": {
            "primary_name":    after["primary_name"],
            "primary_score":   primary_after,
            "primary_std":     after["primary_std"],
            "secondary_name":  after["secondary_name"],
            "secondary_score": after["secondary_score"],
            "n_features":      after["n_features"],
            "n_samples":       after["n_samples"]
        },
        "improvement":      improvement,
        "pct_change":       pct_change,
        "improved":         improved,
        "is_rmse":          is_rmse
    }