from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country",
]


def load_data(path: str | Path) -> pd.DataFrame:
    """Load an Online Retail II CSV and validate its expected schema."""
    data = pd.read_csv(path, dtype={"Invoice": "string", "StockCode": "string"})
    missing_columns = sorted(set(EXPECTED_COLUMNS) - set(data.columns))
    if missing_columns:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing_columns)}")
    return data
