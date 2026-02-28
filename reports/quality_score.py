# reports/quality_score.py

def compute_quality_score(state: dict) -> dict:
    """Compute a 0-100 data quality score before and after preprocessing."""

    profiling     = state.get("profiling_report", {}) or {}
    imputation    = state.get("imputation_report", {}) or {}
    outlier       = state.get("outlier_report", {}) or {}
    encoding      = state.get("encoding_report", {}) or {}
    transformation= state.get("transformation_report", {}) or {}
    sampling      = state.get("sampling_report", {}) or {}
    df_final      = state.get("processed_dataframe")

    shape         = profiling.get("shape", {})
    total_rows    = shape.get("rows", 1)
    total_cols    = shape.get("columns", 1)
    total_cells   = total_rows * total_cols

    scores = {}

    # ── 1. COMPLETENESS (25 pts) ──────────────────────────────────────────
    missing_info = profiling.get("missing_values", {})
    total_missing_before = sum(
        v["count"] for v in missing_info.values()
    ) if missing_info else 0

    missing_pct_before = (total_missing_before / total_cells * 100) if total_cells else 0
    completeness_before = max(0, round(25 - (missing_pct_before / 4), 1))

    remaining_missing = 0
    if df_final is not None:
        remaining_missing = int(df_final.isnull().sum().sum())
    missing_pct_after = (remaining_missing / total_cells * 100) if total_cells else 0
    completeness_after = max(0, round(25 - (missing_pct_after / 4), 1))

    scores["completeness"] = {
        "label": "Completeness",
        "before": completeness_before,
        "after": completeness_after,
        "max": 25,
        "detail": f"{total_missing_before} missing values → {remaining_missing} remaining"
    }

    # ── 2. OUTLIER HEALTH (25 pts) ────────────────────────────────────────
    outlier_info = outlier.get("outlier_info", {}) or {}
    total_outliers_before = sum(
        v.get("iqr_outliers", 0) for v in outlier_info.values()
    ) if outlier_info else 0

    outlier_pct = (total_outliers_before / total_rows * 100) if total_rows else 0
    outlier_before = max(0, round(25 - (outlier_pct / 4), 1))

    outlier_status = outlier.get("status", "skipped")
    if outlier_status == "completed":
        outlier_after = min(25, outlier_before + 8)
    elif outlier_status == "skipped" and total_outliers_before == 0:
        outlier_after = 25
    else:
        outlier_after = outlier_before

    scores["outlier_health"] = {
        "label": "Outlier Health",
        "before": outlier_before,
        "after": round(outlier_after, 1),
        "max": 25,
        "detail": f"{total_outliers_before} outliers detected, "
                  f"{'treated' if outlier_status == 'completed' else 'none found'}"
    }

    # ── 3. FEATURE READINESS (25 pts) ────────────────────────────────────
    cat_cols = profiling.get("categorical_columns", {}) or {}
    num_cols = profiling.get("numerical_columns", {}) or {}

    unencoded_cats  = len(cat_cols)
    unscaled_nums   = len(num_cols)
    total_features  = unencoded_cats + unscaled_nums or 1

    feature_before = max(0, round(25 - (
        (unencoded_cats * 8 + unscaled_nums * 4) / total_features
    ), 1))
    feature_before = max(0, min(25, feature_before))

    enc_done   = encoding.get("status") == "completed"
    trans_done = transformation.get("status") == "completed"
    feature_after = 25 if (enc_done or not cat_cols) and (trans_done or not num_cols) \
                    else (20 if enc_done or trans_done else feature_before)

    scores["feature_readiness"] = {
        "label": "Feature Readiness",
        "before": feature_before,
        "after": feature_after,
        "max": 25,
        "detail": f"{'Encoded + Scaled' if enc_done and trans_done else 'Encoded' if enc_done else 'Scaled' if trans_done else 'Raw features'}"
    }

    # ── 4. BALANCE SCORE (25 pts) ─────────────────────────────────────────
    balance_before_info = sampling.get("balance_before", {}) or {}
    imbalance_ratio     = balance_before_info.get("imbalance_ratio", 1.0) or 1.0
    sampling_status     = sampling.get("status", "skipped")

    if imbalance_ratio <= 1.5:
        balance_before = 25
    elif imbalance_ratio <= 2.0:
        balance_before = 18
    elif imbalance_ratio <= 3.0:
        balance_before = 12
    else:
        balance_before = 6

    if sampling_status == "completed":
        balance_after = min(25, balance_before + 10)
    elif sampling_status == "skipped" and balance_before == 25:
        balance_after = 25  # was already balanced
    else:
        balance_after = balance_before

    scores["balance"] = {
        "label": "Class Balance",
        "before": balance_before,
        "after": balance_after,
        "max": 25,
        "detail": f"Imbalance ratio: {imbalance_ratio}" if imbalance_ratio > 1 else "Balanced dataset"
    }

    # ── TOTALS ────────────────────────────────────────────────────────────
    total_before = sum(s["before"] for s in scores.values())
    total_after  = sum(s["after"]  for s in scores.values())

    def grade(score):
        if score >= 90: return {"label": "Excellent", "color": "#22c55e"}
        if score >= 75: return {"label": "Good",      "color": "#3b82f6"}
        if score >= 60: return {"label": "Fair",       "color": "#f59e0b"}
        return               {"label": "Poor",         "color": "#ef4444"}

    return {
        "total_before": round(total_before, 1),
        "total_after":  round(total_after,  1),
        "improvement":  round(total_after - total_before, 1),
        "grade_before": grade(total_before),
        "grade_after":  grade(total_after),
        "dimensions":   scores
    }