import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import re


LOG_LINE_REGEX = re.compile(
    r"\[TIME:(?P<timestamp>[^\]]+)\]\s+\[(?P<severity>[A-Z]+)\]\s+\[(?P<module>[A-Z0-9_]+)\]\s+(?P<message>.+)"
)


DEFAULT_MODULES = ["CACHE_CTRL", "MEMORY_CTRL", "ALU", "AXI_INTERFACE"]
SEVERITIES = ["INFO", "WARNING", "ERROR", "FATAL"]


def generate_synthetic_logs(log_dir: Path, num_files: int = 5, lines_per_file: int = 300) -> None:
    """
    Generate synthetic simulation logs for demo purposes.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    base_time = datetime.now()

    patterns: List[Tuple[str, List[str]]] = [
        ("assertion failure", ["assert", "assertion", "property"]),
        ("timeout error", ["timeout", "no response", "stalled"]),
        ("protocol violation", ["protocol", "handshake", "invalid state", "axi violation"]),
        ("data mismatch", ["data mismatch", "mismatch detected", "compare fail"]),
        ("memory error", ["parity error", "ecc error", "invalid address"]),
    ]

    for idx in range(num_files):
        file_path = log_dir / f"sim_{idx+1}.log"
        with file_path.open("w") as f:
            current_time = base_time
            for _ in range(lines_per_file):
                current_time += timedelta(nanoseconds=100)
                ts_str = f"{int((current_time - base_time).total_seconds() * 1e9)}ns"
                severity = random.choices(
                    SEVERITIES, weights=[0.6, 0.15, 0.2, 0.05], k=1
                )[0]
                module = random.choice(DEFAULT_MODULES)

                base_pattern, variants = random.choice(patterns)
                msg_variant = random.choice(variants)

                if base_pattern == "assertion failure":
                    msg = f"Assertion failed in {module}: {msg_variant}"
                elif base_pattern == "timeout error":
                    msg = f"{module} {msg_variant} waiting for response"
                elif base_pattern == "protocol violation":
                    msg = f"{module} protocol violation: {msg_variant}"
                elif base_pattern == "data mismatch":
                    msg = f"Data mismatch detected on {module}: {msg_variant}"
                elif base_pattern == "memory error":
                    msg = f"Memory error in {module}: {msg_variant}"
                else:
                    msg = f"Unknown issue in {module}"

                line = f"[TIME:{ts_str}] [{severity}] [{module}] {msg}\n"
                f.write(line)


def load_logs(log_dir: Path) -> List[str]:
    """
    Load all .log files from the directory. If none exist, generate synthetic logs first.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_files = sorted(log_dir.glob("*.log"))

    if not log_files:
        generate_synthetic_logs(log_dir)
        log_files = sorted(log_dir.glob("*.log"))

    all_lines: List[str] = []
    for fp in log_files:
        with fp.open("r") as f:
            all_lines.extend(f.readlines())
    return all_lines


def parse_logs_to_df(log_lines: List[str]) -> pd.DataFrame:
    """
    Parse raw log lines into a structured DataFrame.
    """
    records = []
    for line in log_lines:
        m = LOG_LINE_REGEX.search(line.strip())
        if not m:
            continue
        records.append(
            {
                "raw_line": line.strip(),
                "timestamp": m.group("timestamp"),
                "severity": m.group("severity"),
                "module": m.group("module"),
                "message": m.group("message"),
            }
        )

    df = pd.DataFrame.from_records(records)
    if not df.empty:
        df["timestamp_parsed"] = pd.to_datetime(
            df["timestamp"].str.replace("ns", "", regex=False).astype(float),
            unit="ns",
            origin="unix",
            errors="coerce",
        )
    else:
        df["timestamp_parsed"] = pd.NaT
    return df


def ingest_and_parse(log_dir: str = "logs") -> pd.DataFrame:
    """
    High-level entry point: load logs, parse, and return structured DataFrame.
    """
    log_dir_path = Path(log_dir)
    lines = load_logs(log_dir_path)
    df = parse_logs_to_df(lines)
    return df


if __name__ == "__main__":
    df_logs = ingest_and_parse("logs")
    print(df_logs.head())

