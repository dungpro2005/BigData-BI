from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.kpi import customer_kpi_summary
from src.rfm import transform_rfm


ROOT = Path(__file__).resolve().parents[1]
CUSTOMERS_PATH = ROOT / "data" / "processed" / "customer_segments.csv"
DIAGNOSTICS_PATH = ROOT / "reports" / "cluster_diagnostics.csv"
COMPARISON_PATH = ROOT / "reports" / "comparison.csv"

st.set_page_config(page_title="Phân khúc khách hàng", layout="wide")
st.title("Phân khúc khách hàng theo hành vi mua sắm")
st.caption("Dữ liệu Online Retail II | Phân khúc được tạo trên toàn bộ kỳ dữ liệu.")

if not CUSTOMERS_PATH.exists():
    st.error("Chưa có dữ liệu đầu ra. Hãy chạy `python3 -m src.pipeline` trước.")
    st.stop()

customers = pd.read_csv(CUSTOMERS_PATH, parse_dates=["last_purchase", "snapshot_date"])
method = st.sidebar.selectbox("Phương pháp phân khúc", ["K-Means", "Baseline"])
segment_col = "kmeans_segment" if method == "K-Means" else "baseline_segment"
countries = sorted(customers["Country"].dropna().unique())
selected_countries = st.sidebar.multiselect("Quốc gia", countries, default=countries)
min_date = customers["last_purchase"].min().date()
max_date = customers["last_purchase"].max().date()
date_range = st.sidebar.date_input("Ngày mua gần nhất", value=(min_date, max_date))
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_date, end_date = pd.Timestamp(min_date), pd.Timestamp(max_date)
all_segments = sorted(customers[segment_col].dropna().unique())
selected_segments = st.sidebar.multiselect("Phân khúc", all_segments, default=all_segments)

filtered = customers.loc[
    customers["Country"].isin(selected_countries)
    & customers["last_purchase"].between(start_date, end_date + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1))
    & customers[segment_col].isin(selected_segments)
].copy()

if not filtered.empty:
    _, scaled = transform_rfm(filtered)
    selected_kpis = customer_kpi_summary(filtered, scaled, filtered[segment_col])
    sil = selected_kpis["silhouette"]
else:
    selected_kpis = {
        "customer_count": 0,
        "revenue_gbp": 0.0,
        "repeat_customer_rate_pct": 0.0,
        "silhouette": float("nan"),
    }
    sil = selected_kpis["silhouette"]

metrics = st.columns(4)
metrics[0].metric("Số khách hàng", f"{selected_kpis['customer_count']:,}")
metrics[1].metric("Doanh thu (GBP)", f"£{selected_kpis['revenue_gbp']:,.2f}")
metrics[2].metric("Silhouette", f"{sil:.3f}" if pd.notna(sil) else "N/A")
metrics[3].metric(
    "Khách quay lại",
    f"{selected_kpis['repeat_customer_rate_pct']:.1f}%" if len(filtered) else "N/A",
)

if filtered.empty:
    st.warning("Không có khách hàng thỏa bộ lọc.")
    st.stop()

left, right = st.columns(2)
summary = filtered.groupby(segment_col, as_index=False).agg(
    customers=("Customer ID", "nunique"), revenue=("Monetary", "sum")
)
with left:
    st.plotly_chart(px.bar(summary, x=segment_col, y="customers", title="Số khách theo phân khúc"), use_container_width=True)
with right:
    st.plotly_chart(px.bar(summary, x=segment_col, y="revenue", title="Doanh thu theo phân khúc"), use_container_width=True)

left, right = st.columns(2)
with left:
    st.plotly_chart(
        px.scatter(filtered, x="Frequency", y="Monetary", color=segment_col,
                   hover_data=["Customer ID", "Recency", "Country"], log_x=True, log_y=True,
                   title="RFM: Frequency – Monetary"),
        use_container_width=True,
    )
with right:
    heat = filtered.pivot_table(index="Recency", columns="Frequency", values="Customer ID", aggfunc="count", fill_value=0)
    st.plotly_chart(px.imshow(heat, aspect="auto", title="Mật độ khách theo Recency – Frequency"), use_container_width=True)

if DIAGNOSTICS_PATH.exists():
    diagnostics = pd.read_csv(DIAGNOSTICS_PATH)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=diagnostics["k"], y=diagnostics["inertia"], name="Inertia"))
    fig.add_trace(go.Scatter(x=diagnostics["k"], y=diagnostics["silhouette"], name="Silhouette", yaxis="y2"))
    fig.update_layout(title="Chọn số cụm K-Means", xaxis_title="k",
                      yaxis=dict(title="Inertia"),
                      yaxis2=dict(title="Silhouette", overlaying="y", side="right"))
    st.plotly_chart(fig, use_container_width=True)

if COMPARISON_PATH.exists():
    st.subheader("So sánh phương pháp trên cùng không gian RFM chuẩn hóa")
    st.dataframe(pd.read_csv(COMPARISON_PATH), use_container_width=True, hide_index=True)

st.subheader("RFM trung bình theo phân khúc")
st.dataframe(
    filtered.groupby(segment_col, as_index=False).agg(
        customers=("Customer ID", "nunique"),
        mean_recency_days=("Recency", "mean"),
        mean_frequency=("Frequency", "mean"),
        mean_monetary_gbp=("Monetary", "mean"),
        revenue_gbp=("Monetary", "sum"),
    ),
    use_container_width=True,
    hide_index=True,
)
