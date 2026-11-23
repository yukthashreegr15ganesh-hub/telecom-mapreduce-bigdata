# Large-Scale Telecommunication Data Processing & Performance Monitoring Using MapReduce

**Engineering Final Report**  
**Project Workspace:** `C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce`  
**Execution Environment:** Windows 10/11 Host + Ubuntu 24.04.3 LTS (WSL2)  
**Distributed Core:** Apache Hadoop 3.4.0 (HDFS + Hadoop Streaming)  
**Runtime:** OpenJDK 11.0.33 + Python 3.12 (WSL2) / Python 3.10 (Host Dashboard)  
**Execution Date:** November 23, 2026  
**Final Status:** **PRODUCTION OPERATIONAL & VERIFIED**

---

## 1. Executive Summary & Project Abstract

This project successfully implements an end-to-end, enterprise-grade big data processing and network performance monitoring architecture using Apache Hadoop and MapReduce. The system processes authentic telecommunications Call Detail Records (CDRs) from Telecom Italia covering the Milan metropolitan area.

The architecture comprises:
1. **Authentic Dataset Acquisition & Ingestion:** Ingested the authentic 322.87 MB Day 1 dataset (4,842,625 records) into HDFS with 100% cryptographic MD5 checksum verification against the Harvard Dataverse DOI repository.
2. **Robust HDFS Daemon Architecture:** Resolved WSL ephemeral session termination via `loginctl` session lingering and dedicated `systemd` service units for NameNode and DataNode.
3. **Data Quality & Preprocessing Engine:** Built a streaming validator that profiled the full dataset, preserved traffic sparsity explicitly, verified zero data loss, and published clean normalized TSV datasets.
4. **Hadoop Streaming MapReduce Execution:** Designed and executed a combined aggregation MapReduce job using the In-Mapper Combining pattern, aggregating 4.84M records into 10,390 summary keys in 16.01 seconds (302,565 records/sec).
5. **Telecom Traffic Analytics:** Profiled SMS and voice call directional ratios, spatial traffic concentration (Gini coefficient 0.5952, top 20% cells carrying 63.11% volume), and 24-hour diurnal patterns.
6. **Network Performance Monitoring & Anomaly Detection:** Deployed an explainable, non-parametric anomaly detection engine (Median Absolute Deviation and Modified Z-scores) identifying 56 empirical traffic anomalies.
7. **Interactive Streamlit Dashboard:** Launched a full-featured web dashboard providing live KPI monitoring, interactive charts, hotspot analysis, and Hadoop execution telemetry at `http://localhost:8501`.

---

## 2. Verified Dataset Specification & Integrity

- **Dataset Source:** Telecom Italia Big Data Challenge (Harvard Dataverse DOI: `10.7910/DVN/EGZHFV`)
- **Raw File:** `data/raw/sms-call-internet-mi-2013-11-01.txt`
- **File Size:** `322,874,887 bytes` (307.92 MB)
- **Total Record Count:** `4,842,625`
- **Authentic MD5 Checksum:** `658c49f8e3c7910bd3bb2bafbf62cdce` (100% match)
- **HDFS Location:** `/telecom/data/raw/sms-call-internet-mi-2013-11-01.txt`
- **HDFS Replication Factor:** `1` (Single-node pseudo-distributed)
- **HDFS Internal Checksum:** `MD5-of-262144MD5-of-512CRC32C 00000200000000000004000036717c3ec5380d6b5d21faf9b2adeadc`

---

## 3. Apache Hadoop Infrastructure & Process Engineering

### Execution Mode Disclosure
Hadoop 3.4.0 is deployed in a resource-constrained pseudo-distributed single-node configuration:
- **Filesystem (`core-site.xml`):** `hdfs://localhost:9000`
- **HDFS Daemons:** `NameNode` (RPC port 9000, Web UI 9870), `DataNode` (Data port 9866, IPC 9867, Web UI 9864).
- **Execution Mode (`mapred-site.xml`):** `mapreduce.framework.name=local` (Single-Node `LocalJobRunner` processing against distributed HDFS block storage).

### WSL2 Session Isolation & Systemd Units
Because ephemeral WSL2 subshells terminate process groups upon completion via `SIGHUP`, custom `systemd` service units were deployed:
- `/etc/systemd/system/hadoop-namenode.service`
- `/etc/systemd/system/hadoop-datanode.service`
- Enabled via `systemctl enable --now hadoop-namenode hadoop-datanode` with user lingering (`loginctl enable-linger dminmlops`).

---

## 4. Preprocessing & Data Quality Profiling

The streaming preprocessor (`scripts/preprocess_telecom.py`) validated all 4,842,625 records against an 8-column schema:

| Column | Missing Count | Missing % | Domain & Validation Logic |
| :--- | :---: | :---: | :--- |
| `cell_id` | 0 | **0.00%** | Mandatory; integer $1 \le \text{cell\_id} \le 10,000$ |
| `timestamp` | 0 | **0.00%** | Mandatory; 10-minute epoch ms slot |
| `country_code` | 0 | **0.00%** | Mandatory; ITU-T calling code ($\ge 0$) |
| `sms_in` | 1,981,177 | **40.91%** | Float $\ge 0.0$; preserved explicitly |
| `sms_out` | 3,210,070 | **66.29%** | Float $\ge 0.0$; preserved explicitly |
| `call_in` | 3,329,423 | **68.75%** | Float $\ge 0.0$; preserved explicitly |
| `call_out` | 2,611,016 | **53.92%** | Float $\ge 0.0$; preserved explicitly |
| `internet_traffic` | 2,488,626 | **51.39%** | Float $\ge 0.0$; preserved explicitly |

### Invariant Balance Check
$$\text{Input Records} (4,842,625) = \text{Clean Output} (4,842,625) + \text{Rejected Output} (0)$$
- **Zero data loss verified.** Clean dataset stored at `/telecom/data/processed/clean/sms-call-internet-mi-2013-11-01-clean.tsv` (317,887,646 bytes).

---

## 5. MapReduce Architecture & Performance Benchmarks

### In-Mapper Combining Architecture
To maximize throughput and eliminate MapReduce shuffle bottlenecks on single-node hardware, `scripts/mapper.py` implements the **In-Mapper Combining Pattern**:
- Accumulates intermediate metrics across bounded batches in memory.
- Emits consolidated partial sums for `CELL_<id>`, `TIME_<ts>`, and `COUNTRY_<cc>`.
- `scripts/reducer.py` computes exact final counts, sums, non-null averages, and total traffic volumes.

### Hadoop Job Counters Audit
```text
Map input records:               4,842,625
Map output records:                 16,126
Reduce input groups:                10,390
Reduce output records:              10,390
Bytes Read (HDFS):             317,895,838 (303.17 MB)
Bytes Written (HDFS):            1,526,145 (1.46 MB)
GC time elapsed:                     32 ms
Total Committed Heap:            919.98 MB
Execution Duration:                  16.01 seconds
Processing Throughput:             302,565 records/second
```

---

## 6. Telecom Traffic Analytics

Aggregated from the 10,390 reduced keys:

### 1. Metropolitan Traffic Totals
- **Total Network Traffic:** `95,727,626.19` normalized activity units
- **Mobile Internet Data:** `82,479,246.59` units (**86.16%** of total metropolitan volume)
- **SMS Traffic:** `7,428,817.42` units (**7.76%** of volume)
  - Inbound SMS: `4,606,387.33` | Outbound SMS: `2,822,430.08` | Ratio: **1.632x inbound bias**
- **Voice Calls:** `5,819,562.19` units (**6.08%** of volume)
  - Inbound Calls: `2,622,799.88` | Outbound Calls: `3,196,762.31` | Ratio: **0.820x outbound bias**

### 2. Spatial Concentration (Pareto & Gini Analysis)
- **Gini Coefficient:** `0.5952` (High spatial inequality)
- **Top 1% Cells (100 cells):** Carry `9.81%` of all traffic.
- **Top 5% Cells (500 cells):** Carry `30.39%` of all traffic.
- **Top 20% Cells (2,000 cells):** Carry **`63.11%`** of all metropolitan traffic.

### 3. Diurnal Temporal Profiling
- **Peak Traffic Interval:** `2013-11-01 10:10:00 UTC` (`868,986.91` units / 42,074 records)
- **Lowest Traffic Interval:** `2013-11-01 04:40:00 UTC` (`348,265.95` units / 20,802 records)
- **Diurnal Dynamic Range:** Peak interval volume is **2.50x** higher than nighttime baseline.

### 4. Top 5 Busiest Cell Towers
1. **Cell 5060:** Total Traffic `364,577.67` | Internet `335,014.28` | Calls `17,046.77`
2. **Cell 5059:** Total Traffic `346,801.32` | Internet `320,812.54` | Calls `15,487.60`
3. **Cell 4259:** Total Traffic `328,194.20` | Internet `304,118.91` | Calls `13,674.15`
4. **Cell 5258:** Total Traffic `312,984.11` | Internet `289,451.80` | Calls `12,890.12`
5. **Cell 5161:** Total Traffic `298,710.45` | Internet `276,190.22` | Calls `12,110.45`

---

## 7. Network Performance Monitoring & Anomaly Detection

A robust non-parametric anomaly detection engine (`scripts/anomaly_detector.py`) was deployed:
- **Statistical Model:** Median Absolute Deviation (MAD) & Boris Iglewicz Modified Z-Score.
- **Total Flagged Anomalies:** `56`
  - **Rate-of-Change Spikes:** `5` interval-to-interval volume surges/drops ($Z \ge 2.5$).
  - **Cell Hotspot Outliers:** `51` extreme-traffic cell towers ($>99.5\text{th}$ percentile, up to $73\times$ metropolitan median).

> **Monitoring Disclaimer:** All flagged anomalies represent empirical statistical deviations in CDR aggregate traffic volume, reflecting localized public gatherings, transit congestion, or morning wake-up traffic surges, rather than physical network hardware failures.

---

## 8. Streamlit Web Dashboard

A full-featured Streamlit dashboard was developed and launched at **`http://localhost:8501`**:
- **Section 1: Executive Overview:** Live KPI metric cards and spatial/temporal bounds.
- **Section 2: Telecom Traffic Analytics:** SMS & voice call directional ratios and channel comparisons.
- **Section 3: Cell Tower Performance:** Gini curve, Pareto rankings, and Top 20 cell data tables.
- **Section 4: Country-Level Traffic:** International origin/destination rankings across 246 countries.
- **Section 5: Temporal Traffic Monitoring:** 24-hour diurnal line charts across 144 intervals.
- **Section 6: Anomaly Detection:** Explainable anomaly cards and severity breakdown tables.
- **Section 7: MapReduce Execution Metrics:** Hadoop job counter tables and HDFS output listings.

---

## 9. Comprehensive Testing & Validation Summary

Automated test suite (`scripts/test_pipeline.py`) executed 8 rigorous test suites with 100% pass rate:
1. `test_01_mapper_normal_record`: Verified mapper parsing and multi-key emissions.
2. `test_02_mapper_missing_values`: Verified graceful missing-value handling without zero conversion.
3. `test_03_mapper_skips_malformed`: Verified strict rejection of non-8-field lines.
4. `test_04_reducer_aggregation`: Verified accurate aggregation and non-null average computation.
5. `test_05_mapreduce_output_file_exists_and_valid`: Confirmed exact 10,390 output keys and 19 columns.
6. `test_06_record_reconciliation_invariant`: Reconciled 4,842,625 records across all partitions.
7. `test_07_analytics_report_integrity`: Validated non-zero analytics metrics and rankings.
8. `test_08_anomaly_report_integrity`: Verified anomaly score calculations and baselines.

---

## 10. HDFS Directory & Project Artifact Registry

### HDFS Storage Map
```text
/telecom
├── data/
│   ├── raw/
│   │   └── sms-call-internet-mi-2013-11-01.txt            [322,874,887 bytes | 4,842,625 raw records]
│   └── processed/
│       ├── clean/
│       │   └── sms-call-internet-mi-2013-11-01-clean.tsv  [317,887,646 bytes | 4,842,625 clean records]
│       └── rejected/
│           └── sms-call-internet-mi-2013-11-01-rejected.tsv [28 bytes header | 0 rejected records]
├── output/
│   └── mapreduce/
│       ├── _SUCCESS                                      [0 bytes]
│       └── part-00000                                    [1,526,145 bytes | 10,390 reduced keys]
└── results/
    ├── data_quality/
    │   └── data_quality_report.json                      [3,575 bytes]
    ├── analytics/
    │   └── telecom_analytics.json                        [88,412 bytes]
    └── anomalies/
        └── anomaly_report.json                           [24,198 bytes]
```

### Local Code & Report Registry
- **Pipeline Scripts:**
  - [scripts/mapper.py](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/scripts/mapper.py)
  - [scripts/reducer.py](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/scripts/reducer.py)
  - [scripts/run_mapreduce.py](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/scripts/run_mapreduce.py)
  - [scripts/generate_analytics.py](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/scripts/generate_analytics.py)
  - [scripts/anomaly_detector.py](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/scripts/anomaly_detector.py)
  - [scripts/dashboard.py](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/scripts/dashboard.py)
  - [scripts/run_dashboard.py](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/scripts/run_dashboard.py)
  - [scripts/test_pipeline.py](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/scripts/test_pipeline.py)
- **Analytical & Performance Reports:**
  - [reports/mapreduce_execution_report.json](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/reports/mapreduce_execution_report.json)
  - [reports/telecom_analytics.json](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/reports/telecom_analytics.json)
  - [reports/anomaly_report.json](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/reports/anomaly_report.json)
  - [reports/performance_benchmark.json](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/reports/performance_benchmark.json)
  - [reports/data_quality_report.json](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/reports/data_quality_report.json)
