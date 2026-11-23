#!/usr/bin/env python3
"""
Network Performance Monitoring & CDR Traffic Anomaly Detector
Project: Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce
Workspace: C:\\Users\\Admin\\.gemini\antigravity\\scratch\\telecom-mapreduce

Applies robust non-parametric statistical methods:
- Median and Median Absolute Deviation (MAD)
- Modified Z-Score (Boris Iglewicz and David Hoaglin standard)
- First-order temporal rate-of-change delta spike analysis
- Heavy-tail cell traffic intensity thresholding
"""

import os
import sys
import json
import math
import subprocess
from datetime import datetime, timezone

LOCAL_WORKSPACE = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce"
ANALYTICS_JSON = os.path.join(LOCAL_WORKSPACE, "reports", "telecom_analytics.json")
LOCAL_MR_OUTPUT = os.path.join(LOCAL_WORKSPACE, "data", "processed", "mapreduce", "part-00000")
REPORTS_DIR = os.path.join(LOCAL_WORKSPACE, "reports")
HDFS_ANOMALIES_DIR = "/telecom/results/anomalies"

def run_wsl(bash_cmd):
    p = subprocess.run(
        ["wsl.exe", "-d", "Ubuntu", "-u", "dminmlops", "-e", "bash", "-c", f"source /etc/profile; {bash_cmd}"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def compute_median(data):
    s = sorted(data)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2.0

def compute_mad(data, med=None):
    if med is None:
        med = compute_median(data)
    deviations = [abs(x - med) for x in data]
    return compute_median(deviations)

def main():
    print("=" * 70)
    print("PHASE 6: NETWORK PERFORMANCE MONITORING & ANOMALY DETECTION")
    print("=" * 70)

    if not os.path.exists(ANALYTICS_JSON):
        print("ERROR: Analytics file not found! Run generate_analytics.py first.")
        sys.exit(1)

    with open(ANALYTICS_JSON, "r", encoding="utf-8") as f:
        analytics = json.load(f)

    times = analytics["temporal_distribution"]
    
    # ---------------------------------------------------------
    # 1. Temporal Anomalies (High Traffic & Delta Spikes)
    # ---------------------------------------------------------
    traffic_vals = [t["total_traffic"] for t in times]
    med_traffic = compute_median(traffic_vals)
    mad_traffic = compute_mad(traffic_vals, med_traffic)
    if mad_traffic == 0:
        mad_traffic = 1.0

    temporal_anomalies = []
    for t in times:
        val = t["total_traffic"]
        mod_z = 0.6745 * (val - med_traffic) / mad_traffic

        # Identify positive traffic surge anomalies (z > 2.0)
        if mod_z >= 2.0:
            severity = "CRITICAL" if mod_z >= 3.5 else ("HIGH" if mod_z >= 2.8 else "MODERATE")
            temporal_anomalies.append({
                "type": "TEMPORAL_TRAFFIC_SURGE",
                "timestamp": t["timestamp"],
                "time_utc": t["time_utc"],
                "observed_value": round(val, 2),
                "baseline_median": round(med_traffic, 2),
                "mad_scale": round(mad_traffic, 2),
                "deviation_score": round(mod_z, 3),
                "severity": severity,
                "explanation": f"Observed traffic of {val:,.2f} exceeds median baseline ({med_traffic:,.2f}) by a modified z-score of {mod_z:.2f}. Indicates surge period (inferred from CDR volume)."
            })

    # Rate-of-change (Delta) Spikes
    delta_vals = []
    for i in range(1, len(times)):
        delta = times[i]["total_traffic"] - times[i - 1]["total_traffic"]
        delta_vals.append(delta)

    med_delta = compute_median([abs(d) for d in delta_vals])
    mad_delta = compute_mad([abs(d) for d in delta_vals], med_delta)
    if mad_delta == 0:
        mad_delta = 1.0

    delta_spikes = []
    for i in range(1, len(times)):
        curr = times[i]
        prev = times[i - 1]
        raw_delta = curr["total_traffic"] - prev["total_traffic"]
        abs_delta = abs(raw_delta)
        delta_z = 0.6745 * (abs_delta - med_delta) / mad_delta

        if delta_z >= 2.5:
            direction = "SURGE" if raw_delta > 0 else "DROP"
            severity = "HIGH" if delta_z >= 3.5 else "MODERATE"
            delta_spikes.append({
                "type": f"RATE_OF_CHANGE_{direction}",
                "timestamp": curr["timestamp"],
                "time_utc": curr["time_utc"],
                "observed_delta": round(raw_delta, 2),
                "prior_interval_traffic": round(prev["total_traffic"], 2),
                "current_interval_traffic": round(curr["total_traffic"], 2),
                "baseline_median_delta": round(med_delta, 2),
                "deviation_score": round(delta_z, 3),
                "severity": severity,
                "explanation": f"Sudden interval-to-interval {direction.lower()} of {raw_delta:+,.2f} traffic volume from {prev['time_utc']} to {curr['time_utc']} (Delta Z: {delta_z:.2f})."
            })

    # ---------------------------------------------------------
    # 2. Cell-Level Activity Anomalies (Extreme Intensity Cells)
    # ---------------------------------------------------------
    cell_records = []
    with open(LOCAL_MR_OUTPUT, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if parts[0] == "CELL":
                cell_id = int(parts[1])
                rec_cnt = int(parts[2])
                tot_traffic = float(parts[18])
                internet = float(parts[15])
                cell_records.append({
                    "cell_id": cell_id,
                    "record_count": rec_cnt,
                    "total_traffic": tot_traffic,
                    "internet": internet
                })

    cell_traffics = [c["total_traffic"] for c in cell_records]
    med_cell = compute_median(cell_traffics)
    mad_cell = compute_mad(cell_traffics, med_cell)
    if mad_cell == 0:
        mad_cell = 1.0

    # Sort cells by traffic desc
    cell_records.sort(key=lambda x: x["total_traffic"], reverse=True)
    p995_threshold = cell_records[int(len(cell_records) * 0.005)]["total_traffic"]

    cell_anomalies = []
    for c in cell_records:
        if c["total_traffic"] >= p995_threshold:
            mod_z = 0.6745 * (c["total_traffic"] - med_cell) / mad_cell
            ratio_to_median = c["total_traffic"] / med_cell if med_cell > 0 else 0
            severity = "CRITICAL" if ratio_to_median >= 25.0 else ("HIGH" if ratio_to_median >= 15.0 else "MODERATE")

            cell_anomalies.append({
                "type": "CELL_TRAFFIC_HOTSPOT",
                "cell_id": c["cell_id"],
                "observed_value": round(c["total_traffic"], 2),
                "baseline_median": round(med_cell, 2),
                "ratio_to_median": round(ratio_to_median, 2),
                "deviation_score": round(mod_z, 3),
                "internet_share_pct": round((c["internet"] / c["total_traffic"]) * 100, 2) if c["total_traffic"] > 0 else 0,
                "severity": severity,
                "explanation": f"Cell {c['cell_id']} generated {c['total_traffic']:,.2f} total traffic, which is {ratio_to_median:.1f}x the metropolitan median ({med_cell:,.2f}). High-density commercial/transit cluster."
            })

    # Summary Anomaly Report Payload
    anomaly_report = {
        "metadata": {
            "project": "Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce",
            "phase": "Phase 6: Network Performance Monitoring & CDR Anomaly Detection",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "methodology": "Robust Non-Parametric Median & MAD Anomaly Scoring (Modified Z-score)",
            "disclaimer": "All detected anomalies represent empirical statistical deviations in CDR traffic volume and do not indicate confirmed physical equipment outages or network hardware failures."
        },
        "summary_counts": {
            "temporal_surges_detected": len(temporal_anomalies),
            "rate_of_change_spikes_detected": len(delta_spikes),
            "cell_hotspot_anomalies_detected": len(cell_anomalies),
            "total_anomalies_flagged": len(temporal_anomalies) + len(delta_spikes) + len(cell_anomalies)
        },
        "baselines": {
            "temporal_traffic": {
                "median_per_10min_interval": round(med_traffic, 2),
                "mad_per_10min_interval": round(mad_traffic, 2),
                "average_per_10min_interval": round(sum(traffic_vals) / len(traffic_vals), 2)
            },
            "cell_traffic": {
                "median_per_cell": round(med_cell, 2),
                "mad_per_cell": round(mad_cell, 2),
                "p99_5_threshold": round(p995_threshold, 2)
            }
        },
        "temporal_surge_anomalies": temporal_anomalies,
        "rate_of_change_spike_anomalies": delta_spikes,
        "cell_hotspot_anomalies": cell_anomalies[:50]
    }

    report_path = os.path.join(REPORTS_DIR, "anomaly_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(anomaly_report, f, indent=2)
    print(f"Saved Anomaly Report to: {report_path}")

    # Upload to HDFS
    print("Uploading anomaly report to HDFS...")
    run_wsl(f"/opt/hadoop/bin/hdfs dfs -mkdir -p {HDFS_ANOMALIES_DIR}")
    run_wsl(f"/opt/hadoop/bin/hdfs dfs -put -f /mnt/c/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/reports/anomaly_report.json {HDFS_ANOMALIES_DIR}/anomaly_report.json")
    print(f"Detected {anomaly_report['summary_counts']['total_anomalies_flagged']} total explainable anomalies across intervals and cell towers.")

if __name__ == "__main__":
    main()
