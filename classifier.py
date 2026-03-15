from typing import List

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


CATEGORIES = [
    "assertion failure",
    "timeout error",
    "protocol violation",
    "data mismatch",
    "memory error",
    "unknown",
]


def _build_heuristic_training_data() -> pd.DataFrame:
    """
    Build a tiny heuristic training set so the classifier has some notion of categories.
    """
    examples = [
        ("assertion failed property x", "assertion failure"),
        ("assertion error check signal", "assertion failure"),
        ("timeout waiting for response", "timeout error"),
        ("no response from axi slave", "timeout error"),
        ("protocol violation invalid handshake", "protocol violation"),
        ("axi protocol error invalid burst", "protocol violation"),
        ("data mismatch expected value", "data mismatch"),
        ("compare fail mismatch detected", "data mismatch"),
        ("memory parity error ecc", "memory error"),
        ("invalid memory address access", "memory error"),
        ("unexpected failure", "unknown"),
        ("unknown error occurred", "unknown"),
    ]
    return pd.DataFrame(examples, columns=["text", "label"])


class FailureClassifier:
    """
    Simple TF-IDF + Logistic Regression classifier for failure categories.
    Trains a small heuristic model at initialization time.
    """

    def __init__(self) -> None:
        train_df = _build_heuristic_training_data()
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        X = self.vectorizer.fit_transform(train_df["text"])
        self.model = LogisticRegression(max_iter=1000)
        self.model.fit(X, train_df["label"])

    def predict(self, messages: List[str]) -> List[str]:
        if not messages:
            return []
        X = self.vectorizer.transform(messages)
        preds = self.model.predict(X)
        return preds.tolist()

    def add_categories(self, df: pd.DataFrame, message_col: str = "normalized_message") -> pd.DataFrame:
        df = df.copy()
        msgs = df[message_col].fillna("").astype(str).tolist()
        preds = self.predict(msgs)
        df["category"] = preds
        return df


def categorize_failures(df: pd.DataFrame) -> pd.DataFrame:
    clf = FailureClassifier()
    return clf.add_categories(df)


if __name__ == "__main__":
    sample = pd.DataFrame(
        {
            "normalized_message": [
                "assertion failed in axi interface",
                "axi interface timeout waiting response",
                "axi protocol violation invalid state",
                "data mismatch expected",
                "memory parity error",
                "some random unknown message",
            ]
        }
    )
    out = categorize_failures(sample)
    print(out[["normalized_message", "category"]])

