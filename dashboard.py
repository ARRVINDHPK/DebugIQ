import pandas as pd
import plotly.express as px
import streamlit as st

from analysis import compute_module_hotspots, compute_failure_frequency, compute_regression_health
from database import read_failures


st.set_page_config(page_title="DebugIQ Dashboard", layout="wide")

st.title("🔍 DebugIQ – Simulation Log Intelligence")

df = read_failures()

if df.empty:
    st.warning("No failures found in database yet. Run `python main.py` to analyze logs.")
    st.stop()

health_score, severity_dist = compute_regression_health(df)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Regression Health Score", f"{health_score}/100")
with col2:
    st.metric("Total Failures", len(df))
with col3:
    st.metric("Unique Failures", df["failure_signature"].nunique())

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    # Failure category distribution
    if "category" in df.columns:
        cat_counts = df["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        fig_cat = px.pie(cat_counts, names="category", values="count", title="Failure Categories")
        st.plotly_chart(fig_cat, use_container_width=True)

    # Module hotspots
    mod_hot = compute_module_hotspots(df)
    if not mod_hot.empty:
        fig_mod = px.bar(mod_hot, x="module", y="failures", title="Module Hotspots")
        st.plotly_chart(fig_mod, use_container_width=True)

with col_right:
    # Failure timeline chart
    if "timestamp_parsed" in df.columns and not df["timestamp_parsed"].isna().all():
        ts_df = df.copy()
        ts_df = ts_df.sort_values("timestamp_parsed")
        fig_time = px.scatter(
            ts_df,
            x="timestamp_parsed",
            y="priority_score",
            color="severity",
            title="Failure Timeline (by priority)",
            hover_data=["module", "category", "message"],
        )
        st.plotly_chart(fig_time, use_container_width=True)

    # Cluster visualization (priority vs frequency)
    if "cluster_id" in df.columns:
        cluster_view = df.groupby("cluster_id").agg(
            avg_priority=("priority_score", "mean"),
            count=("failure_signature", "size"),
        ).reset_index()
        fig_cluster = px.scatter(
            cluster_view,
            x="count",
            y="avg_priority",
            color="cluster_id",
            size="count",
            title="Failure Clusters (size vs. avg priority)",
        )
        st.plotly_chart(fig_cluster, use_container_width=True)

st.markdown("---")

st.subheader("Top Priority Failures")
top_n = st.slider("Show top N failures", min_value=5, max_value=50, value=20, step=5)
cols = [
    "severity",
    "module",
    "category",
    "message",
    "priority_score",
    "frequency",
    "cluster_id",
    "known_bug_flag",
]
subset = df.sort_values("priority_score", ascending=False).head(top_n)[cols]
st.dataframe(subset, use_container_width=True)

st.subheader("Known Bugs")
known_df = df[df["known_bug_flag"] == 1]
if known_df.empty:
    st.write("No known bugs detected in this run.")
else:
    st.dataframe(
        known_df[
            [
                "severity",
                "module",
                "category",
                "message",
                "failure_signature",
                "frequency",
            ]
        ],
        use_container_width=True,
    )

