import pandas as pd

from src.rfm import calculate_rfm


def test_rfm_values_for_three_customers():
    data = pd.DataFrame([
        [1, "A", pd.Timestamp("2011-01-01"), 10.0],
        [1, "B", pd.Timestamp("2011-01-10 23:59:00"), 20.0],
        [2, "C", pd.Timestamp("2011-01-05 12:00:00"), 5.0],
        [3, "D", pd.Timestamp("2011-01-08 23:00:00"), 7.0],
        [3, "D", pd.Timestamp("2011-01-08 23:00:00"), 3.0],
    ], columns=["Customer ID", "Invoice", "InvoiceDate", "Revenue"])
    result = calculate_rfm(data, snapshot_date="2011-01-11").set_index("Customer ID")

    assert result.loc[1, ["Recency", "Frequency", "Monetary"]].tolist() == [1, 2, 30.0]
    assert result.loc[2, ["Recency", "Frequency", "Monetary"]].tolist() == [6, 1, 5.0]
    assert result.loc[3, ["Recency", "Frequency", "Monetary"]].tolist() == [3, 1, 10.0]
