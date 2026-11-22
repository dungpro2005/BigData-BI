from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path

import pandas as pd
import sklearn

from src.baseline import score_rfm
from src.clean import clean_data
from src.cluster import fit_kmeans, name_clusters
from src.evaluate import compare_methods, evaluate_candidates
from src.kpi import customer_kpi_summary, repeat_customer_rate, temporal_repurchase_rate
from src.load import load_data
from src.rfm import calculate_rfm, transform_rfm


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "Kaggle" / "online_retail_II.csv"


def _write_dictionary(raw: pd.DataFrame, out: Path) -> None:
    meanings = {
        "Invoice": "Invoice number; values beginning with C indicate cancellations",
        "StockCode": "Product or service stock code",
        "Description": "Product description",
        "Quantity": "Units in the transaction line",
        "InvoiceDate": "Transaction timestamp",
        "Price": "Unit price in GBP",
        "Customer ID": "Pseudonymous customer identifier",
        "Country": "Customer country",
    }
    rows = []
    for column in raw.columns:
        rows.append({
            "field": column,
            "dtype": str(raw[column].dtype),
            "meaning": meanings.get(column, "Source field"),
            "missing_pct": float(raw[column].isna().mean() * 100),
        })
    pd.DataFrame(rows).to_csv(out / "data_dictionary.csv", index=False)


def _write_business_outputs(customers: pd.DataFrame, output: Path, repeat_rate: float, temporal_rate: float) -> None:
    grouped = customers.groupby("kmeans_segment").agg(
        customers=("Customer ID", "nunique"),
        revenue_gbp=("Monetary", "sum"),
        frequency=("Frequency", "sum"),
        repeat_customers=("Frequency", lambda values: int(values.ge(2).sum())),
    ).reset_index()
    grouped["customer_share_pct"] = grouped["customers"] / len(customers) * 100
    grouped["revenue_share_pct"] = grouped["revenue_gbp"] / customers["Monetary"].sum() * 100
    grouped["mean_order_value_gbp"] = grouped["revenue_gbp"] / grouped["frequency"].replace(0, pd.NA)
    grouped.to_csv(output / "segment_insights.csv", index=False)

    campaigns = []
    for _, row in grouped.iterrows():
        for scenario, response_rate in (("low", 0.01), ("base", 0.03), ("high", 0.05)):
            cost_per_contact = 1.50
            campaign_cost = row["customers"] * cost_per_contact
            expected_revenue = row["customers"] * response_rate * row["mean_order_value_gbp"]
            campaigns.append({
                "segment": row["kmeans_segment"],
                "scenario": scenario,
                "assumed_response_rate_pct": response_rate * 100,
                "assumed_cost_per_contact_gbp": cost_per_contact,
                "customers": int(row["customers"]),
                "estimated_cost_gbp": campaign_cost,
                "estimated_revenue_gbp": expected_revenue,
                "estimated_roi_pct": (expected_revenue - campaign_cost) / campaign_cost * 100 if campaign_cost else 0,
                "note": "Illustrative gross revenue, not profit; assumptions require A/B validation",
            })
    pd.DataFrame(campaigns).to_csv(output / "campaign_sensitivity.csv", index=False)

    largest = grouped.sort_values("revenue_share_pct", ascending=False).iloc[0]
    largest_customers = grouped.sort_values("customer_share_pct", ascending=False).iloc[0]
    insights = [
        f"{largest['kmeans_segment']} đóng góp {largest['revenue_share_pct']:.1f}% doanh thu và chiếm {largest['customer_share_pct']:.1f}% khách.",
        f"{largest_customers['kmeans_segment']} là nhóm đông nhất, chiếm {largest_customers['customer_share_pct']:.1f}% khách và {largest_customers['revenue_share_pct']:.1f}% doanh thu.",
        f"Tỷ lệ khách có ít nhất hai hóa đơn trong toàn kỳ là {repeat_rate:.1f}%; tỷ lệ mua lại qua mốc 01/06/2011 là {temporal_rate:.1f}%.",
    ]
    (output / "insights.txt").write_text("\n".join(insights) + "\n", encoding="utf-8")


def run_pipeline(input_path: str | Path = DEFAULT_INPUT, output_dir: str | Path = ROOT / "reports") -> dict:
    output = Path(output_dir)
    logs = output / "logs"
    processed = ROOT / "data" / "processed"
    logs.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    timings = {}
    row_counts = {}

    t = time.perf_counter()
    raw = load_data(input_path)
    timings["load_seconds"] = time.perf_counter() - t
    row_counts["raw"] = len(raw)
    _write_dictionary(raw, output)

    t = time.perf_counter()
    clean, cancellations, quality = clean_data(raw)
    timings["clean_seconds"] = time.perf_counter() - t
    row_counts["clean"] = len(clean)
    row_counts["cancelled_separated"] = len(cancellations)
    quality.to_csv(output / "quality_before_after.csv", index=False)
    cancellations.to_csv(processed / "cancellations.csv", index=False)
    clean.to_csv(processed / "clean_transactions.csv", index=False)
    profile = {
        "input_file": str(input_path),
        "raw_rows": int(len(raw)),
        "raw_columns": int(len(raw.columns)),
        "raw_date_min": str(pd.to_datetime(raw["InvoiceDate"], errors="coerce").min()),
        "raw_date_max": str(pd.to_datetime(raw["InvoiceDate"], errors="coerce").max()),
        "clean_rows": int(len(clean)),
        "clean_customers": int(clean["Customer ID"].nunique()),
        "clean_invoices": int(clean["Invoice"].nunique()),
    }
    (output / "dataset_profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")

    t = time.perf_counter()
    rfm = calculate_rfm(clean)
    _, scaled = transform_rfm(rfm)
    timings["rfm_and_scale_seconds"] = time.perf_counter() - t
    row_counts["customers"] = len(rfm)

    t = time.perf_counter()
    candidates = evaluate_candidates(scaled)
    chosen_k = int(candidates.sort_values(
        ["silhouette", "davies_bouldin"], ascending=[False, True]
    ).iloc[0]["k"])
    _, km_labels = fit_kmeans(scaled, chosen_k)
    km_names, profile = name_clusters(rfm, km_labels)
    baseline = score_rfm(rfm)
    timings["cluster_and_evaluate_seconds"] = time.perf_counter() - t

    t = time.perf_counter()
    comparison = compare_methods(rfm, scaled, chosen_k)
    timings["method_comparison_seconds"] = time.perf_counter() - t
    candidates.to_csv(output / "cluster_diagnostics.csv", index=False)
    comparison.to_csv(output / "comparison.csv", index=False)
    profile.to_csv(output / "kmeans_cluster_profiles.csv", index=True)

    customers = rfm.copy()
    customers["Country"] = clean.groupby("Customer ID")["Country"].agg(
        lambda values: values.mode().iloc[0] if not values.mode().empty else "Unknown"
    ).reindex(customers["Customer ID"]).to_numpy()
    customers["baseline_segment"] = baseline["baseline_segment"].to_numpy()
    customers["kmeans_cluster"] = km_labels
    customers["kmeans_segment"] = km_names
    customers.to_csv(processed / "customer_segments.csv", index=False)

    kmeans_kpis = customer_kpi_summary(rfm, scaled, km_labels)
    baseline_kpis = customer_kpi_summary(rfm, scaled, baseline["baseline_segment"])
    repeat_rate = repeat_customer_rate(clean)
    temporal_rate = temporal_repurchase_rate(clean)
    metrics = {
        "snapshot_date": str(rfm["snapshot_date"].iloc[0].date()),
        "customer_count": kmeans_kpis["customer_count"],
        "revenue_gbp": kmeans_kpis["revenue_gbp"],
        "repeat_customer_rate_pct": kmeans_kpis["repeat_customer_rate_pct"],
        "temporal_repurchase_rate_pct": temporal_rate,
        "selected_k": chosen_k,
        "silhouette_kmeans": kmeans_kpis["silhouette"],
        "silhouette_baseline": baseline_kpis["silhouette"],
    }
    _write_business_outputs(customers, output, repeat_rate, temporal_rate)
    (output / "kpi_summary.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    try:
        ram_gib = round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / (1024 ** 3), 2)
    except (AttributeError, OSError, ValueError):
        ram_gib = None
    (output / "hardware.json").write_text(json.dumps({
        "cpu": platform.processor() or platform.machine(),
        "logical_cpu_count": __import__("os").cpu_count(),
        "ram_gib": ram_gib,
        "os": platform.platform(),
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
    }, indent=2), encoding="utf-8")

    duration = time.perf_counter() - started
    timings["total_seconds"] = duration
    log = {
        "started_at": pd.Timestamp.now().isoformat(),
        "input": str(input_path),
        "row_counts": row_counts,
        "timings_seconds": timings,
        "snapshot_date": metrics["snapshot_date"],
        "selected_k": chosen_k,
    }
    (logs / f"pipeline_{pd.Timestamp.now():%Y%m%d_%H%M%S}.json").write_text(
        json.dumps(log, indent=2), encoding="utf-8"
    )
    return {"metrics": metrics, "quality": quality, "comparison": comparison}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the customer segmentation pipeline")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=ROOT / "reports")
    args = parser.parse_args()
    result = run_pipeline(args.input, args.output)
    print(json.dumps(result["metrics"], indent=2))
