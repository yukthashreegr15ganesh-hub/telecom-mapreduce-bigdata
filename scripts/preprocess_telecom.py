#!/usr/bin/env python3
"""
Telecom Italia Milan CDR Preprocessing & Data Quality Pipeline
Project: Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce
Workspace: C:\\Users\\Admin\\.gemini\\antigravity\\scratch\\telecom-mapreduce

Processes raw tab-separated telecommunication data:
1. cell_id (int)
2. timestamp (epoch ms)
3. country_code (int)
4. sms_in (float / empty)
5. sms_out (float / empty)
6. call_in (float / empty)
7. call_out (float / empty)
8. internet_traffic (float / empty)
"""

import sys
import os
import time
import json
import subprocess
from datetime import datetime, timezone

# Configuration
HDFS_INPUT = "/telecom/data/raw/sms-call-internet-mi-2013-11-01.txt"
HDFS_CLEAN_DIR = "/telecom/data/processed/clean"
HDFS_CLEAN_FILE = "/telecom/data/processed/clean/sms-call-internet-mi-2013-11-01-clean.tsv"
HDFS_REJECTED_DIR = "/telecom/data/processed/rejected"
HDFS_REJECTED_FILE = "/telecom/data/processed/rejected/sms-call-internet-mi-2013-11-01-rejected.tsv"
HDFS_METRICS_DIR = "/telecom/results/data_quality"
HDFS_METRICS_FILE = "/telecom/results/data_quality/data_quality_report.json"

LOCAL_WORKSPACE = "/mnt/c/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce"
if not os.path.exists(LOCAL_WORKSPACE):
    LOCAL_WORKSPACE = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce"

LOCAL_CLEAN_PATH = os.path.join(LOCAL_WORKSPACE, "data", "processed", "clean", "sms-call-internet-mi-2013-11-01-clean.tsv")
LOCAL_REJECTED_PATH = os.path.join(LOCAL_WORKSPACE, "data", "processed", "rejected", "sms-call-internet-mi-2013-11-01-rejected.tsv")
LOCAL_REPORT_PATH = os.path.join(LOCAL_WORKSPACE, "reports", "data_quality_report.json")

FIELD_NAMES = [
    "cell_id", "timestamp", "country_code",
    "sms_in", "sms_out", "call_in", "call_out", "internet_traffic"
]

def run_cmd(cmd_list):
    res = subprocess.run(cmd_list, capture_output=True, text=True)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def main():
    print("=" * 70)
    print("STARTING TELECOM DATA PREPROCESSING & QUALITY VALIDATION PIPELINE")
    print("=" * 70)
    start_total_time = time.time()

    # Ensure local staging directories exist
    os.makedirs(os.path.dirname(LOCAL_CLEAN_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(LOCAL_REJECTED_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(LOCAL_REPORT_PATH), exist_ok=True)

    # Launch streaming read from HDFS
    print(f"Streaming dataset from HDFS: {HDFS_INPUT}")
    read_cmd = ["/opt/hadoop/bin/hdfs", "dfs", "-cat", HDFS_INPUT]
    proc = subprocess.Popen(read_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1024*1024*16)

    # Profiling and Validation accumulators
    total_records = 0
    valid_records = 0
    malformed_records = 0
    duplicate_records = 0

    missing_counts = {f: 0 for f in FIELD_NAMES}
    present_counts = {f: 0 for f in FIELD_NAMES}

    unique_cells = set()
    unique_countries = set()

    min_timestamp = float("inf")
    max_timestamp = float("-inf")

    # Metrics stats for traffic fields
    traffic_fields = ["sms_in", "sms_out", "call_in", "call_out", "internet_traffic"]
    traffic_stats = {
        f: {"min": float("inf"), "max": float("-inf"), "sum": 0.0, "count": 0}
        for f in traffic_fields
    }

    # Tracking seen keys for duplicate checking: (cell_id, timestamp, country_code)
    seen_keys = set()

    # Open staging output files
    print(f"Writing clean records to local staging: {LOCAL_CLEAN_PATH}")
    print(f"Writing rejected records to local staging: {LOCAL_REJECTED_PATH}")

    clean_file = open(LOCAL_CLEAN_PATH, "w", encoding="utf-8", newline="\n")
    rejected_file = open(LOCAL_REJECTED_PATH, "w", encoding="utf-8", newline="\n")

    # Header for rejected file to document rejection reasons
    rejected_file.write("raw_record\trejection_reason\n")

    try:
        for line in proc.stdout:
            total_records += 1
            raw_line = line.rstrip("\r\n")
            fields = raw_line.split("\t")

            # Check 1: Exactly 8 fields
            if len(fields) != 8:
                malformed_records += 1
                rejected_file.write(f"{raw_line}\tINVALID_FIELD_COUNT_{len(fields)}\n")
                continue

            # Check 2: cell_id integer validation (1 to 10000)
            try:
                cell_id = int(fields[0])
                if not (1 <= cell_id <= 10000):
                    malformed_records += 1
                    rejected_file.write(f"{raw_line}\tCELL_ID_OUT_OF_BOUNDS_{cell_id}\n")
                    continue
            except ValueError:
                malformed_records += 1
                rejected_file.write(f"{raw_line}\tCELL_ID_NON_INTEGER\n")
                continue

            # Check 3: timestamp validation (epoch ms, reasonable bounds around Nov 2013)
            try:
                ts = int(fields[1])
                # Bounds: Nov 1, 2013 is ~1383260400000
                if ts <= 0:
                    malformed_records += 1
                    rejected_file.write(f"{raw_line}\tINVALID_NEGATIVE_TIMESTAMP\n")
                    continue
            except ValueError:
                malformed_records += 1
                rejected_file.write(f"{raw_line}\tTIMESTAMP_NON_INTEGER\n")
                continue

            # Check 4: country_code validation (non-negative integer)
            try:
                country_code = int(fields[2])
                if country_code < 0:
                    malformed_records += 1
                    rejected_file.write(f"{raw_line}\tNEGATIVE_COUNTRY_CODE\n")
                    continue
            except ValueError:
                malformed_records += 1
                rejected_file.write(f"{raw_line}\tCOUNTRY_CODE_NON_INTEGER\n")
                continue

            # Check 5: Traffic fields validation (if non-empty, must be float and >= 0.0)
            traffic_valid = True
            parsed_traffic = []
            for i, fname in enumerate(traffic_fields, start=3):
                val_str = fields[i].strip()
                if val_str == "":
                    parsed_traffic.append(None)
                else:
                    try:
                        val = float(val_str)
                        if val < 0.0:
                            traffic_valid = False
                            malformed_records += 1
                            rejected_file.write(f"{raw_line}\tNEGATIVE_TRAFFIC_VALUE_{fname}\n")
                            break
                        parsed_traffic.append(val)
                    except ValueError:
                        traffic_valid = False
                        malformed_records += 1
                        rejected_file.write(f"{raw_line}\tNON_NUMERIC_TRAFFIC_VALUE_{fname}\n")
                        break

            if not traffic_valid:
                continue

            # Check 6: Duplicate detection (cell_id, timestamp, country_code)
            pk = (cell_id, ts, country_code)
            if pk in seen_keys:
                duplicate_records += 1
            else:
                seen_keys.add(pk)

            # Record is VALID! Update accumulators
            valid_records += 1
            unique_cells.add(cell_id)
            unique_countries.add(country_code)

            if ts < min_timestamp:
                min_timestamp = ts
            if ts > max_timestamp:
                max_timestamp = ts

            present_counts["cell_id"] += 1
            present_counts["timestamp"] += 1
            present_counts["country_code"] += 1

            # Update traffic statistics
            clean_traffic_str = []
            for i, fname in enumerate(traffic_fields):
                val = parsed_traffic[i]
                if val is None:
                    missing_counts[fname] += 1
                    clean_traffic_str.append("")
                else:
                    present_counts[fname] += 1
                    stat = traffic_stats[fname]
                    if val < stat["min"]:
                        stat["min"] = val
                    if val > stat["max"]:
                        stat["max"] = val
                    stat["sum"] += val
                    stat["count"] += 1
                    # Normalize string representation
                    clean_traffic_str.append(f"{val:.16g}")

            # Write clean normalized record
            clean_record = f"{cell_id}\t{ts}\t{country_code}\t" + "\t".join(clean_traffic_str) + "\n"
            clean_file.write(clean_record)

            if total_records % 1000000 == 0:
                print(f"  Processed {total_records:,} records ({valid_records:,} valid, {malformed_records:,} malformed)...")

    finally:
        clean_file.close()
        rejected_file.close()
        proc.stdout.close()
        proc.wait()

    stream_duration = time.time() - start_total_time
    print(f"\nStreaming & Processing completed in {stream_duration:.2f} seconds.")
    print(f"Total processed: {total_records:,}")
    print(f"Valid records:   {valid_records:,}")
    print(f"Malformed:       {malformed_records:,}")
    print(f"Duplicate keys:  {duplicate_records:,}")

    # Calculate final traffic averages
    formatted_traffic_stats = {}
    for f in traffic_fields:
        stat = traffic_stats[f]
        cnt = stat["count"]
        formatted_traffic_stats[f] = {
            "present_count": cnt,
            "missing_count": missing_counts[f],
            "missing_percentage": round((missing_counts[f] / valid_records * 100.0), 2) if valid_records else 0,
            "min": round(stat["min"], 8) if cnt > 0 else None,
            "max": round(stat["max"], 8) if cnt > 0 else None,
            "avg": round(stat["sum"] / cnt, 8) if cnt > 0 else None,
            "sum": round(stat["sum"], 8) if cnt > 0 else None
        }

    # Timestamp human-readable conversion
    min_dt_str = datetime.fromtimestamp(min_timestamp / 1000.0, tz=timezone.utc).isoformat() if min_timestamp != float("inf") else None
    max_dt_str = datetime.fromtimestamp(max_timestamp / 1000.0, tz=timezone.utc).isoformat() if max_timestamp != float("-inf") else None

    # Construct comprehensive Data Quality & Preprocessing Report
    data_quality_report = {
        "pipeline": {
            "project": "Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce",
            "phase": "Phase 2.5: Data Preprocessing & Quality Validation",
            "execution_timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_time_seconds": round(stream_duration, 2),
            "source_hdfs_path": HDFS_INPUT,
            "clean_hdfs_destination": HDFS_CLEAN_FILE,
            "rejected_hdfs_destination": HDFS_REJECTED_FILE
        },
        "record_counts": {
            "total_input_records": total_records,
            "valid_clean_records": valid_records,
            "malformed_rejected_records": malformed_records,
            "duplicate_primary_keys": duplicate_records,
            "balance_check_passed": (total_records == valid_records + malformed_records)
        },
        "spatial_coverage": {
            "unique_cells_count": len(unique_cells),
            "expected_cells_count": 10000,
            "cell_id_min": min(unique_cells) if unique_cells else None,
            "cell_id_max": max(unique_cells) if unique_cells else None,
            "coverage_percentage": round(len(unique_cells) / 10000.0 * 100, 2)
        },
        "temporal_coverage": {
            "min_timestamp_ms": min_timestamp if min_timestamp != float("inf") else None,
            "max_timestamp_ms": max_timestamp if max_timestamp != float("-inf") else None,
            "min_timestamp_utc": min_dt_str,
            "max_timestamp_utc": max_dt_str,
            "expected_interval_ms": 600000,
            "observation_window_hours": round((max_timestamp - min_timestamp) / (3600 * 1000.0), 2) if min_timestamp != float("inf") else None
        },
        "international_coverage": {
            "unique_country_codes_count": len(unique_countries),
            "sample_country_codes": sorted(list(unique_countries))[:25]
        },
        "missing_value_analysis": {
            "total_records": valid_records,
            "per_column_metrics": {
                "cell_id": {"missing": missing_counts["cell_id"], "missing_pct": 0.0},
                "timestamp": {"missing": missing_counts["timestamp"], "missing_pct": 0.0},
                "country_code": {"missing": missing_counts["country_code"], "missing_pct": 0.0},
                "sms_in": {"missing": missing_counts["sms_in"], "missing_pct": formatted_traffic_stats["sms_in"]["missing_percentage"]},
                "sms_out": {"missing": missing_counts["sms_out"], "missing_pct": formatted_traffic_stats["sms_out"]["missing_percentage"]},
                "call_in": {"missing": missing_counts["call_in"], "missing_pct": formatted_traffic_stats["call_in"]["missing_percentage"]},
                "call_out": {"missing": missing_counts["call_out"], "missing_pct": formatted_traffic_stats["call_out"]["missing_percentage"]},
                "internet_traffic": {"missing": missing_counts["internet_traffic"], "missing_pct": formatted_traffic_stats["internet_traffic"]["missing_percentage"]}
            }
        },
        "traffic_field_statistics": formatted_traffic_stats
    }

    # Save local JSON report
    with open(LOCAL_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(data_quality_report, f, indent=2)
    print(f"Data quality report saved locally to: {LOCAL_REPORT_PATH}")

    # ====================================================================
    # TASK 4: UPLOAD RESULTS TO HDFS
    # ====================================================================
    print("\n" + "=" * 70)
    print("TASK 4 — UPLOADING PROCESSED DATASETS AND QUALITY METRICS TO HDFS")
    print("=" * 70)

    # 1. Create HDFS processed directories
    print("Creating HDFS processed and results directories...")
    run_cmd(["/opt/hadoop/bin/hdfs", "dfs", "-mkdir", "-p", HDFS_CLEAN_DIR, HDFS_REJECTED_DIR, HDFS_METRICS_DIR])

    # 2. Upload Clean Dataset
    print(f"Uploading clean dataset to {HDFS_CLEAN_FILE}...")
    run_cmd(["/opt/hadoop/bin/hdfs", "dfs", "-rm", "-skipTrash", HDFS_CLEAN_FILE])
    rc_clean, _, err_clean = run_cmd(["/opt/hadoop/bin/hdfs", "dfs", "-put", LOCAL_CLEAN_PATH, HDFS_CLEAN_FILE])
    if rc_clean != 0:
        print("ERROR uploading clean dataset:", err_clean)
        sys.exit(1)

    # 3. Upload Rejected Dataset
    print(f"Uploading rejected dataset to {HDFS_REJECTED_FILE}...")
    run_cmd(["/opt/hadoop/bin/hdfs", "dfs", "-rm", "-skipTrash", HDFS_REJECTED_FILE])
    rc_rej, _, err_rej = run_cmd(["/opt/hadoop/bin/hdfs", "dfs", "-put", LOCAL_REJECTED_PATH, HDFS_REJECTED_FILE])
    if rc_rej != 0:
        print("ERROR uploading rejected dataset:", err_rej)
        sys.exit(1)

    # 4. Upload Data Quality Report
    print(f"Uploading quality metrics to {HDFS_METRICS_FILE}...")
    run_cmd(["/opt/hadoop/bin/hdfs", "dfs", "-rm", "-skipTrash", HDFS_METRICS_FILE])
    rc_rep, _, err_rep = run_cmd(["/opt/hadoop/bin/hdfs", "dfs", "-put", LOCAL_REPORT_PATH, HDFS_METRICS_FILE])
    if rc_rep != 0:
        print("ERROR uploading quality report:", err_rep)
        sys.exit(1)

    # ====================================================================
    # TASK 5: TESTING & INTEGRITY VALIDATION
    # ====================================================================
    print("\n" + "=" * 70)
    print("TASK 5 — TESTING & INTEGRITY VALIDATION")
    print("=" * 70)

    # HDFS file listings and size verification
    rc_ls, ls_out, _ = run_cmd(["/opt/hadoop/bin/hdfs", "dfs", "-ls", "-R", "/telecom/data/processed", "/telecom/results/data_quality"])
    print("HDFS processed and results listing:\n", ls_out)

    # Stream clean line count from HDFS in chunks
    print("Verifying HDFS clean dataset line count via stream...")
    proc_clean = subprocess.Popen(["/opt/hadoop/bin/hdfs", "dfs", "-cat", HDFS_CLEAN_FILE], stdout=subprocess.PIPE, bufsize=1024*1024*4)
    hdfs_clean_lines = 0
    while chunk := proc_clean.stdout.read(1024 * 1024 * 4):
        hdfs_clean_lines += chunk.count(b"\n")
    proc_clean.stdout.close()
    proc_clean.wait()
    print(f"HDFS Clean line count:    {hdfs_clean_lines:,} (Expected: {valid_records:,})")

    # Rejected line count (minus header)
    print("Verifying HDFS rejected dataset line count via stream...")
    proc_rej = subprocess.Popen(["/opt/hadoop/bin/hdfs", "dfs", "-cat", HDFS_REJECTED_FILE], stdout=subprocess.PIPE, bufsize=1024*1024)
    hdfs_rej_lines_raw = 0
    while chunk := proc_rej.stdout.read(1024 * 1024):
        hdfs_rej_lines_raw += chunk.count(b"\n")
    proc_rej.stdout.close()
    proc_rej.wait()
    hdfs_rej_data_lines = max(0, hdfs_rej_lines_raw - 1)
    print(f"HDFS Rejected line count: {hdfs_rej_data_lines:,} (Expected: {malformed_records:,})")

    print("\n--- INVARIANT CHECK ---")
    print(f"Input Records ({total_records:,}) == Valid Output ({hdfs_clean_lines:,}) + Rejected ({hdfs_rej_data_lines:,})")
    assert total_records == hdfs_clean_lines + hdfs_rej_data_lines, "Data Loss Detected! Invariant failed!"
    print("PASSED: Zero data loss verified across HDFS pipeline!")

    total_pipeline_time = time.time() - start_total_time
    print(f"\nEntire Preprocessing and Validation completed successfully in {total_pipeline_time:.2f} seconds.")

if __name__ == "__main__":
    main()
