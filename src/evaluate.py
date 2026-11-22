import time

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score
from sklearn.metrics import silhouette_score

from src.baseline import score_rfm
from src.cluster import fit_kmeans


def evaluate_candidates(scaled_features: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k in range(2, min(10, len(scaled_features) - 1) + 1):
        model, labels = fit_kmeans(scaled_features, k)
        rows.append({
            "k": k,
            "inertia": float(model.inertia_),
            "silhouette": float(silhouette_score(scaled_features, labels)),
            "davies_bouldin": float(davies_bouldin_score(scaled_features, labels)),
        })
    if not rows:
        raise ValueError("At least 3 customers are required for cluster evaluation")
    return pd.DataFrame(rows)


def compare_methods(rfm: pd.DataFrame, scaled_features: pd.DataFrame, k: int) -> pd.DataFrame:
    baseline = score_rfm(rfm)["baseline_segment"].to_numpy()
    kmeans_model, kmeans_labels = fit_kmeans(scaled_features, k)
    rows = []
    for name, labels, method in (
        ("Baseline quintile RFM", baseline, "baseline"),
        (f"K-Means k={k}", kmeans_labels, "kmeans"),
    ):
        repeats = []
        for seed in range(5):
            start = time.perf_counter()
            if method == "baseline":
                score_rfm(rfm)
            else:
                fit_kmeans(scaled_features, k, random_state=seed)
            repeats.append(time.perf_counter() - start)
        n_clusters = pd.Series(labels).nunique()
        rows.append({
            "method": name,
            "clusters": int(n_clusters),
            "silhouette": float(silhouette_score(scaled_features, labels)),
            "davies_bouldin": float(davies_bouldin_score(scaled_features, labels)),
            "stability_ari": (
                1.0 if method == "baseline" else _kmeans_stability(scaled_features, k)
            ),
            "mean_runtime_seconds_5_runs": float(np.mean(repeats)),
            "interpretability": (
                "Rule-based quintile segments; direct to explain"
                if method == "baseline"
                else "Data-driven clusters; profile and label using observed RFM"
            ),
        })
    return pd.DataFrame(rows)


def _kmeans_stability(features: pd.DataFrame, k: int, runs: int = 5) -> float:
    labels = [fit_kmeans(features, k, random_state=seed)[1] for seed in range(runs)]
    return float(np.mean([
        adjusted_rand_score(labels[0], current) for current in labels[1:]
    ]))
