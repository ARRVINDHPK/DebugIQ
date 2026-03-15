import sqlite3
from pathlib import Path
from typing import Iterable

import pandas as pd


DB_PATH = Path("data") / "debugiq.db"


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                module TEXT,
                severity TEXT,
                category TEXT,
                message TEXT,
                cluster_id INTEGER,
                failure_signature TEXT,
                frequency INTEGER,
                priority_score REAL,
                known_bug_flag INTEGER,
                root_cause_suggestion TEXT,
                debug_actions TEXT
            )
            """
        )
        conn.commit()


def write_failures(df: pd.DataFrame, db_path: Path = DB_PATH) -> None:
    if df.empty:
        return
    init_db(db_path)
    cols = [
        "timestamp",
        "module",
        "severity",
        "category",
        "message",
        "cluster_id",
        "failure_signature",
        "frequency",
        "priority_score",
        "known_bug_flag",
        "root_cause_suggestion",
        "debug_actions",
    ]
    records = df[cols].copy()
    with sqlite3.connect(db_path) as conn:
        records.to_sql("failures", conn, if_exists="replace", index=False)


def read_failures(db_path: Path = DB_PATH) -> pd.DataFrame:
    if not db_path.exists():
        return pd.DataFrame()
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query("SELECT * FROM failures", conn)


if __name__ == "__main__":
    init_db()

