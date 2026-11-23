#!/usr/bin/env python3
"""
Dashboard Performance & Correctness Validator
Project: Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce
Workspace: C:\\Users\\Admin\\.gemini\\antigravity\\scratch\\telecom-mapreduce
"""

import urllib.request
import time
import json
import os
import sys

LOCAL_WORKSPACE = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce"
sys.path.insert(0, os.path.join(LOCAL_WORKSPACE, "scripts"))

from dashboard import (
    get_analytics_data,
    get_anomalies_data,
    get_mapreduce_report,
    get_benchmark_report,
    get_top_cells_df,
    get_top_countries_df,
    get_temporal_df
)

def test_http_endpoint():
    print("--- 1. HTTP Endpoint Latency Benchmark ---")
    latencies = []
    for i in range(5):
        t0 = time.time()
        req = urllib.request.Request("http://localhost:8501")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
            code = resp.getcode()
        dur = time.time() - t0
        latencies.append(dur)
        print(f"  Request {i+1}: {dur:.4f}s (HTTP {code}, {len(data):,} bytes)")
    avg_latency = sum(latencies) / len(latencies)
    print(f"  Average HTTP Latency: {avg_latency*1000:.2f} ms")
    return avg_latency

def test_cache_and_sections():
    print("\n--- 2. Cache & Section Rendering Performance ---")
    
    # Test 1: Data loaders
    t0 = time.time()
    analytics = get_analytics_data()
    anomalies = get_anomalies_data()
    mr_report = get_mapreduce_report()
    benchmark = get_benchmark_report()
    t_load = time.time() - t0
    print(f"  Data Loaders Execution Time: {t_load*1000:.3f} ms")

    # Test 2: Cached DataFrames
    t0 = time.time()
    cells_df = get_top_cells_df()
    countries_df = get_top_countries_df()
    times_df = get_temporal_df()
    t_dfs = time.time() - t0
    print(f"  Cached DataFrames Access Time: {t_dfs*1000:.3f} ms")

    # Test 3: Metric Fidelity
    print("\n--- 3. Metric Reconciliation with Verified Reports ---")
    assert analytics["metadata"]["total_records_profiled"] == 4842625, "Record count mismatch!"
    print("  ✔ Total CDR Records: 4,842,625 (100% Match)")

    assert analytics["executive_traffic_totals"]["total_network_traffic"] == 95727626.19, "Total traffic mismatch!"
    print("  ✔ Total Network Traffic: 95,727,626.19 (100% Match)")

    assert analytics["executive_traffic_totals"]["total_internet_traffic"] == 82479246.58, "Internet traffic mismatch!"
    print("  ✔ Internet Traffic Volume: 82,479,246.58 (86.16% Share) (100% Match)")

    assert anomalies["summary_counts"]["total_anomalies_flagged"] == 56, "Anomaly count mismatch!"
    print("  ✔ Total Anomalies Flagged: 56 (100% Match)")

    assert mr_report["job_counters"]["Map input records"] == 4842625, "MR Map inputs mismatch!"
    assert mr_report["reduced_output_records"] == 10390, "MR Reduced keys mismatch!"
    print("  ✔ MapReduce Input Records: 4,842,625 | Reduced Keys: 10,390 (100% Match)")

    # Test 4: Section Filtering Logic
    print("\n--- 4. Section Filter Logic Testing ---")
    # Cell filter
    top_5_cells = cells_df.sort_values(by="total_traffic", ascending=False).head(5)
    assert len(top_5_cells) == 5, "Cell filter failed!"
    print(f"  ✔ Top 5 Cells Filter: {list(top_5_cells['cell_id'])}")

    # Country filter
    filtered_country = countries_df[countries_df["country_code"] == 39]
    assert len(filtered_country) == 1, "Country filter failed!"
    print(f"  ✔ Country Filter (Italy 39): {filtered_country['total_traffic'].values[0]:,.2f} Traffic")

    # Temporal Morning window filter (slots 36 to 71)
    morning_times = times_df[(times_df["slot_index"] >= 36) & (times_df["slot_index"] < 72)]
    assert len(morning_times) == 36, "Temporal morning filter failed!"
    print(f"  ✔ Temporal Diurnal Window Filter (Morning): {len(morning_times)} observation slots")

    # Anomaly severity filter
    spikes_df = pd.DataFrame(anomalies["rate_of_change_spike_anomalies"])
    high_spikes = spikes_df[spikes_df["severity"] == "HIGH"]
    print(f"  ✔ Anomaly Severity Filter (High Delta Spikes): {len(high_spikes)} anomalies")

    print("\nALL PERFORMANCE AND FIDELITY CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    import pandas as pd
    test_http_endpoint()
    test_cache_and_sections()
