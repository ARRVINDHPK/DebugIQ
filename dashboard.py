import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

from analysis import compute_module_hotspots, compute_failure_frequency, compute_regression_health
from database import read_failures


st.set_page_config(page_title="DebugIQ Dashboard", layout="wide")

st.title("🔍 DebugIQ – Simulation Log Intelligence")

df = read_failures()

if df.empty:
    st.warning("No failures found in database yet. Run `python main.py` to analyze logs.")
    st.stop()

# --- Sidebar: Section 10: Debug Report Download ---
st.sidebar.title("Download Reports")
report_txt_path = Path("data") / "debug_report.txt"
report_md_path = Path("data") / "debug_report.md"

if report_txt_path.exists():
    with open(report_txt_path, "r") as f:
        st.sidebar.download_button(
            label="Download Text Report",
            data=f.read(),
            file_name="debug_report.txt",
            mime="text/plain",
        )

if report_md_path.exists():
    with open(report_md_path, "r") as f:
        st.sidebar.download_button(
            label="Download Markdown Report",
            data=f.read(),
            file_name="debug_report.md",
            mime="text/markdown",
        )

# --- Section 1: Regression Overview ---
st.header("1. Regression Overview")
health_score, severity_dist = compute_regression_health(df)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Regression Health Score", f"{health_score}/100")
with m2:
    st.metric("Total Failures", len(df))
with m3:
    st.metric("Unique Failures", df["failure_signature"].nunique())
with m4:
    critical_count = len(df[df["severity"].isin(["ERROR", "FATAL"])])
    st.metric("Critical Failures", critical_count)

st.markdown("---")

# --- Section 2 & 3: Ranking and Distribution ---
col_rank, col_dist = st.columns([2, 1])

with col_rank:
    st.header("2. Failure Priority Ranking")
    top_n = st.slider("Show top N failures", min_value=5, max_value=50, value=15, step=5)
    rank_cols = ["severity", "module", "category", "priority_score", "frequency", "message"]
    st.dataframe(df.sort_values("priority_score", ascending=False).head(top_n)[rank_cols], use_container_width=True)

with col_dist:
    st.header("3. Failure Category Distribution")
    if "category" in df.columns:
        cat_counts = df["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        fig_cat = px.pie(cat_counts, names="category", values="count", hole=0.4)
        st.plotly_chart(fig_cat, use_container_width=True)

st.markdown("---")

# --- Section 4 & 5: Clusters and Hotspots ---
col_clust, col_mod = st.columns(2)

with col_clust:
    st.header("4. Failure Clusters")
    if "cluster_id" in df.columns:
        cluster_view = df.groupby("cluster_id").agg(
            avg_priority=("priority_score", "mean"),
            count=("failure_signature", "size"),
        ).reset_index()
        fig_cluster = px.scatter(
            cluster_view,
            x="count",
            y="avg_priority",
            color="avg_priority",
            size="count",
            hover_data=["cluster_id"],
            title="Cluster Importance (Density vs Priority)"
        )
        st.plotly_chart(fig_cluster, use_container_width=True)

with col_mod:
    st.header("5. Module Hotspot Analysis")
    mod_hot = compute_module_hotspots(df)
    if not mod_hot.empty:
        fig_mod = px.bar(mod_hot, x="module", y="failures", color="failures", color_continuous_scale="Reds")
        st.plotly_chart(fig_mod, use_container_width=True)

st.markdown("---")

# --- Section 6: Failure Timeline ---
st.header("6. Failure Timeline")
if "timestamp_parsed" in df.columns and not df["timestamp_parsed"].isna().all():
    ts_df = df.copy().sort_values("timestamp_parsed")
    fig_time = px.scatter(
        ts_df,
        x="timestamp_parsed",
        y="priority_score",
        color="severity",
        hover_data=["module", "message"],
        height=400
    )
    st.plotly_chart(fig_time, use_container_width=True)

st.markdown("---")

# --- Section 7 & 8: Root Cause & Recommendations ---
st.header("7 & 8. Root Cause Suggestions & Debug Recommendations")
selected_fail = st.selectbox("Select a failure for deeper analysis (Top 100 by priority)", 
                             options=df.sort_values("priority_score", ascending=False).head(100).index,
                             format_func=lambda i: f"[{df.loc[i, 'module']}] {df.loc[i, 'message'][:80]}...")

rc_col, rec_col = st.columns(2)
with rc_col:
    st.subheader("Root Cause Suggestion")
    st.info(df.loc[selected_fail, "root_cause_suggestion"] if "root_cause_suggestion" in df.columns else "N/A")

with rec_col:
    st.subheader("Debug Recommendations")
    st.success(df.loc[selected_fail, "debug_actions"] if "debug_actions" in df.columns else "N/A")

st.markdown("---")

# --- Section 9: Known Bug Detection ---
st.header("9. Known Bug Detection")
known_df = df[df["known_bug_flag"] == 1]
if known_df.empty:
    st.write("No known bugs detected in this run.")
else:
    st.dataframe(
        known_df[["severity", "module", "category", "message", "frequency"]],
        use_container_width=True,
    )

