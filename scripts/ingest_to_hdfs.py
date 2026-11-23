import os
import sys
import time
import hashlib
import json
import subprocess
import shutil
from datetime import datetime, timezone

PROJECT_DIR = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce"
SOURCE_FILE = os.path.join(PROJECT_DIR, "data", "raw", "sms-call-internet-mi-2013-11-01.txt")
WSL_SOURCE_PATH = "/mnt/c/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/data/raw/sms-call-internet-mi-2013-11-01.txt"
HDFS_TARGET_DIR = "/telecom/data/raw"
HDFS_TARGET_FILE = "/telecom/data/raw/sms-call-internet-mi-2013-11-01.txt"
EXPECTED_SIZE = 322874887
EXPECTED_MD5 = "658c49f8e3c7910bd3bb2bafbf62cdce"
EXPECTED_RECORDS = 4842625

def run_wsl(bash_cmd):
    p = subprocess.run(
        ["wsl.exe", "-d", "Ubuntu", "-u", "dminmlops", "-e", "bash", "-c", f"source /etc/profile; {bash_cmd}"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def run_wsl_stream_md5(bash_cmd):
    p = subprocess.run(
        ["wsl.exe", "-d", "Ubuntu", "-u", "dminmlops", "-e", "bash", "-c", f"source /etc/profile; {bash_cmd}"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def calculate_local_md5(filepath):
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024 * 8):
            hasher.update(chunk)
    return hasher.hexdigest()

def main():
    print("=" * 60)
    print("TASK 1 — PREFLIGHT CHECKS")
    print("=" * 60)

    # 1.1 Local Source File Exists & Size
    if not os.path.exists(SOURCE_FILE):
        print(f"ERROR: Source file does not exist at {SOURCE_FILE}")
        sys.exit(1)

    actual_local_size = os.path.getsize(SOURCE_FILE)
    print(f"Local file size: {actual_local_size} bytes (Expected: {EXPECTED_SIZE})")
    if actual_local_size != EXPECTED_SIZE:
        print("ERROR: File size mismatch!")
        sys.exit(1)

    # 1.2 Local MD5 calculation
    print("Calculating local MD5 checksum...")
    actual_local_md5 = calculate_local_md5(SOURCE_FILE)
    print(f"Local MD5: {actual_local_md5} (Expected: {EXPECTED_MD5})")
    if actual_local_md5.lower() != EXPECTED_MD5.lower():
        print("ERROR: Local MD5 checksum mismatch!")
        sys.exit(1)

    # 1.3 Available Storage Checks
    # Windows C: drive
    total_c, used_c, free_c = shutil.disk_usage("C:\\")
    free_c_gb = free_c / (1024**3)
    print(f"Windows C: free storage: {free_c_gb:.2f} GB")

    # WSL root filesystem
    rc, df_out, _ = run_wsl("df -B1 / | tail -n 1")
    df_parts = df_out.split()
    wsl_avail_bytes = int(df_parts[3]) if len(df_parts) >= 4 else 0
    wsl_avail_gb = wsl_avail_bytes / (1024**3)
    print(f"WSL root filesystem free: {wsl_avail_gb:.2f} GB ({wsl_avail_bytes} bytes)")

    # 1.4 HDFS Health
    rc, jps_out, _ = run_wsl("jps")
    if "NameNode" not in jps_out or "DataNode" not in jps_out:
        print("Starting HDFS services via systemctl...")
        subprocess.run(["wsl.exe", "-d", "Ubuntu", "-u", "root", "-e", "systemctl", "start", "hadoop-namenode", "hadoop-datanode"], check=True)
        time.sleep(5)
        rc, jps_out, _ = run_wsl("jps")
    
    print("Running JPS:\n", jps_out)
    if "NameNode" not in jps_out or "DataNode" not in jps_out:
        print("ERROR: HDFS NameNode or DataNode is not running!")
        sys.exit(1)

    rc, dfs_report, _ = run_wsl("/opt/hadoop/bin/hdfs dfsadmin -report")
    print("HDFS cluster summary:\n", dfs_report.split("Live datanodes")[0].strip())

    if free_c_gb < 1.0:
        print("ERROR: Insufficient host disk space!")
        sys.exit(1)

    print("Preflight check passed successfully.\n")

    print("=" * 60)
    print("TASK 2 — INGESTION TO HDFS")
    print("=" * 60)
    # Check if target already exists in HDFS; if so check if re-upload is needed
    rc, check_exist, _ = run_wsl(f"/opt/hadoop/bin/hdfs dfs -test -e {HDFS_TARGET_FILE}")
    if rc == 0:
        print(f"Target {HDFS_TARGET_FILE} already exists. Removing prior partial copy...")
        run_wsl(f"/opt/hadoop/bin/hdfs dfs -rm -skipTrash {HDFS_TARGET_FILE}")

    print(f"Uploading {WSL_SOURCE_PATH} -> {HDFS_TARGET_FILE}...")
    start_time = time.time()
    
    upload_cmd = f"/opt/hadoop/bin/hdfs dfs -put {WSL_SOURCE_PATH} {HDFS_TARGET_FILE}"
    rc_put, put_out, put_err = run_wsl(upload_cmd)
    end_time = time.time()
    
    duration = end_time - start_time
    throughput_mb_s = (actual_local_size / (1024 * 1024)) / duration if duration > 0 else 0
    
    print(f"Upload completed in {duration:.2f} seconds ({throughput_mb_s:.2f} MB/s). Return code: {rc_put}")
    if rc_put != 0:
        print("ERROR: Ingestion failed!")
        print("STDERR:", put_err)
        sys.exit(1)

    print("=" * 60)
    print("TASK 3 — DATA INTEGRITY VERIFICATION")
    print("=" * 60)

    # 3.1 Verify existence and exact size in HDFS
    rc, ls_stat, _ = run_wsl(f"/opt/hadoop/bin/hdfs dfs -ls {HDFS_TARGET_FILE}")
    print("HDFS ls output:\n", ls_stat)
    
    # Parse ls output: permissions, repl, owner, group, size, date, time, path
    ls_tokens = ls_stat.split()
    hdfs_replication = int(ls_tokens[1])
    hdfs_size = int(ls_tokens[4])
    print(f"HDFS file size: {hdfs_size} bytes (Replication: {hdfs_replication})")
    
    if hdfs_size != EXPECTED_SIZE:
        print("ERROR: HDFS file size mismatch!")
        sys.exit(1)
        
    if hdfs_replication != 1:
        print(f"WARNING: Expected replication 1, found {hdfs_replication}")

    # 3.2 HDFS Checksum
    rc, checksum_out, _ = run_wsl(f"/opt/hadoop/bin/hdfs dfs -checksum {HDFS_TARGET_FILE}")
    print("HDFS Checksum:\n", checksum_out)

    # 3.3 Stream file back from HDFS and calculate MD5
    print("Streaming file back from HDFS to calculate round-trip MD5 checksum...")
    rc, hdfs_md5_out, _ = run_wsl(f"/opt/hadoop/bin/hdfs dfs -cat {HDFS_TARGET_FILE} | md5sum")
    hdfs_streamed_md5 = hdfs_md5_out.split()[0].strip()
    print(f"Streamed HDFS MD5: {hdfs_streamed_md5} (Expected: {EXPECTED_MD5})")

    if hdfs_streamed_md5.lower() != EXPECTED_MD5.lower():
        print("ERROR: Streamed HDFS MD5 checksum does not match expected MD5!")
        sys.exit(1)
    print("MD5 integrity independently verified across HDFS stream: MATCH!")

    # 3.4 Efficient record count verification
    print("Verifying record count via streaming line count...")
    rc, wc_out, _ = run_wsl(f"/opt/hadoop/bin/hdfs dfs -cat {HDFS_TARGET_FILE} | wc -l")
    hdfs_record_count = int(wc_out.strip())
    print(f"HDFS Record Count: {hdfs_record_count} (Expected: {EXPECTED_RECORDS})")
    if hdfs_record_count != EXPECTED_RECORDS:
        print("ERROR: Record count mismatch!")
        sys.exit(1)

    print("=" * 60)
    print("TASK 4 & 5 — GENERATE INGESTION REPORT")
    print("=" * 60)
    ingestion_ts = datetime.now(timezone.utc).isoformat()

    report_payload = {
        "project": "Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce",
        "ingestion_status": "SUCCESS",
        "timestamp": ingestion_ts,
        "source_metadata": {
            "filename": "sms-call-internet-mi-2013-11-01.txt",
            "local_path": SOURCE_FILE,
            "wsl_path": WSL_SOURCE_PATH,
            "byte_size": actual_local_size,
            "md5_checksum": actual_local_md5,
            "expected_md5": EXPECTED_MD5,
            "record_count": hdfs_record_count
        },
        "hdfs_metadata": {
            "target_path": HDFS_TARGET_FILE,
            "byte_size": hdfs_size,
            "replication_factor": hdfs_replication,
            "hdfs_checksum_raw": checksum_out,
            "streamed_md5": hdfs_streamed_md5,
            "md5_match": (hdfs_streamed_md5.lower() == EXPECTED_MD5.lower()),
            "size_match": (hdfs_size == EXPECTED_SIZE),
            "record_count_match": (hdfs_record_count == EXPECTED_RECORDS)
        },
        "performance_metrics": {
            "upload_duration_seconds": round(duration, 3),
            "throughput_mb_per_sec": round(throughput_mb_s, 2),
            "transfer_command": upload_cmd
        },
        "storage_capacity_post_ingestion": {
            "windows_free_gb": round(free_c_gb, 2),
            "wsl_free_gb": round(wsl_avail_gb, 2)
        }
    }

    report_file = os.path.join(PROJECT_DIR, "reports", "hdfs_dataset_ingestion.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    print(f"Ingestion report successfully saved to: {report_file}")

if __name__ == "__main__":
    main()
