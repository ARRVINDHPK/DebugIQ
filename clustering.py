from typing import Optional

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans


class FailureClustering:
    """
    Use sentence-transformers to embed failure messages and cluster them.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", n_clusters: int = 8):
        self.model_name = model_name
        self.n_clusters = n_clusters
        self._embedder: Optional[SentenceTransformer] = None
        self._kmeans: Optional[KMeans] = None

    @property
    def embedder(self) -> SentenceTransformer:
        if self._embedder is None:
            self._embedder = SentenceTransformer(self.model_name)
        return self._embedder

    def fit_predict(self, messages: pd.Series) -> pd.Series:
        texts = messages.fillna("").astype(str).tolist()
        if not texts:
            return pd.Series(dtype=int)

        embeddings = self.embedder.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        n_clusters = min(self.n_clusters, max(2, len(texts) // 5))  # adapt clusters to data size
        self._kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = self._kmeans.fit_predict(embeddings)
        return pd.Series(labels)


def add_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add cluster_id column to DataFrame using semantic clustering.
    """
    df = df.copy()
    if df.empty:
        df["cluster_id"] = []
        return df
    clusterer = FailureClustering()
    df["cluster_id"] = clusterer.fit_predict(df["normalized_message"])
    return df


if __name__ == "__main__":
    sample = pd.DataFrame(
        {
            "normalized_message": [
                "axi interface timeout waiting response",
                "timeout error no response from slave",
                "data mismatch expected value",
                "memory parity error in controller",
                "another memory ecc error occurred",
            ]
        }
    )
    out = add_clusters(sample)
    print(out)

