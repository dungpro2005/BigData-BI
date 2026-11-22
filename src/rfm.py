import numpy as np
import pandas as pd


def calculate_rfm(transactions: pd.DataFrame, snapshot_date=None) -> pd.DataFrame:
    """Calculate customer RFM with the required snapshot convention."""
    required = {"Customer ID", "Invoice", "InvoiceDate", "Revenue"}
    missing = required - set(transactions.columns)
    if missing:
        raise ValueError(f"Transactions are missing required columns: {', '.join(sorted(missing))}")
    if transactions.empty:
        raise ValueError("Cannot calculate RFM from an empty transaction table")

    dates = pd.to_datetime(transactions["InvoiceDate"], errors="coerce")
    if dates.isna().any():
        raise ValueError("InvoiceDate contains invalid dates; clean the data first")
    if snapshot_date is None:
        snapshot_date = dates.max().normalize() + pd.Timedelta(days=1)
    snapshot = pd.Timestamp(snapshot_date)
    if snapshot.tz is not None:
        snapshot = snapshot.tz_localize(None)

    work = transactions.assign(InvoiceDate=dates)
    rfm = work.groupby("Customer ID", as_index=False).agg(
        last_purchase=("InvoiceDate", "max"),
        Frequency=("Invoice", "nunique"),
        Monetary=("Revenue", "sum"),
    )
    rfm["Recency"] = (
        snapshot.normalize() - rfm["last_purchase"].dt.normalize()
    ).dt.days
    rfm["Monetary"] = rfm["Monetary"].astype(float)
    rfm["snapshot_date"] = snapshot
    return rfm[["Customer ID", "Recency", "Frequency", "Monetary", "last_purchase", "snapshot_date"]]


def transform_rfm(rfm: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """log1p-transform skewed RFM and standardize the common comparison space."""
    from sklearn.preprocessing import StandardScaler

    columns = ["Recency", "Frequency", "Monetary"]
    values = rfm[columns].astype(float).copy()
    values["Recency"] = np.log1p(values["Recency"].clip(lower=0))
    values["Frequency"] = np.log1p(values["Frequency"].clip(lower=0))
    values["Monetary"] = np.log1p(values["Monetary"].clip(lower=0))
    scaler = StandardScaler()
    scaled = pd.DataFrame(scaler.fit_transform(values), columns=columns, index=rfm.index)
    return values, scaled
