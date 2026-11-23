#!/usr/bin/env python3
"""
Orchestration Script for Hadoop Streaming MapReduce
Project: Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce
Workspace: C:\\Users\\Admin\\.gemini\\antigravity\\scratch\\telecom-mapreduce
"""

import os
import sys
import time
import json
import re
import subprocess
from datetime import datetime, timezone

HDFS_INPUT = "/telecom/data/processed/clean/sms-call-internet-mi-2013-11-01-clean.tsv"
HDFS_OUTPUT = "/telecom/output/mapreduce"
STREAMING_JAR = "/opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.4.0.jar"

WSL_PROJECT = "/mnt/c/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce"
MAPPER_PATH = f"{WSL_PROJECT}/scripts/mapper.py"
REDUCER_PATH = f"{WSL_PROJECT}/scripts/reducer.py"

LOCAL_WORKSPACE = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce"
REPORT_PATH = os.path.join(LOCAL_WORKSPACE, "reports", "mapreduce_execution_report.json")

def run_wsl(bash_cmd):
    p = subprocess.run(
        ["wsl.exe", "-d", "Ubuntu", "-u", "dminmlops", "-e", "bash", "-c", f"source /etc/profile; {bash_cmd}"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def main():
    print("=" * 70)
    print("PHASE 4: HADOOP STREAMING MAPREDUCE EXECUTION")
    print("=" * 70)

    # 1. Chmod scripts
    run_wsl(f"chmod +x {MAPPER_PATH} {REDUCER_PATH}")

    # 2. Pre-clean output directory in HDFS
    print(f"Cleaning previous HDFS output directory: {HDFS_OUTPUT}")
    run_wsl(f"/opt/hadoop/bin/hdfs dfs -rm -r -skipTrash {HDFS_OUTPUT} 2>/dev/null || true")

    # 3. Build Hadoop Streaming command
    cmd = f"""/opt/hadoop/bin/hadoop jar {STREAMING_JAR} \
-D mapreduce.job.name="Telecom_Traffic_Aggregation_Combined" \
-D mapreduce.map.memory.mb=768 \
-D mapreduce.reduce.memory.mb=768 \
-files {MAPPER_PATH},{REDUCER_PATH} \
-input {HDFS_INPUT} \
-output {HDFS_OUTPUT} \
-mapper "python3 mapper.py" \
-reducer "python3 reducer.py"
"""

    print("Submitting Hadoop Streaming Job...")
    start_time = time.time()
    rc, stdout, stderr = run_wsl(cmd)
    end_time = time.time()

    duration = end_time - start_time
    combined_log = stdout + "\n" + stderr
    print(f"Hadoop Streaming Job finished with exit code {rc} in {duration:.2f} seconds.")

    if rc != 0:
        print("ERROR: Hadoop MapReduce execution failed!")
        print("STDERR:\n", stderr)
        sys.exit(1)

    # 4. Parse Hadoop Job Counters from stdout/stderr
    counters = {}
    counter_pattern = re.compile(r"^\s+([A-Za-z0-9_\s\(\)]+?)=([0-9,]+)$")
    for line in combined_log.splitlines():
        match = counter_pattern.match(line)
        if match:
            k = match.group(1).strip()
            v = int(match.group(2).replace(",", ""))
            counters[k] = v

    # 5. Verify HDFS output files
    rc_ls, ls_out, _ = run_wsl(f"/opt/hadoop/bin/hdfs dfs -ls {HDFS_OUTPUT}")
    print("\nHDFS Output Listing:\n", ls_out)

    # Count output lines in HDFS
    rc_wc, wc_out, _ = run_wsl(f"/opt/hadoop/bin/hdfs dfs -cat {HDFS_OUTPUT}/part-* | wc -l")
    output_records = int(wc_out.strip()) if rc_wc == 0 and wc_out.strip() else 0
    print(f"Total Reduced Keys Emitted: {output_records:,}")

    # Inspect first few lines of output
    rc_head, head_out, _ = run_wsl(f"/opt/hadoop/bin/hdfs dfs -cat {HDFS_OUTPUT}/part-* | head -n 10")
    print("\nSample Output Records (First 10):\n", head_out)

    # Throughput calculation
    input_records = 4842625
    records_per_sec = input_records / duration if duration > 0 else 0

    execution_report = {
        "job_name": "Telecom_Traffic_Aggregation_Combined",
        "framework": "Apache Hadoop 3.4.0 (Streaming)",
        "execution_mode": "Single-Node LocalJobRunner against HDFS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "execution_duration_seconds": round(duration, 2),
        "input_records": input_records,
        "reduced_output_records": output_records,
        "throughput_records_per_sec": round(records_per_sec, 2),
        "hdfs_input_path": HDFS_INPUT,
        "hdfs_output_path": HDFS_OUTPUT,
        "exit_code": rc,
        "job_counters": counters,
        "output_verification": {
            "hdfs_listing": ls_out.splitlines(),
            "sample_records": head_out.splitlines()
        }
    }

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(execution_report, f, indent=2)

    print(f"\nExecution report successfully saved to: {REPORT_PATH}")

if __name__ == "__main__":
    main()
