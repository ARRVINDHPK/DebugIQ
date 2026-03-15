import math
from typing import Dict

import pandas as pd


SEVERITY_SCORES: Dict[str, int] = {
    "INFO": 1,
    "WARNING": 3,
    "ERROR": 7,
    "FATAL": 10,
}

MODULE_CRITICALITY: Dict[str, int] = {
    "CACHE_CTRL": 9,
    "MEMORY_CTRL": 10,
    "ALU": 8,
    "AXI_INTERFACE": 9,
}


def compute_priority_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a debug priority score for each failure row.
    Depends on:
      - severity
      - frequency per signature
      - cluster size
      - module criticality
    """
    df = df.copy()
    if df.empty:
        df["priority_score"] = []
        df["frequency"] = []
        return df

    # frequency by failure signature
    freq_by_sig = df.groupby("failure_signature")["failure_signature"].transform("count")
    df["frequency"] = freq_by_sig

    # cluster sizes
    if "cluster_id" in df.columns:
        cluster_sizes = df.groupby("cluster_id")["cluster_id"].transform("count")
    else:
        cluster_sizes = 1
    df["cluster_size"] = cluster_sizes

    severity_score = df["severity"].map(SEVERITY_SCORES).fillna(1)
    module_crit = df["module"].map(MODULE_CRITICALITY).fillna(5)

    df["severity_score"] = severity_score
    df["module_criticality"] = module_crit

    def calc_row(row):
        freq = row["frequency"]
        cl_size = row["cluster_size"]
        sev = row["severity_score"]
        mod_c = row["module_criticality"]
        return (
            0.4 * sev
            + 0.3 * math.log(freq + 1)
            + 0.2 * cl_size
            + 0.1 * mod_c
        )

    df["priority_score"] = df.apply(calc_row, axis=1)
    df = df.sort_values("priority_score", ascending=False)
    return df


if __name__ == "__main__":
    sample = pd.DataFrame(
        {
            "severity": ["ERROR", "FATAL", "WARNING"],
            "module": ["CACHE_CTRL", "MEMORY_CTRL", "ALU"],
            "failure_signature": ["a", "a", "b"],
            "cluster_id": [0, 0, 1],
        }
    )
    out = compute_priority_scores(sample)
    print(out[["severity", "module", "priority_score"]])

