import json
from pathlib import Path

import pandas as pd
import pytest
from sklearn.metrics import silhouette_score

from src.kpi import calculate_silhouette, customer_kpi_summary, repeat_customer_rate
from src.rfm import transform_rfm


def test_repeat_rate_and_silhouette_match_expected_values():
    transactions = pd.DataFrame([
        [1, "A"], [1, "B"], [2, "C"], [3, "D"], [3, "D"],
    ], columns=["Customer ID", "Invoice"])
    assert repeat_customer_rate(transactions) == 1 / 3 * 100

    features = [[0.0, 0.0], [0.1, 0.0], [5.0, 5.0], [5.1, 5.0]]
    labels = [0, 0, 1, 1]
    expected = silhouette_score(features, labels)
    assert -1 <= calculate_silhouette(features, labels) <= 1
    assert calculate_silhouette(features, labels) == expected


def test_dashboard_kpis_match_pipeline_output_when_available():
    root = Path(__file__).resolve().parents[1]
    customers_path = root / "data" / "processed" / "customer_segments.csv"
    metrics_path = root / "reports" / "kpi_summary.json"
    if not customers_path.exists() or not metrics_path.exists():
        pytest.skip("Run the pipeline first to validate dashboard/output parity")

    customers = pd.read_csv(customers_path)
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    _, scaled = transform_rfm(customers)
    dashboard = customer_kpi_summary(customers, scaled, customers["kmeans_segment"])

    assert dashboard["customer_count"] == metrics["customer_count"]
    assert dashboard["revenue_gbp"] == pytest.approx(metrics["revenue_gbp"])
    assert dashboard["repeat_customer_rate_pct"] == pytest.approx(metrics["repeat_customer_rate_pct"])
    assert dashboard["silhouette"] == pytest.approx(metrics["silhouette_kmeans"])
