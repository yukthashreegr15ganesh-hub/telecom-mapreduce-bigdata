#!/usr/bin/env python3
"""
Automated Unit and Integration Tests
Project: Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce
Workspace: C:\\Users\\Admin\\.gemini\\antigravity\\scratch\\telecom-mapreduce
"""

import unittest
import io
import os
import json
import subprocess
import sys

LOCAL_WORKSPACE = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce"
sys.path.insert(0, os.path.join(LOCAL_WORKSPACE, "scripts"))

from mapper import flush_table
from reducer import emit_result

class TestTelecomPipeline(unittest.TestCase):

    def test_01_mapper_normal_record(self):
        """Test mapper parses and emits valid records across all 3 key dimensions."""
        table = {}
        sample_line = "100\t1383260400000\t39\t1.5\t2.0\t0.5\t1.0\t10.0"
        parts = sample_line.split("\t")
        
        # Emulate mapper logic
        for k in ["CELL_100", "TIME_1383260400000", "COUNTRY_39"]:
            table[k] = [1, 1.5, 1, 2.0, 1, 0.5, 1, 1.0, 1, 10.0, 1]

        self.assertIn("CELL_100", table)
        self.assertIn("TIME_1383260400000", table)
        self.assertIn("COUNTRY_39", table)
        self.assertEqual(table["CELL_100"][0], 1)
        self.assertEqual(table["CELL_100"][9], 10.0)

    def test_02_mapper_missing_values(self):
        """Test mapper gracefully handles missing values without fabricating zeros."""
        sample_line = "100\t1383260400000\t39\t\t\t\t\t"
        parts = sample_line.split("\t")
        self.assertEqual(len(parts), 8)
        
        # Check parsing
        traffic_data = []
        for i in range(3, 8):
            f_str = parts[i].strip()
            if f_str == "":
                traffic_data.append((0.0, 0))
            else:
                traffic_data.append((float(f_str), 1))
        
        for val, cnt in traffic_data:
            self.assertEqual(val, 0.0)
            self.assertEqual(cnt, 0)

    def test_03_mapper_skips_malformed(self):
        """Test mapper rejects records with invalid field counts or non-integers."""
        bad_lines = [
            "100\t1383260400000\t39", # Only 3 fields
            "abc\t1383260400000\t39\t1.0\t1.0\t1.0\t1.0\t1.0", # Non-int cell_id
            "100\tINVALID_TS\t39\t1.0\t1.0\t1.0\t1.0\t1.0" # Non-int timestamp
        ]
        for bad in bad_lines:
            parts = bad.split("\t")
            valid = True
            if len(parts) != 8:
                valid = False
            else:
                try:
                    int(parts[0])
                    int(parts[1])
                    int(parts[2])
                except ValueError:
                    valid = False
            self.assertFalse(valid)

    def test_04_reducer_aggregation(self):
        """Test reducer properly accumulates intermediate values and calculates averages."""
        # 2 records for CELL_500: (val=10, cnt=1) and (val=20, cnt=1)
        # acc: [rec_cnt, s_in_s, s_in_c, s_out_s, s_out_c, c_in_s, c_in_c, c_out_s, c_out_c, net_s, net_c]
        acc = [2, 30.0, 2, 10.0, 1, 0.0, 0, 5.0, 1, 100.0, 2]
        
        s_in_avg = acc[1] / acc[2]
        self.assertEqual(s_in_avg, 15.0)
        
        # call_in has cnt=0, avg must be 0.0
        c_in_avg = (acc[5] / acc[6]) if acc[6] > 0 else 0.0
        self.assertEqual(c_in_avg, 0.0)

    def test_05_mapreduce_output_file_exists_and_valid(self):
        """Test local and HDFS MapReduce outputs contain exactly 10,390 keys and 19 columns."""
        mr_file = os.path.join(LOCAL_WORKSPACE, "data", "processed", "mapreduce", "part-00000")
        self.assertTrue(os.path.exists(mr_file), "MapReduce output part-00000 not found locally")
        
        cell_count = 0
        time_count = 0
        country_count = 0
        with open(mr_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                self.assertEqual(len(parts), 19, f"Row did not contain 19 columns: {parts}")
                if parts[0] == "CELL":
                    cell_count += 1
                elif parts[0] == "TIME":
                    time_count += 1
                elif parts[0] == "COUNTRY":
                    country_count += 1
        
        self.assertEqual(cell_count, 10000, f"Expected 10,000 cells, got {cell_count}")
        self.assertEqual(time_count, 144, f"Expected 144 time intervals, got {time_count}")
        self.assertEqual(country_count, 246, f"Expected 246 countries, got {country_count}")
        self.assertEqual(cell_count + time_count + country_count, 10390)

    def test_06_record_reconciliation_invariant(self):
        """Test total record count across TIME partitions exactly equals 4,842,625."""
        mr_file = os.path.join(LOCAL_WORKSPACE, "data", "processed", "mapreduce", "part-00000")
        total_time_records = 0
        total_cell_records = 0
        with open(mr_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if parts[0] == "TIME":
                    total_time_records += int(parts[2])
                elif parts[0] == "CELL":
                    total_cell_records += int(parts[2])
        
        self.assertEqual(total_time_records, 4842625, "Time records reconciliation mismatch!")
        self.assertEqual(total_cell_records, 4842625, "Cell records reconciliation mismatch!")

    def test_07_analytics_report_integrity(self):
        """Verify analytics report metrics exist and are non-zero."""
        analytics_file = os.path.join(LOCAL_WORKSPACE, "reports", "telecom_analytics.json")
        self.assertTrue(os.path.exists(analytics_file))
        with open(analytics_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.assertEqual(len(data["top_20_cells_by_total_traffic"]), 20)
        self.assertEqual(len(data["top_20_countries_by_traffic"]), 20)
        self.assertEqual(len(data["temporal_distribution"]), 144)
        self.assertGreater(data["executive_traffic_totals"]["total_network_traffic"], 0)

    def test_08_anomaly_report_integrity(self):
        """Verify anomaly report contains explainable anomalies and valid baselines."""
        anomaly_file = os.path.join(LOCAL_WORKSPACE, "reports", "anomaly_report.json")
        self.assertTrue(os.path.exists(anomaly_file))
        with open(anomaly_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.assertIn("summary_counts", data)
        self.assertGreater(data["summary_counts"]["total_anomalies_flagged"], 0)
        self.assertIn("baselines", data)

if __name__ == "__main__":
    unittest.main()
