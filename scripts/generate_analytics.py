#!/usr/bin/env python3
"""
Telecom Traffic Analytics Generator
Project: Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce
Workspace: C:\\Users\\Admin\\.gemini\\antigravity\\scratch\\telecom-mapreduce

Processes MapReduce reduced partitions for:
- CELL (10,000 cells)
- TIME (144 intervals)
- COUNTRY (246 countries)
"""

import os
import sys
import json
import csv
import subprocess
from datetime import datetime, timezone

LOCAL_WORKSPACE = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce"
HDFS_OUTPUT = "/telecom/output/mapreduce/part-00000"
HDFS_RESULTS_DIR = "/telecom/results/analytics"

LOCAL_MR_OUTPUT = os.path.join(LOCAL_WORKSPACE, "data", "processed", "mapreduce", "part-00000")
REPORTS_DIR = os.path.join(LOCAL_WORKSPACE, "reports")

def run_wsl(bash_cmd):
    p = subprocess.run(
        ["wsl.exe", "-d", "Ubuntu", "-u", "dminmlops", "-e", "bash", "-c", f"source /etc/profile; {bash_cmd}"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def calculate_gini(values):
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 0 or sum(sorted_vals) == 0:
        return 0.0
    cum_vals = 0
    total_val = sum(sorted_vals)
    gini_sum = 0
    for i, v in enumerate(sorted_vals, 1):
        cum_vals += v
        gini_sum += (2 * i - n - 1) * v
    return round(gini_sum / (n * total_val), 4)

def main():
    print("=" * 70)
    print("PHASE 5: TELECOM TRAFFIC ANALYTICS GENERATION")
    print("=" * 70)

    # 1. Fetch MapReduce output from HDFS to local staging
    os.makedirs(os.path.dirname(LOCAL_MR_OUTPUT), exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    print("Fetching MapReduce part-00000 from HDFS...")
    run_wsl(f"/opt/hadoop/bin/hdfs dfs -get -f {HDFS_OUTPUT} /mnt/c/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/data/processed/mapreduce/part-00000")

    if not os.path.exists(LOCAL_MR_OUTPUT):
        print("ERROR: Failed to copy MapReduce output locally!")
        sys.exit(1)

    cells = []
    times = []
    countries = []

    with open(LOCAL_MR_OUTPUT, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 19:
                continue

            gtype = parts[0]
            gid = parts[1]
            rec_cnt = int(parts[2])
            sms_in = float(parts[3])
            sms_in_cnt = int(parts[4])
            sms_out = float(parts[6])
            sms_out_cnt = int(parts[7])
            call_in = float(parts[9])
            call_in_cnt = int(parts[10])
            call_out = float(parts[12])
            call_out_cnt = int(parts[13])
            internet = float(parts[15])
            internet_cnt = int(parts[16])
            total_traffic = float(parts[18])

            item = {
                "id": gid,
                "record_count": rec_cnt,
                "sms_in": sms_in,
                "sms_in_cnt": sms_in_cnt,
                "sms_out": sms_out,
                "sms_out_cnt": sms_out_cnt,
                "call_in": call_in,
                "call_in_cnt": call_in_cnt,
                "call_out": call_out,
                "call_out_cnt": call_out_cnt,
                "internet": internet,
                "internet_cnt": internet_cnt,
                "total_traffic": total_traffic
            }

            if gtype == "CELL":
                item["cell_id"] = int(gid)
                cells.append(item)
            elif gtype == "TIME":
                item["timestamp"] = int(gid)
                item["time_utc"] = datetime.fromtimestamp(int(gid)/1000.0, tz=timezone.utc).isoformat()
                times.append(item)
            elif gtype == "COUNTRY":
                item["country_code"] = int(gid)
                countries.append(item)

    print(f"Loaded {len(cells):,} cells, {len(times):,} time intervals, {len(countries):,} country codes.")

    # 1. Top 20 Cells by Total Traffic
    top20_cells_total = sorted(cells, key=lambda x: x["total_traffic"], reverse=True)[:20]

    # 2. Top 20 Cells by Internet Traffic
    top20_cells_internet = sorted(cells, key=lambda x: x["internet"], reverse=True)[:20]

    # 3. Top 20 Countries by Total Traffic
    top20_countries = sorted(countries, key=lambda x: x["total_traffic"], reverse=True)[:20]

    # 4 & 5. SMS and Call Inbound vs Outbound
    total_sms_in = sum(c["sms_in"] for c in times)
    total_sms_out = sum(c["sms_out"] for c in times)
    total_call_in = sum(c["call_in"] for c in times)
    total_call_out = sum(c["call_out"] for c in times)
    total_internet = sum(c["internet"] for c in times)
    total_overall = sum(c["total_traffic"] for c in times)

    # 7. Chronological Time Intervals
    times_sorted = sorted(times, key=lambda x: x["timestamp"])
    for idx, t in enumerate(times_sorted):
        t["slot_index"] = idx

    # 8 & 9. Peak and Lowest Traffic Interval
    peak_interval = max(times, key=lambda x: x["total_traffic"])
    lowest_interval = min(times, key=lambda x: x["total_traffic"])

    # 10. Traffic Concentration Across Cells
    cell_traffics = sorted([c["total_traffic"] for c in cells], reverse=True)
    total_cell_traffic = sum(cell_traffics)
    n_cells = len(cell_traffics)

    top_1_pct_count = int(n_cells * 0.01)
    top_5_pct_count = int(n_cells * 0.05)
    top_10_pct_count = int(n_cells * 0.10)
    top_20_pct_count = int(n_cells * 0.20)

    top_1_pct_share = round((sum(cell_traffics[:top_1_pct_count]) / total_cell_traffic) * 100, 2)
    top_5_pct_share = round((sum(cell_traffics[:top_5_pct_count]) / total_cell_traffic) * 100, 2)
    top_10_pct_share = round((sum(cell_traffics[:top_10_pct_count]) / total_cell_traffic) * 100, 2)
    pareto_80_20_share = round((sum(cell_traffics[:top_20_pct_count]) / total_cell_traffic) * 100, 2)
    gini_coeff = calculate_gini(cell_traffics)

    analytics_data = {
        "metadata": {
            "project": "Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce",
            "source": "MapReduce Output /telecom/output/mapreduce/part-00000",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_records_profiled": sum(c["record_count"] for c in times)
        },
        "executive_traffic_totals": {
            "total_network_traffic": round(total_overall, 2),
            "total_internet_traffic": round(total_internet, 2),
            "internet_traffic_percentage": round((total_internet / total_overall) * 100, 2),
            "sms_metrics": {
                "inbound_sms": round(total_sms_in, 2),
                "outbound_sms": round(total_sms_out, 2),
                "total_sms": round(total_sms_in + total_sms_out, 2),
                "inbound_to_outbound_ratio": round(total_sms_in / total_sms_out, 4) if total_sms_out > 0 else 0
            },
            "call_metrics": {
                "inbound_calls": round(total_call_in, 2),
                "outbound_calls": round(total_call_out, 2),
                "total_calls": round(total_call_in + total_call_out, 2),
                "inbound_to_outbound_ratio": round(total_call_in / total_call_out, 4) if total_call_out > 0 else 0
            }
        },
        "traffic_concentration": {
            "gini_coefficient": gini_coeff,
            "top_1_percent_cells_share_pct": top_1_pct_share,
            "top_5_percent_cells_share_pct": top_5_pct_share,
            "top_10_percent_cells_share_pct": top_10_pct_share,
            "pareto_top_20_percent_cells_share_pct": pareto_80_20_share,
            "interpretation": f"High spatial concentration: top 20% of cells handle {pareto_80_20_share}% of metropolitan traffic (Gini: {gini_coeff})."
        },
        "extreme_traffic_intervals": {
            "peak_interval": {
                "timestamp": peak_interval["timestamp"],
                "time_utc": peak_interval["time_utc"],
                "total_traffic": round(peak_interval["total_traffic"], 2),
                "internet_traffic": round(peak_interval["internet"], 2),
                "records": peak_interval["record_count"]
            },
            "lowest_interval": {
                "timestamp": lowest_interval["timestamp"],
                "time_utc": lowest_interval["time_utc"],
                "total_traffic": round(lowest_interval["total_traffic"], 2),
                "internet_traffic": round(lowest_interval["internet"], 2),
                "records": lowest_interval["record_count"]
            }
        },
        "top_20_cells_by_total_traffic": [
            {
                "rank": i + 1,
                "cell_id": c["cell_id"],
                "total_traffic": round(c["total_traffic"], 2),
                "internet": round(c["internet"], 2),
                "sms_total": round(c["sms_in"] + c["sms_out"], 2),
                "calls_total": round(c["call_in"] + c["call_out"], 2),
                "record_count": c["record_count"]
            } for i, c in enumerate(top20_cells_total)
        ],
        "top_20_cells_by_internet_traffic": [
            {
                "rank": i + 1,
                "cell_id": c["cell_id"],
                "internet_traffic": round(c["internet"], 2),
                "total_traffic": round(c["total_traffic"], 2),
                "record_count": c["record_count"]
            } for i, c in enumerate(top20_cells_internet)
        ],
        "top_20_countries_by_traffic": [
            {
                "rank": i + 1,
                "country_code": c["country_code"],
                "total_traffic": round(c["total_traffic"], 2),
                "internet": round(c["internet"], 2),
                "sms": round(c["sms_in"] + c["sms_out"], 2),
                "calls": round(c["call_in"] + c["call_out"], 2),
                "record_count": c["record_count"]
            } for i, c in enumerate(top20_countries)
        ],
        "temporal_distribution": [
            {
                "slot_index": t["slot_index"],
                "timestamp": t["timestamp"],
                "time_utc": t["time_utc"],
                "total_traffic": round(t["total_traffic"], 2),
                "internet": round(t["internet"], 2),
                "sms": round(t["sms_in"] + t["sms_out"], 2),
                "calls": round(t["call_in"] + t["call_out"], 2),
                "record_count": t["record_count"]
            } for t in times_sorted
        ]
    }

    # Save JSON analytics report
    report_json_path = os.path.join(REPORTS_DIR, "telecom_analytics.json")
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(analytics_data, f, indent=2)
    print(f"Saved: {report_json_path}")

    # Save CSVs
    # 1. Top cells
    top_cells_csv = os.path.join(REPORTS_DIR, "top_20_cells_total_traffic.csv")
    with open(top_cells_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["rank", "cell_id", "total_traffic", "internet", "sms_total", "calls_total", "record_count"])
        writer.writeheader()
        writer.writerows(analytics_data["top_20_cells_by_total_traffic"])

    # 2. Top countries
    top_countries_csv = os.path.join(REPORTS_DIR, "top_20_countries_traffic.csv")
    with open(top_countries_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["rank", "country_code", "total_traffic", "internet", "sms", "calls", "record_count"])
        writer.writeheader()
        writer.writerows(analytics_data["top_20_countries_by_traffic"])

    # 3. Time intervals
    time_csv = os.path.join(REPORTS_DIR, "time_interval_traffic.csv")
    with open(time_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["slot_index", "timestamp", "time_utc", "total_traffic", "internet", "sms", "calls", "record_count"])
        writer.writeheader()
        writer.writerows(analytics_data["temporal_distribution"])

    # Upload to HDFS results
    print("Uploading analytics results to HDFS...")
    run_wsl(f"/opt/hadoop/bin/hdfs dfs -mkdir -p {HDFS_RESULTS_DIR}")
    run_wsl(f"/opt/hadoop/bin/hdfs dfs -put -f /mnt/c/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/reports/telecom_analytics.json {HDFS_RESULTS_DIR}/telecom_analytics.json")
    print("Analytics generation complete!")

if __name__ == "__main__":
    main()
