#!/usr/bin/env python3
"""
Optimized High-Performance Streamlit Telecom Performance Dashboard
Project: Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce
Workspace: C:\\Users\\Admin\\.gemini\\antigravity\\scratch\\telecom-mapreduce
"""

import os
import json
import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Telecom MapReduce Performance & Analytics",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

LOCAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORTS_DIR = os.path.join(LOCAL_DIR, "reports")

ANALYTICS_PATH = os.path.join(REPORTS_DIR, "telecom_analytics.json")
ANOMALY_PATH = os.path.join(REPORTS_DIR, "anomaly_report.json")
MR_PATH = os.path.join(REPORTS_DIR, "mapreduce_execution_report.json")
BENCHMARK_PATH = os.path.join(REPORTS_DIR, "performance_benchmark.json")

TOP_CELLS_CSV = os.path.join(REPORTS_DIR, "top_20_cells_total_traffic.csv")
TOP_COUNTRIES_CSV = os.path.join(REPORTS_DIR, "top_20_countries_traffic.csv")
TIME_CSV = os.path.join(REPORTS_DIR, "time_interval_traffic.csv")

# -----------------------------------------------------------------------------
# GRANULAR CACHED DATA LOADERS (@st.cache_data)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_analytics_data():
    with open(ANALYTICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def get_anomalies_data():
    with open(ANOMALY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def get_mapreduce_report():
    with open(MR_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def get_benchmark_report():
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def get_top_cells_df():
    if os.path.exists(TOP_CELLS_CSV):
        return pd.read_csv(TOP_CELLS_CSV)
    data = get_analytics_data()
    return pd.DataFrame(data["top_20_cells_by_total_traffic"])

@st.cache_data(show_spinner=False)
def get_top_countries_df():
    if os.path.exists(TOP_COUNTRIES_CSV):
        return pd.read_csv(TOP_COUNTRIES_CSV)
    data = get_analytics_data()
    return pd.DataFrame(data["top_20_countries_by_traffic"])

@st.cache_data(show_spinner=False)
def get_temporal_df():
    if os.path.exists(TIME_CSV):
        return pd.read_csv(TIME_CSV)
    data = get_analytics_data()
    return pd.DataFrame(data["temporal_distribution"])

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION & GLOBAL CONTROLS
# -----------------------------------------------------------------------------
st.sidebar.title("📡 Telecom Big Data")
st.sidebar.markdown("**Project:** Telecom MapReduce & Performance Monitoring")
st.sidebar.markdown("**Hadoop Release:** Apache Hadoop 3.4.0 (HDFS)")
st.sidebar.markdown("**Dataset:** Telecom Italia Milan CDR (Day 1)")
st.sidebar.markdown("---")

section = st.sidebar.radio(
    "Navigation Menu",
    [
        "1. Executive Overview",
        "2. Telecom Traffic Analytics",
        "3. Cell Tower Performance",
        "4. Country-Level Traffic",
        "5. Temporal Traffic Monitoring",
        "6. Anomaly Detection",
        "7. MapReduce Execution Metrics"
    ]
)

st.sidebar.markdown("---")
st.sidebar.success("⚡ Optimized Engine: Zero-Lag In-Memory Caching & Precomputed TSV/JSON streams.")

# -----------------------------------------------------------------------------
# SECTION 1: EXECUTIVE OVERVIEW
# -----------------------------------------------------------------------------
def render_executive():
    st.title("📊 Executive Overview: Telecom Traffic & Infrastructure")
    st.markdown("High-level key performance indicators derived from MapReduce processing of the Milan Call Detail Record (CDR) dataset.")

    analytics = get_analytics_data()
    anomalies = get_anomalies_data()
    totals = analytics["executive_traffic_totals"]
    total_recs = analytics["metadata"]["total_records_profiled"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total CDR Records", f"{total_recs:,}", "100% Validated")
    col2.metric("Total Network Traffic", f"{totals['total_network_traffic']:,.0f}", "Normalized Units")
    col3.metric("Internet Traffic Share", f"{totals['internet_traffic_percentage']}%", f"{totals['total_internet_traffic']:,.0f} Units")
    col4.metric("Anomalies Detected", f"{anomalies['summary_counts']['total_anomalies_flagged']}", "56 Statistical Outliers")

    st.markdown("---")
    st.subheader("Traffic Channel Breakdown")
    c1, c2, c3 = st.columns(3)
    c1.metric("Mobile Internet Data", f"{totals['total_internet_traffic']:,.1f}", "86.16% Total Volume")
    c2.metric("Short Message Service (SMS)", f"{totals['sms_metrics']['total_sms']:,.1f}", "7.76% Total Volume")
    c3.metric("Voice Calls", f"{totals['call_metrics']['total_calls']:,.1f}", "6.08% Total Volume")

    st.markdown("---")
    st.subheader("Spatial & Temporal Bounds")
    b1, b2, b3 = st.columns(3)
    b1.info(f"**Spatial Coverage:** 10,000 / 10,000 Cells (100.0% Milan Metropolitan Grid)")
    b2.info(f"**Temporal Scope:** 144 Intervals (24 Hours from 2013-10-31 23:00 to 2013-11-01 22:50 UTC)")
    b3.info(f"**International Scope:** 246 Sovereign Calling Prefixes Logged")

# -----------------------------------------------------------------------------
# SECTION 2: TELECOM TRAFFIC ANALYTICS
# -----------------------------------------------------------------------------
def render_analytics():
    st.title("📈 Telecom Multi-Channel Traffic Analytics")
    st.markdown("In-depth analysis of directional communication patterns across SMS, Voice Calls, and Packet Internet.")

    analytics = get_analytics_data()
    totals = analytics["executive_traffic_totals"]
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📩 SMS Directional Balance")
        sms_df = pd.DataFrame({
            "Direction": ["Inbound SMS", "Outbound SMS"],
            "Traffic Volume": [totals["sms_metrics"]["inbound_sms"], totals["sms_metrics"]["outbound_sms"]]
        })
        st.bar_chart(sms_df.set_index("Direction"))
        st.write(f"- **Inbound SMS:** {totals['sms_metrics']['inbound_sms']:,.2f}")
        st.write(f"- **Outbound SMS:** {totals['sms_metrics']['outbound_sms']:,.2f}")
        st.write(f"- **Inbound / Outbound Ratio:** **{totals['sms_metrics']['inbound_to_outbound_ratio']}** (1.63x inbound bias)")

    with c2:
        st.subheader("📞 Voice Calls Directional Balance")
        call_df = pd.DataFrame({
            "Direction": ["Inbound Calls", "Outbound Calls"],
            "Traffic Volume": [totals["call_metrics"]["inbound_calls"], totals["call_metrics"]["outbound_calls"]]
        })
        st.bar_chart(call_df.set_index("Direction"))
        st.write(f"- **Inbound Calls:** {totals['call_metrics']['inbound_calls']:,.2f}")
        st.write(f"- **Outbound Calls:** {totals['call_metrics']['outbound_calls']:,.2f}")
        st.write(f"- **Inbound / Outbound Ratio:** **{totals['call_metrics']['inbound_to_outbound_ratio']}** (0.82x, outbound dominant)")

    st.markdown("---")
    st.subheader("Service Channel Volume Comparison")
    chan_df = pd.DataFrame({
        "Service Channel": ["Mobile Internet", "Inbound SMS", "Outbound Voice", "Outbound SMS", "Inbound Voice"],
        "Normalized Volume": [
            totals["total_internet_traffic"],
            totals["sms_metrics"]["inbound_sms"],
            totals["call_metrics"]["outbound_calls"],
            totals["sms_metrics"]["outbound_sms"],
            totals["call_metrics"]["inbound_calls"]
        ]
    })
    st.bar_chart(chan_df.set_index("Service Channel"))

# -----------------------------------------------------------------------------
# SECTION 3: CELL TOWER PERFORMANCE
# -----------------------------------------------------------------------------
def render_cells():
    st.title("🗼 Cell Tower Performance & Spatial Concentration")
    st.markdown("Evaluation of traffic load distribution and infrastructure hotspotting across 10,000 spatial cells.")

    analytics = get_analytics_data()
    conc = analytics["traffic_concentration"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Gini Inequality Index", f"{conc['gini_coefficient']}", "High Concentration")
    col2.metric("Top 1% Cells Share", f"{conc['top_1_percent_cells_share_pct']}%", "100 Busiest Cells")
    col3.metric("Top 5% Cells Share", f"{conc['top_5_percent_cells_share_pct']}%", "500 Busiest Cells")
    col4.metric("Pareto Top 20% Share", f"{conc['pareto_top_20_percent_cells_share_pct']}%", "63.1% of All Traffic")

    st.markdown("---")
    # Interactive Filter Control
    f1, f2 = st.columns([1, 3])
    with f1:
        top_n = st.slider("Select Top N Busiest Cells to Display", min_value=5, max_value=20, value=10, step=5)
    with f2:
        sort_metric = st.selectbox("Sort Ranking By", ["total_traffic", "internet", "sms_total", "calls_total"], index=0)

    top_cells_df = get_top_cells_df()
    sorted_cells_df = top_cells_df.sort_values(by=sort_metric, ascending=False).head(top_n)

    st.subheader(f"🏆 Top {top_n} Busiest Cells Ranked by {sort_metric.replace('_', ' ').title()}")
    st.dataframe(sorted_cells_df, use_container_width=True)

    st.subheader(f"Top {top_n} Cells Traffic Composition")
    st.bar_chart(sorted_cells_df.set_index("cell_id")[["internet", "sms_total", "calls_total"]])

    st.markdown("---")
    st.subheader("🌐 Top 20 Cells by Internet Traffic Volume")
    top_net_df = pd.DataFrame(analytics["top_20_cells_by_internet_traffic"])
    st.dataframe(top_net_df, use_container_width=True)

# -----------------------------------------------------------------------------
# SECTION 4: COUNTRY-LEVEL TRAFFIC
# -----------------------------------------------------------------------------
def render_countries():
    st.title("🌍 Country-Level & Roaming Partner Traffic")
    st.markdown("Analysis of international origin and destination telecommunications traffic across 246 countries.")

    top_countries_df = get_top_countries_df()

    # Interactive Filter Control
    f1, f2 = st.columns([1, 3])
    with f1:
        top_k = st.slider("Select Top N Countries to Display", min_value=5, max_value=20, value=10, step=5)
    with f2:
        search_cc = st.text_input("Filter by Calling Code (e.g. 39 for Italy, 33 for France, 1 for USA)", value="")

    filtered_countries = top_countries_df
    if search_cc.strip().isdigit():
        filtered_countries = top_countries_df[top_countries_df["country_code"] == int(search_cc.strip())]
    else:
        filtered_countries = top_countries_df.head(top_k)

    st.subheader(f"Top {len(filtered_countries)} International Calling Prefixes")
    st.dataframe(filtered_countries, use_container_width=True)

    if not filtered_countries.empty:
        st.subheader("International Traffic Volume Chart")
        st.bar_chart(filtered_countries.set_index("country_code")[["total_traffic"]])
    st.caption("Country Code 39 represents Domestic Italy. Code 0 represents Internal / Undisclosed CDR traffic.")

# -----------------------------------------------------------------------------
# SECTION 5: TEMPORAL TRAFFIC MONITORING
# -----------------------------------------------------------------------------
def render_temporal():
    st.title("⏰ Temporal Traffic Monitoring (24-Hour Diurnal Cycle)")
    st.markdown("Traffic intensity over 144 non-overlapping 10-minute intervals throughout November 1, 2013.")

    analytics = get_analytics_data()
    times_df = get_temporal_df()

    col1, col2 = st.columns(2)
    peak = analytics["extreme_traffic_intervals"]["peak_interval"]
    lowest = analytics["extreme_traffic_intervals"]["lowest_interval"]
    col1.metric("Peak Interval", f"{peak['time_utc'][11:16]} UTC", f"{peak['total_traffic']:,.0f} Volume")
    col2.metric("Lowest Interval", f"{lowest['time_utc'][11:16]} UTC", f"{lowest['total_traffic']:,.0f} Volume")

    st.markdown("---")
    # Time window filter
    st.subheader("Time Window Filter")
    window_choice = st.radio(
        "Select Diurnal Window",
        ["Full 24 Hours (All 144 Intervals)", "Morning Peak (06:00 - 12:00 UTC)", "Afternoon Active (12:00 - 18:00 UTC)", "Evening & Night (18:00 - 06:00 UTC)"],
        horizontal=True
    )

    if "Morning" in window_choice:
        filtered_times = times_df[(times_df["slot_index"] >= 36) & (times_df["slot_index"] < 72)]
    elif "Afternoon" in window_choice:
        filtered_times = times_df[(times_df["slot_index"] >= 72) & (times_df["slot_index"] < 108)]
    elif "Evening" in window_choice:
        filtered_times = times_df[(times_df["slot_index"] >= 108) | (times_df["slot_index"] < 36)]
    else:
        filtered_times = times_df

    st.subheader(f"Traffic Curve ({len(filtered_times)} Observation Slots)")
    st.line_chart(filtered_times.set_index("time_utc")[["total_traffic", "internet", "sms", "calls"]])

    st.subheader("Interval Telemetry Data Table")
    st.dataframe(filtered_times, use_container_width=True)

# -----------------------------------------------------------------------------
# SECTION 6: ANOMALY DETECTION
# -----------------------------------------------------------------------------
def render_anomalies():
    st.title("⚠️ Network Anomaly & Hotspot Detection Engine")
    st.markdown("Explainable anomaly detection using non-parametric Median Absolute Deviation (MAD) and Modified Z-scores.")

    st.caption("ℹ️ *Disclaimer: All detected anomalies represent empirical statistical deviations in CDR traffic volume and do not indicate confirmed physical equipment outages or network hardware failures.*")

    anomalies = get_anomalies_data()
    counts = anomalies["summary_counts"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Rate-of-Change Spikes", f"{counts['rate_of_change_spikes_detected']}")
    c2.metric("Cell Hotspot Outliers", f"{counts['cell_hotspot_anomalies_detected']}")
    c3.metric("Total Flagged Anomalies", f"{counts['total_anomalies_flagged']}")

    st.markdown("---")
    # Severity Filter
    f_sev = st.selectbox("Filter Anomalies by Severity", ["ALL SEVERITIES", "CRITICAL", "HIGH", "MODERATE"], index=0)

    st.subheader("⚡ Rate-of-Change (Delta) Temporal Spikes")
    spikes_df = pd.DataFrame(anomalies["rate_of_change_spike_anomalies"])
    if not spikes_df.empty:
        if f_sev != "ALL SEVERITIES":
            spikes_df = spikes_df[spikes_df["severity"] == f_sev]
        st.dataframe(spikes_df, use_container_width=True)

    st.markdown("---")
    st.subheader("🔥 Top Cell Hotspot Anomalies")
    hotspots_df = pd.DataFrame(anomalies["cell_hotspot_anomalies"])
    if not hotspots_df.empty:
        if f_sev != "ALL SEVERITIES":
            hotspots_df = hotspots_df[hotspots_df["severity"] == f_sev]
        st.dataframe(hotspots_df, use_container_width=True)

# -----------------------------------------------------------------------------
# SECTION 7: MAPREDUCE EXECUTION METRICS
# -----------------------------------------------------------------------------
def render_mapreduce():
    st.title("⚙️ Apache Hadoop MapReduce Execution Metrics")
    st.markdown("Comprehensive audit of the Hadoop Streaming aggregation job executed over the clean HDFS dataset.")

    mr_report = get_mapreduce_report()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Execution Mode", "LocalJobRunner", "Single-Node HDFS")
    c2.metric("Input Records", f"{mr_report['input_records']:,}", "4.84M Records")
    c3.metric("Execution Duration", f"{mr_report['execution_duration_seconds']}s", "Fast Stream")
    c4.metric("Throughput", f"{mr_report['throughput_records_per_sec']:,.0f}", "Records / Sec")

    st.markdown("---")
    st.subheader("Hadoop Job Counters Telemetry")
    counters_df = pd.DataFrame([
        {"Hadoop Counter Name": k, "Counter Value": f"{v:,}"}
        for k, v in mr_report["job_counters"].items()
    ])
    st.dataframe(counters_df, use_container_width=True)

    st.markdown("---")
    st.subheader("HDFS Output Directory Verification")
    for item in mr_report["output_verification"]["hdfs_listing"]:
        st.code(item)

# -----------------------------------------------------------------------------
# LAZY DISPATCHER
# -----------------------------------------------------------------------------
section_dispatch = {
    "1. Executive Overview": render_executive,
    "2. Telecom Traffic Analytics": render_analytics,
    "3. Cell Tower Performance": render_cells,
    "4. Country-Level Traffic": render_countries,
    "5. Temporal Traffic Monitoring": render_temporal,
    "6. Anomaly Detection": render_anomalies,
    "7. MapReduce Execution Metrics": render_mapreduce
}

# Execute only the active section
with st.spinner("Rendering telemetry..."):
    section_dispatch[section]()
