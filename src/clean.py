import re

import pandas as pd


NON_PRODUCT_CODES = {
    "ADJUST",
    "AMAZONFEE",
    "BANK CHARGES",
    "C2",
    "CRUK",
    "D",
    "DOT",
    "M",
    "PADS",
    "POST",
    "S",
    "TEST",
}


def is_product_stockcode(value: object) -> bool:
    """Keep normal stock codes and exclude known fees, postage, and adjustment codes."""
    code = str(value).strip().upper()
    if not code or code in NON_PRODUCT_CODES:
        return False
    return not bool(re.match(r"^(POSTAGE|BANK|AMAZONFEE|ADJUST)", code))


def _quality_row(name: str, data: pd.DataFrame) -> dict:
    rows = len(data)
    return {
        "stage": name,
        "rows": rows,
        "customers": data["Customer ID"].nunique(dropna=True) if "Customer ID" in data else 0,
        "invoices": data["Invoice"].nunique(dropna=True) if "Invoice" in data else 0,
        "missing_pct": (data.isna().sum().sum() / (rows * len(data.columns)) * 100) if rows else 0.0,
        "duplicate_pct": (data.duplicated().sum() / rows * 100) if rows else 0.0,
    }


def clean_data(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Clean transaction rows, retaining cancelled invoices separately.

    Returns cleaned rows, cancelled rows, and a stage-by-stage quality report.
    """
    required = {"Invoice", "StockCode", "Quantity", "InvoiceDate", "Price", "Customer ID"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Data is missing required columns: {', '.join(sorted(missing))}")

    cleaned = data.copy()
    cleaned["Customer ID"] = pd.to_numeric(cleaned["Customer ID"], errors="coerce")
    quality = [_quality_row("before", cleaned)]

    cleaned = cleaned.dropna(subset=["Customer ID"]).copy()
    quality.append(_quality_row("after_missing_customer_id", cleaned))

    cleaned = cleaned.drop_duplicates().copy()
    quality.append(_quality_row("after_duplicates", cleaned))

    cleaned["InvoiceDate"] = pd.to_datetime(cleaned["InvoiceDate"], errors="coerce")
    cleaned = cleaned.dropna(subset=["InvoiceDate"]).copy()
    quality.append(_quality_row("after_invalid_invoice_date", cleaned))

    is_cancelled = cleaned["Invoice"].astype("string").str.upper().str.startswith("C", na=False)
    cancelled = cleaned.loc[is_cancelled].copy()
    cleaned = cleaned.loc[~is_cancelled].copy()
    quality.append(_quality_row("after_cancelled_invoices", cleaned))

    cleaned["Quantity"] = pd.to_numeric(cleaned["Quantity"], errors="coerce")
    cleaned["Price"] = pd.to_numeric(cleaned["Price"], errors="coerce")
    cleaned = cleaned.loc[
        cleaned["Quantity"].gt(0) & cleaned["Price"].gt(0)
    ].copy()
    quality.append(_quality_row("after_nonpositive_quantity_or_price", cleaned))

    cleaned = cleaned.loc[cleaned["StockCode"].map(is_product_stockcode)].copy()
    cleaned["Revenue"] = cleaned["Quantity"] * cleaned["Price"]
    quality.append(_quality_row("after_non_product_stockcodes", cleaned))

    quality_df = pd.DataFrame(quality)
    quality_df["rows_removed_from_active_set"] = (
        quality_df["rows"].shift(1, fill_value=quality_df.iloc[0]["rows"]) - quality_df["rows"]
    )
    return cleaned, cancelled, quality_df
