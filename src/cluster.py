import pandas as pd
from sklearn.cluster import KMeans


def fit_kmeans(features: pd.DataFrame, n_clusters: int, random_state: int = 42):
    if n_clusters < 2 or n_clusters >= len(features):
        raise ValueError("n_clusters must be between 2 and n_samples - 1")
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = model.fit_predict(features)
    return model, labels


def name_clusters(rfm: pd.DataFrame, labels) -> tuple[list[str], pd.DataFrame]:
    """Create reproducible business labels based on observed centroid RFM ranks."""
    profile = rfm.assign(cluster=labels).groupby("cluster").agg(
        Recency=("Recency", "mean"),
        Frequency=("Frequency", "mean"),
        Monetary=("Monetary", "mean"),
    )
    profile["r_rank"] = profile["Recency"].rank(ascending=True, method="first")
    profile["f_rank"] = profile["Frequency"].rank(ascending=False, method="first")
    profile["m_rank"] = profile["Monetary"].rank(ascending=False, method="first")
    n = len(profile)
    names = {}
    for cluster, row in profile.iterrows():
        if row["r_rank"] <= max(1, n / 3) and row["f_rank"] <= max(1, n / 2):
            name = "Champions"
        elif row["r_rank"] > n * 2 / 3:
            name = "At-risk/Lost"
        elif row["f_rank"] <= max(1, n / 2):
            name = "Loyal"
        else:
            name = "Developing"
        names[cluster] = f"{name} (C{cluster})"
    profile["segment"] = profile.index.map(names)
    return [names[label] for label in labels], profile.drop(columns=["r_rank", "f_rank", "m_rank"])
