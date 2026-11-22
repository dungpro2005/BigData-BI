import pandas as pd
from sklearn.metrics import silhouette_score


def repeat_customer_rate(transactions: pd.DataFrame) -> float:
    """Share of customers with at least two distinct invoices, in percent."""
    if transactions.empty:
        return 0.0
    invoices = transactions.groupby("Customer ID")["Invoice"].nunique()
    return float(invoices.ge(2).mean() * 100)


def calculate_silhouette(features, labels) -> float:
    """Return sklearn's silhouette score after validating cluster cardinality."""
    labels = pd.Series(labels)
    n_labels = labels.nunique()
    if n_labels < 2 or n_labels >= len(labels):
        raise ValueError("Silhouette requires between 2 and n_samples - 1 clusters")
    return float(silhouette_score(features, labels))


def customer_kpi_summary(customers: pd.DataFrame, features, labels) -> dict:
    """Shared dashboard/pipeline KPI calculation for a customer selection."""
    silhouette = float("nan")
    if len(customers) >= 3 and pd.Series(labels).nunique() > 1:
        silhouette = calculate_silhouette(features, labels)
    return {
        "customer_count": int(customers["Customer ID"].nunique()),
        "revenue_gbp": float(customers["Monetary"].sum()),
        "repeat_customer_rate_pct": (
            float(customers["Frequency"].ge(2).mean() * 100) if len(customers) else 0.0
        ),
        "silhouette": silhouette,
    }


def temporal_repurchase_rate(transactions: pd.DataFrame, cutoff="2011-06-01") -> float:
    """Share of pre-cutoff customers who also bought after the cutoff, in percent."""
    dates = pd.to_datetime(transactions["InvoiceDate"])
    cutoff = pd.Timestamp(cutoff)
    early = set(transactions.loc[dates < cutoff, "Customer ID"].dropna())
    later = set(transactions.loc[dates >= cutoff, "Customer ID"].dropna())
    return float(len(early & later) / len(early) * 100) if early else 0.0
