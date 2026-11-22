import pandas as pd

from src.clean import clean_data


def test_clean_removes_invalid_rows_and_separates_cancellations():
    data = pd.DataFrame([
        ["100", "12345", "Valid", 2, "2011-01-01", 3.0, 1, "UK"],
        ["101", "12345", "Missing customer", 1, "2011-01-02", 3.0, None, "UK"],
        ["C102", "12345", "Cancelled", 1, "2011-01-03", 3.0, 1, "UK"],
        ["103", "12345", "Zero price", 1, "2011-01-04", 0.0, 1, "UK"],
    ], columns=["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID", "Country"])

    clean, cancelled, quality = clean_data(data)

    assert clean["Invoice"].tolist() == ["100"]
    assert cancelled["Invoice"].tolist() == ["C102"]
    assert quality.iloc[0]["rows"] == 4
    assert quality.iloc[-1]["rows"] == 1
    assert quality["rows_removed_from_active_set"].sum() == 3
