from pathlib import Path
from typing import Dict

import pandas as pd

from analysis import summarize_for_report


def generate_text_report(df: pd.DataFrame) -> str:
    summary: Dict = summarize_for_report(df)
    lines = []
    lines.append("DebugIQ Regression Debug Report")
    lines.append("=" * 32)
    lines.append("")
    lines.append(f"Total failures: {summary['total_failures']}")
    lines.append(f"Unique failures: {summary['unique_failures']}")
    lines.append(f"Regression health score: {summary['regression_health_score']}")
    lines.append("")

    if summary["most_frequent_bug"]:
        mf = summary["most_frequent_bug"]
        lines.append("Most frequent bug:")
        lines.append(f"  Signature: {mf['failure_signature']}")
        lines.append(f"  Count: {mf['count']}")
        lines.append(f"  Example: {mf['example_message']}")
        lines.append("")

    if summary["highest_priority_bug"]:
        hp = summary["highest_priority_bug"]
        lines.append("Highest priority bug:")
        lines.append(f"  Severity: {hp.get('severity')}")
        lines.append(f"  Module: {hp.get('module')}")
        lines.append(f"  Category: {hp.get('category')}")
        lines.append(f"  Message: {hp.get('message')}")
        lines.append(f"  Priority score: {round(hp.get('priority_score', 0.0), 2)}")
        lines.append("")

    lines.append("Problematic modules:")
    for mod in summary["problematic_modules"]:
        lines.append(f"  {mod['module']}: {mod['failures']} failures")

    return "\n".join(lines)


def generate_markdown_report(df: pd.DataFrame) -> str:
    summary: Dict = summarize_for_report(df)
    lines = []
    lines.append("# DebugIQ Regression Debug Report")
    lines.append("")
    lines.append(f"- **Total failures**: {summary['total_failures']}")
    lines.append(f"- **Unique failures**: {summary['unique_failures']}")
    lines.append(f"- **Regression health score**: {summary['regression_health_score']}")
    lines.append("")

    if summary["most_frequent_bug"]:
        mf = summary["most_frequent_bug"]
        lines.append("## Most Frequent Bug")
        lines.append(f"- **Signature**: `{mf['failure_signature']}`")
        lines.append(f"- **Count**: {mf['count']}")
        lines.append(f"- **Example**: {mf['example_message']}")
        lines.append("")

    if summary["highest_priority_bug"]:
        hp = summary["highest_priority_bug"]
        lines.append("## Highest Priority Bug")
        lines.append(f"- **Severity**: `{hp.get('severity')}`")
        lines.append(f"- **Module**: `{hp.get('module')}`")
        lines.append(f"- **Category**: `{hp.get('category')}`")
        lines.append(f"- **Message**: {hp.get('message')}")
        lines.append(f"- **Priority score**: {round(hp.get('priority_score', 0.0), 2)}")
        lines.append("")

    lines.append("## Problematic Modules")
    for mod in summary["problematic_modules"]:
        lines.append(f"- **{mod['module']}**: {mod['failures']} failures")

    return "\n".join(lines)


def save_report(df: pd.DataFrame, path: Path, markdown: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = generate_markdown_report(df) if markdown else generate_text_report(df)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    # Reports are normally generated from main pipeline
    pass

