import math
from typing import Dict, Tuple

import pandas as pd


def compute_failure_frequency(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("failure_signature")
        .agg(
            count=("failure_signature", "size"),
            example_message=("message", "first"),
            severity=("severity", "first"),
        )
        .reset_index()
        .sort_values("count", ascending=False)
    )


def compute_module_hotspots(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("module")
        .agg(
            failures=("failure_signature", "size"),
        )
        .reset_index()
        .sort_values("failures", ascending=False)
    )


def compute_regression_health(df: pd.DataFrame) -> Tuple[float, Dict[str, int]]:
    """
    Compute a regression health score between 0 and 100 based on:
      - number of failures
      - severity distribution
      - cluster diversity
    """
    if df.empty:
        return 100.0, {}

    total = len(df)
    severity_counts = df["severity"].value_counts().to_dict()
    cluster_diversity = df["cluster_id"].nunique() if "cluster_id" in df.columns else 1

    # crude weighted penalty
    sev_weights = {"INFO": 0.5, "WARNING": 1.0, "ERROR": 2.0, "FATAL": 3.0}
    weighted = 0.0
    for sev, count in severity_counts.items():
        w = sev_weights.get(sev, 1.0)
        weighted += w * count

    diversity_penalty = math.log(cluster_diversity + 1)
    total_penalty = weighted * 0.7 + diversity_penalty * 5.0

    health = max(0.0, 100.0 - total_penalty)
    return float(round(health, 2)), {k: int(v) for k, v in severity_counts.items()}


def summarize_for_report(df: pd.DataFrame) -> Dict:
    """
    Compute basic summary statistics for report generation.
    """
    total_failures = len(df)
    unique_failures = df["failure_signature"].nunique() if not df.empty else 0
    freq_df = compute_failure_frequency(df)
    most_frequent_bug = (
        freq_df.iloc[0].to_dict() if not freq_df.empty else None
    )
    highest_priority_bug = (
        df.sort_values("priority_score", ascending=False).iloc[0].to_dict()
        if not df.empty
        else None
    )
    module_hotspots = compute_module_hotspots(df)
    health_score, severity_dist = compute_regression_health(df)

    return {
        "total_failures": int(total_failures),
        "unique_failures": int(unique_failures),
        "most_frequent_bug": most_frequent_bug,
        "highest_priority_bug": highest_priority_bug,
        "problematic_modules": module_hotspots.to_dict(orient="records"),
        "regression_health_score": health_score,
        "severity_distribution": severity_dist,
    }


if __name__ == "__main__":
    # module-level smoke test would go here
    pass

