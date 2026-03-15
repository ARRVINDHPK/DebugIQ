from pathlib import Path

import pandas as pd

from analysis import summarize_for_report
from classifier import categorize_failures
from clustering import add_clusters
from database import write_failures
from parser import ingest_and_parse
from preprocess import preprocess_logs
from ranking import compute_priority_scores
from recommendations import add_recommendations
from report_generator import save_report


KNOWN_BUG_SIGNATURES = {
    # simple example known bug signatures (signatures of normalized messages)
}


def apply_known_bug_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if not KNOWN_BUG_SIGNATURES:
        df["known_bug_flag"] = 0
        return df
    df["known_bug_flag"] = df["failure_signature"].apply(
        lambda sig: 1 if sig in KNOWN_BUG_SIGNATURES else 0
    )
    return df


def run_pipeline(log_dir: str = "logs") -> pd.DataFrame:
    print("Ingesting and parsing logs...")
    df = ingest_and_parse(log_dir)
    if df.empty:
        print("No log entries parsed.")
        return df

    print(f"Parsed {len(df)} log entries.")

    print("Preprocessing logs and generating signatures...")
    df = preprocess_logs(df)

    print("Categorizing failures...")
    df = categorize_failures(df)

    print("Clustering failures semantically...")
    df = add_clusters(df)

    print("Computing priority scores...")
    df = compute_priority_scores(df)

    print("Applying known bug detection...")
    df = apply_known_bug_flags(df)

    print("Adding root cause suggestions and debug recommendations...")
    df = add_recommendations(df)

    print("Writing failures to SQLite database...")
    write_failures(df)

    print("Generating debug reports...")
    save_report(df, Path("data") / "debug_report.txt", markdown=False)
    save_report(df, Path("data") / "debug_report.md", markdown=True)

    summary = summarize_for_report(df)
    print("=== Pipeline complete ===")
    print(f"Total failures: {summary['total_failures']}")
    print(f"Unique failures: {summary['unique_failures']}")
    print(f"Regression health score: {summary['regression_health_score']}")
    return df


if __name__ == "__main__":
    run_pipeline("logs")

