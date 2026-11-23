import os
import sys
import csv
import json
import hashlib
import time
import argparse
from datetime import datetime

DEFAULT_DATA_DIR = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\data\raw"
DEFAULT_MANIFEST = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\data\metadata\download_manifest.csv"
DEFAULT_REPORT = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\reports\dataset_summary.json"

EXPECTED_COLUMNS = [
    "cell_id",
    "timestamp",
    "country_code",
    "sms_in",
    "sms_out",
    "call_in",
    "call_out",
    "internet_traffic"
]

def compute_md5(filepath):
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()

def validate_dataset(data_dir=DEFAULT_DATA_DIR, manifest_path=DEFAULT_MANIFEST, report_path=DEFAULT_REPORT):
    start_time = time.time()
    print("=" * 70)
    print("TELECOM DATASET INTEGRITY & QUALITY VALIDATION")
    print("=" * 70)
    print(f"Target Directory: {data_dir}")
    print(f"Manifest File:    {manifest_path}")
    print(f"Report Output:    {report_path}")
    print("-" * 70)

    # 1. Load manifest checksums if available
    manifest_info = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                manifest_info[row["filename"]] = {
                    "expected_md5": row.get("md5_checksum", ""),
                    "expected_bytes": int(row.get("filesize_bytes", 0)),
                    "file_id": row.get("file_id", ""),
                    "activity_date": row.get("activity_date", "")
                }
        print(f"Loaded {len(manifest_info)} reference files from manifest.")
    else:
        print("Warning: Manifest file not found. Proceeding without official checksum verification.")

    # 2. Identify all files in raw data directory
    if not os.path.exists(data_dir):
        print(f"Error: Raw data directory {data_dir} does not exist.")
        return False

    raw_files = [f for f in os.listdir(data_dir) if not f.endswith(".part") and not f.endswith(".tmp")]
    raw_files.sort()

    print(f"Found {len(raw_files)} complete downloaded file(s) in target directory.")
    if not raw_files:
        print("No completed files to validate. Exiting.")
        return False

    file_reports = []
    total_bytes = 0
    total_records = 0
    total_malformed_records = 0
    total_empty_files = 0
    overall_min_timestamp = None
    overall_max_timestamp = None
    all_unique_cells = set()

    for idx, fname in enumerate(raw_files, start=1):
        fpath = os.path.join(data_dir, fname)
        fsize = os.path.getsize(fpath)
        total_bytes += fsize

        print(f"\n[{idx}/{len(raw_files)}] Validating: {fname} ({fsize:,} bytes)...")

        # Check for empty file
        if fsize == 0:
            print(f"  [ALERT] Empty file detected: {fname}")
            total_empty_files += 1
            file_reports.append({
                "filename": fname,
                "filesize_bytes": 0,
                "is_empty": True,
                "integrity_status": "EMPTY_FILE",
                "record_count": 0,
                "malformed_count": 0
            })
            continue

        # Checksum Verification
        actual_md5 = compute_md5(fpath)
        expected_meta = manifest_info.get(fname, {})
        expected_md5 = expected_meta.get("expected_md5", "")
        checksum_valid = True
        if expected_md5:
            checksum_valid = (actual_md5.lower() == expected_md5.lower())
            status_str = "MATCH" if checksum_valid else "MISMATCH"
            print(f"  Checksum: MD5={actual_md5} ({status_str})")
        else:
            print(f"  Checksum: MD5={actual_md5} (No reference MD5)")

        # Inspect and validate records
        records_in_file = 0
        malformed_in_file = 0
        file_min_ts = None
        file_max_ts = None
        delimiter_detected = None
        col_count_observed = None

        null_counts = {col: 0 for col in EXPECTED_COLUMNS}
        
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            for line_no, line in enumerate(f, start=1):
                raw_line = line.strip("\r\n")
                if not raw_line:
                    continue

                if delimiter_detected is None:
                    if "\t" in raw_line:
                        delimiter_detected = "\t"
                    elif "," in raw_line:
                        delimiter_detected = ","
                    else:
                        delimiter_detected = " "

                parts = raw_line.split(delimiter_detected)
                
                if col_count_observed is None:
                    col_count_observed = len(parts)

                if len(parts) != len(EXPECTED_COLUMNS):
                    malformed_in_file += 1
                    if malformed_in_file <= 3:
                        print(f"  [Malformed Record L{line_no}]: Expected {len(EXPECTED_COLUMNS)} columns, got {len(parts)} -> {parts[:5]}...")
                    continue

                records_in_file += 1

                # Validate types & range
                try:
                    cell_id = int(parts[0])
                    ts = int(parts[1])
                    if len(all_unique_cells) < 20000:
                        all_unique_cells.add(cell_id)

                    if file_min_ts is None or ts < file_min_ts:
                        file_min_ts = ts
                    if file_max_ts is None or ts > file_max_ts:
                        file_max_ts = ts

                    for col_idx, col_name in enumerate(EXPECTED_COLUMNS):
                        val_str = parts[col_idx].strip()
                        if val_str == "" or val_str.lower() == "null":
                            null_counts[col_name] += 1
                except ValueError:
                    malformed_in_file += 1

        total_records += records_in_file
        total_malformed_records += malformed_in_file

        if file_min_ts and (overall_min_timestamp is None or file_min_ts < overall_min_timestamp):
            overall_min_timestamp = file_min_ts
        if file_max_ts and (overall_max_timestamp is None or file_max_ts > overall_max_timestamp):
            overall_max_timestamp = file_max_ts

        file_reports.append({
            "filename": fname,
            "filesize_bytes": fsize,
            "filesize_mb": round(fsize / (1024 * 1024), 2),
            "md5_actual": actual_md5,
            "md5_expected": expected_md5,
            "md5_verified": checksum_valid,
            "is_empty": False,
            "detected_delimiter": "\\t" if delimiter_detected == "\t" else delimiter_detected,
            "column_count": col_count_observed,
            "records_valid": records_in_file,
            "records_malformed": malformed_in_file,
            "min_timestamp": file_min_ts,
            "max_timestamp": file_max_ts,
            "min_datetime_utc": datetime.utcfromtimestamp(file_min_ts / 1000).isoformat() if file_min_ts else None,
            "max_datetime_utc": datetime.utcfromtimestamp(file_max_ts / 1000).isoformat() if file_max_ts else None,
            "null_values_per_column": null_counts
        })

        print(f"  Valid Records:     {records_in_file:,}")
        print(f"  Malformed Records: {malformed_in_file}")
        if file_min_ts and file_max_ts:
            print(f"  Time Range (UTC):  {datetime.utcfromtimestamp(file_min_ts / 1000)} to {datetime.utcfromtimestamp(file_max_ts / 1000)}")

    # Overall Summary
    validation_duration = round(time.time() - start_time, 2)
    summary_report = {
        "dataset_name": "Telecom Italia Milan Call Detail Records (CDR)",
        "source_doi": "10.7910/DVN/EGZHFV",
        "validation_timestamp_utc": datetime.utcnow().isoformat(),
        "validation_duration_seconds": validation_duration,
        "total_files_analyzed": len(raw_files),
        "total_empty_files": total_empty_files,
        "total_storage_bytes": total_bytes,
        "total_storage_mb": round(total_bytes / (1024 * 1024), 2),
        "total_storage_gb": round(total_bytes / (1024**3), 4),
        "total_valid_records": total_records,
        "total_malformed_records": total_malformed_records,
        "expected_schema": EXPECTED_COLUMNS,
        "temporal_range": {
            "min_timestamp_epoch_ms": overall_min_timestamp,
            "max_timestamp_epoch_ms": overall_max_timestamp,
            "min_datetime_utc": datetime.utcfromtimestamp(overall_min_timestamp / 1000).isoformat() if overall_min_timestamp else None,
            "max_datetime_utc": datetime.utcfromtimestamp(overall_max_timestamp / 1000).isoformat() if overall_max_timestamp else None
        },
        "spatial_coverage": {
            "unique_cells_sampled": len(all_unique_cells),
            "expected_cell_grid_size": 10000
        },
        "files": file_reports
    }

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as rf:
        json.dump(summary_report, rf, indent=2)

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY REPORT COMPLETE")
    print(f"Total Files:       {len(raw_files)}")
    print(f"Total Storage:     {total_bytes:,} bytes ({summary_report['total_storage_mb']} MB)")
    print(f"Total Records:     {total_records:,}")
    print(f"Malformed Records: {total_malformed_records}")
    print(f"Summary JSON:      {report_path}")
    print("=" * 70)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telecom Italia Dataset Validator")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="Path to raw dataset directory")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="Path to manifest CSV")
    parser.add_argument("--report", default=DEFAULT_REPORT, help="Path to output summary JSON")
    args = parser.parse_args()

    validate_dataset(data_dir=args.data_dir, manifest_path=args.manifest, report_path=args.report)
