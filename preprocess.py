import re
from typing import Iterable

import pandas as pd


NOISE_WORDS = {
    "the",
    "and",
    "in",
    "on",
    "for",
    "to",
    "of",
    "a",
    "an",
    "at",
    "is",
    "are",
    "was",
    "were",
    "detected",
    "error",
    "warning",
    "info",
    "fatal",
    "module",
    "ctrl",
}


def clean_message(text: str) -> str:
    """
    Basic normalization for log messages:
    - lowercase
    - remove numbers
    - remove brackets and punctuation-like noise
    - remove short/common noise words
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    # remove numbers
    text = re.sub(r"\d+", " ", text)
    # remove non-alphanumeric characters except underscores and spaces
    text = re.sub(r"[^a-zA-Z_ ]+", " ", text)
    tokens = [t for t in text.split() if t not in NOISE_WORDS and len(t) > 2]
    return " ".join(tokens)


def add_normalized_message(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a normalized_message column to the DataFrame.
    """
    df = df.copy()
    df["normalized_message"] = df["message"].astype(str).apply(clean_message)
    return df


def add_failure_signature(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a simple deterministic signature for each failure based on normalized message.
    """
    df = df.copy()
    df["failure_signature"] = df["normalized_message"].apply(
        lambda x: f"sig_{abs(hash(x)) % (10**12)}" if x else "sig_unknown"
    )
    return df


def preprocess_logs(df: pd.DataFrame) -> pd.DataFrame:
    """
    High-level preprocessing pipeline.
    """
    df = add_normalized_message(df)
    df = add_failure_signature(df)
    return df


if __name__ == "__main__":
    # simple smoke test when run standalone
    sample = pd.DataFrame(
        {
            "message": [
                "Data mismatch detected on CACHE_CTRL: value 0xdead != 0xbeef",
                "AXI_INTERFACE protocol violation: handshake not asserted",
            ]
        }
    )
    out = preprocess_logs(sample)
    print(out)

