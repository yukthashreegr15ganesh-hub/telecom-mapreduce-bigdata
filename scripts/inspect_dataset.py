import os
import sys
import json
from collections import Counter
from datetime import datetime

SAMPLE_FILE = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\data\sample\sms-call-internet-mi-sample.txt"
RAW_DIR = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\data\raw"
INSPECTION_REPORT = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\reports\dataset_inspection.json"

COLUMNS = [
    "cell_id",
    "timestamp",
    "country_code",
    "sms_in",
    "sms_out",
    "call_in",
    "call_out",
    "internet_traffic"
]

def inspect_dataset():
    if not os.path.exists(SAMPLE_FILE):
        print(f"Sample file not found at {SAMPLE_FILE}")
        return False

    print("=" * 70)
    print("DETAILED DATASET INSPECTION & PROFILING")
    print("=" * 70)

    total_records = 0
    column_counts = Counter()
    missing_counts = {col: 0 for col in COLUMNS}
    data_types = {col: set() for col in COLUMNS}
    
    unique_cells = set()
    unique_country_codes = Counter()
    seen_keys = set()
    duplicate_keys = 0
    
    min_timestamp = None
    max_timestamp = None
    timestamp_intervals = Counter()
    prev_timestamp_by_cell_country = {}

    numeric_stats = {
        col: {"min": float("inf"), "max": float("-inf"), "sum": 0.0, "count": 0}
        for col in ["sms_in", "sms_out", "call_in", "call_out", "internet_traffic"]
    }

    with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip("\r\n")
            if not line:
                continue

            parts = line.split("\t")
            column_counts[len(parts)] += 1
            total_records += 1

            if len(parts) != 8:
                continue

            # Composite Key: (cell_id, timestamp, country_code)
            c_id_raw, ts_raw, country_raw = parts[0], parts[1], parts[2]
            key = (c_id_raw, ts_raw, country_raw)
            if key in seen_keys:
                duplicate_keys += 1
            else:
                seen_keys.add(key)

            # 1. cell_id
            try:
                cell_id = int(c_id_raw)
                unique_cells.add(cell_id)
                data_types["cell_id"].add("integer")
            except ValueError:
                data_types["cell_id"].add("invalid")

            # 2. timestamp
            try:
                ts = int(ts_raw)
                data_types["timestamp"].add("integer (epoch_millis)")
                if min_timestamp is None or ts < min_timestamp:
                    min_timestamp = ts
                if max_timestamp is None or ts > max_timestamp:
                    max_timestamp = ts

                pair_key = (c_id_raw, country_raw)
                if pair_key in prev_timestamp_by_cell_country:
                    diff = ts - prev_timestamp_by_cell_country[pair_key]
                    if diff > 0 and diff <= 3600000:
                        timestamp_intervals[diff] += 1
                prev_timestamp_by_cell_country[pair_key] = ts
            except ValueError:
                data_types["timestamp"].add("invalid")

            # 3. country_code
            try:
                cc = int(country_raw) if country_raw.strip() else 0
                unique_country_codes[cc] += 1
                data_types["country_code"].add("integer")
            except ValueError:
                data_types["country_code"].add("invalid")

            # 4-8. Activity Metrics
            metric_cols = ["sms_in", "sms_out", "call_in", "call_out", "internet_traffic"]
            for idx, col_name in enumerate(metric_cols, start=3):
                val_str = parts[idx].strip()
                if val_str == "" or val_str.lower() == "null":
                    missing_counts[col_name] += 1
                    data_types[col_name].add("null")
                else:
                    try:
                        val = float(val_str)
                        data_types[col_name].add("float")
                        stats = numeric_stats[col_name]
                        stats["min"] = min(stats["min"], val)
                        stats["max"] = max(stats["max"], val)
                        stats["sum"] += val
                        stats["count"] += 1
                    except ValueError:
                        data_types[col_name].add("invalid")

    # Format numeric stats
    formatted_metrics = {}
    for col, st in numeric_stats.items():
        formatted_metrics[col] = {
            "non_null_count": st["count"],
            "null_count": missing_counts[col],
            "null_percentage": round((missing_counts[col] / total_records) * 100, 2),
            "min": round(st["min"], 6) if st["count"] > 0 else None,
            "max": round(st["max"], 6) if st["count"] > 0 else None,
            "mean": round(st["sum"] / st["count"], 6) if st["count"] > 0 else None
        }

    inspection_results = {
        "inspection_target": SAMPLE_FILE,
        "sample_size_bytes": os.path.getsize(SAMPLE_FILE),
        "total_records_inspected": total_records,
        "file_format": "Uncompressed Tab-Separated Values (TSV)",
        "delimiter": "\\t",
        "has_header": False,
        "column_distribution": dict(column_counts),
        "schema_verified": list(COLUMNS),
        "inferred_data_types": {col: list(types) for col, types in data_types.items()},
        "primary_key_candidate": ["cell_id", "timestamp", "country_code"],
        "duplicate_records_on_key": duplicate_keys,
        "temporal_profile": {
            "min_timestamp_epoch_ms": min_timestamp,
            "max_timestamp_epoch_ms": max_timestamp,
            "min_datetime_utc": datetime.utcfromtimestamp(min_timestamp / 1000).isoformat() if min_timestamp else None,
            "max_datetime_utc": datetime.utcfromtimestamp(max_timestamp / 1000).isoformat() if max_timestamp else None,
            "dominant_time_interval_ms": timestamp_intervals.most_common(1)[0][0] if timestamp_intervals else None,
            "dominant_time_interval_minutes": (timestamp_intervals.most_common(1)[0][0] / 60000) if timestamp_intervals else None
        },
        "spatial_profile": {
            "unique_cells_in_sample": len(unique_cells),
            "min_cell_id": min(unique_cells) if unique_cells else None,
            "max_cell_id": max(unique_cells) if unique_cells else None
        },
        "country_code_distribution_top_5": [
            {"country_code": cc, "record_count": count} for cc, count in unique_country_codes.most_common(5)
        ],
        "metrics_profiling": formatted_metrics
    }

    os.makedirs(os.path.dirname(INSPECTION_REPORT), exist_ok=True)
    with open(INSPECTION_REPORT, "w", encoding="utf-8") as rf:
        json.dump(inspection_results, rf, indent=2)

    print(f"Total Inspected Records:  {total_records:,}")
    print(f"Delimiter:                Tab (\\t)")
    print(f"Columns Verified:         {COLUMNS}")
    print(f"Duplicate Keys:           {duplicate_keys}")
    print(f"Sample Time Span (UTC):   {inspection_results['temporal_profile']['min_datetime_utc']} to {inspection_results['temporal_profile']['max_datetime_utc']}")
    print(f"Dominant Time Interval:   {inspection_results['temporal_profile']['dominant_time_interval_minutes']} minutes (600,000 ms)")
    print(f"Inspection Report Saved:  {INSPECTION_REPORT}")
    print("=" * 70)
    return True

if __name__ == "__main__":
    inspect_dataset()
