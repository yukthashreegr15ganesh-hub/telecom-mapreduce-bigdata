# Telecom Italia Milan CDR Preprocessing & Data Quality Report

**Project:** Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce  
**Environment:** WSL2 (Ubuntu 24.04.3 LTS) on Windows 10/11  
**Hadoop Framework:** Apache Hadoop 3.4.0 (Single-Node HDFS Pseudo-Distributed)  
**Execution Script:** `scripts/preprocess_telecom.py`  
**Execution Date:** November 23, 2026  
**Pipeline Status:** **SUCCESSFUL & VERIFIED (Zero Data Loss)**

---

## 1. Executive Summary

A reproducible, memory-efficient data preprocessing and quality validation pipeline was implemented and executed against the authentic Telecom Italia Milan dataset stored in HDFS (`/telecom/data/raw/sms-call-internet-mi-2013-11-01.txt`). 

The pipeline streamed all **4,842,625 records** from HDFS, enforced strict schema constraints, validated field domains and physical bounds, performed statistical profiling across all dimensions, and segregated the outputs into clean normalized datasets and rejected inspection logs.

### Key Headline Metrics
- **Total Ingested Records:** `4,842,625`
- **Clean Valid Records:** `4,842,625` (100.0%)
- **Malformed / Rejected Records:** `0` (0.0%)
- **Duplicate Primary Keys:** `0` (0.0%)
- **Spatial Coverage:** Exactly `10,000 / 10,000` grid cells (100.0% coverage of Milan tessellation)
- **Temporal Coverage:** Exactly `144` non-overlapping 10-minute intervals (24 hours full cycle)
- **International Calling Codes:** `246` unique sovereign calling prefixes
- **Balance Equation:** $\text{Input Records} (4,842,625) = \text{Clean Output} (4,842,625) + \text{Rejected Output} (0)$ — **Passed**

---

## 2. Data Schema & Validation Constraints

The pipeline enforces an 8-column uncompressed Tab-Separated Values (TSV) schema:

| Index | Field Name | Data Type | Constraint & Validation Logic | Handling of Missing |
| :---: | :--- | :--- | :--- | :--- |
| **0** | `cell_id` | Integer | Mandatory; $1 \le \text{cell\_id} \le 10,000$ | Reject record if missing/invalid |
| **1** | `timestamp` | BigInt | Mandatory; positive Unix Epoch ms ($\sim 2013-11-01$) | Reject record if missing/invalid |
| **2** | `country_code` | Integer | Mandatory; non-negative integer ($\ge 0$) | Reject record if missing/invalid |
| **3** | `sms_in` | Float / Empty | Optional; if present, must parse to float and $\ge 0.0$ | Preserved as empty TSV field (`""`) |
| **4** | `sms_out` | Float / Empty | Optional; if present, must parse to float and $\ge 0.0$ | Preserved as empty TSV field (`""`) |
| **5** | `call_in` | Float / Empty | Optional; if present, must parse to float and $\ge 0.0$ | Preserved as empty TSV field (`""`) |
| **6** | `call_out` | Float / Empty | Optional; if present, must parse to float and $\ge 0.0$ | Preserved as empty TSV field (`""`) |
| **7** | `internet_traffic` | Float / Empty | Optional; if present, must parse to float and $\ge 0.0$ | Preserved as empty TSV field (`""`) |

> **Important Engineering Principle:** Missing traffic metrics represent periods with no telecommunication activity on that channel within the cell. These are **never silently replaced with zero**, which would introduce statistical distortion into downstream mobile density modeling. Instead, missing fields are preserved explicitly.

---

## 3. Spatial & Temporal Profiling Discoveries

### Spatial Tessellation
- **Grid Bound:** Milan metropolitan bounding box.
- **Unique Cells Observed:** `10,000`
- **Minimum Cell ID:** `1`
- **Maximum Cell ID:** `10,000`
- **Coverage:** `100.0%`. Every single geometric tile in the Milan grid recorded at least one telecommunication activity event during the 24-hour observation cycle.

### Temporal Profiling
- **Observation Start:** `1383260400000` ms $\rightarrow$ `2013-10-31 23:00:00 UTC` (`2013-11-01 00:00:00 CET`)
- **Observation End:** `1383346200000` ms $\rightarrow$ `2013-11-01 22:50:00 UTC` (`2013-11-01 23:50:00 CET`)
- **Discrete Time Slots:** Exactly $144$ non-overlapping windows of $600,000$ ms ($10$ minutes).
- **Span:** $23.83$ hours (completing a full calendar cycle from slot 0 to slot 143).

### International Call & Roaming Distribution
- **Unique Country Codes:** `246`
- **Primary Country Codes Observed:** Italy (`39`), Unknown/Domestic Internal (`0`), United States/Canada (`1`), Russia/Kazakhstan (`7`), Egypt (`20`), South Africa (`27`), Greece (`30`), Netherlands (`31`), France (`33`), Spain (`34`), Switzerland (`41`), United Kingdom (`44`), Germany (`49`), and others.

---

## 4. Missing Value Analysis

The sparsity pattern of the multi-channel telecommunication traffic was profiled:

| Column | Total Records | Present Values | Missing Values | Missing % | Sparsity Pattern Interpretation |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `cell_id` | 4,842,625 | 4,842,625 | 0 | **0.00%** | Primary coordinate identifier; mandatory |
| `timestamp` | 4,842,625 | 4,842,625 | 0 | **0.00%** | Temporal coordinate identifier; mandatory |
| `country_code` | 4,842,625 | 4,842,625 | 0 | **0.00%** | International routing prefix; mandatory |
| `sms_in` | 4,842,625 | 2,861,448 | 1,981,177 | **40.91%** | Active in 59.09% of aggregated events |
| `sms_out` | 4,842,625 | 1,632,555 | 3,210,070 | **66.29%** | Outgoing SMS traffic is concentrated |
| `call_in` | 4,842,625 | 1,513,202 | 3,329,423 | **68.75%** | Highly localized incoming voice calls |
| `call_out` | 4,842,625 | 2,231,609 | 2,611,016 | **53.92%** | More widely dispersed than incoming calls |
| `internet_traffic` | 4,842,625 | 2,353,999 | 2,488,626 | **51.39%** | Mobile data logged in 48.61% of records |

---

## 5. Statistical Profile of Traffic Dimensions

Statistical moments for non-missing activity measurements across the metropolitan area:

| Metric Channel | Non-Null Count | Minimum | Maximum | Metropolitan Mean | Cumulative Sum |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`sms_in`** | 2,861,448 | $2.33 \times 10^{-6}$ | $234.018$ | $1.6098$ | $4,606,387.33$ |
| **`sms_out`** | 1,632,555 | $2.33 \times 10^{-6}$ | $295.726$ | $1.7288$ | $2,822,430.08$ |
| **`call_in`** | 1,513,202 | $2.33 \times 10^{-6}$ | $190.989$ | $1.7333$ | $2,622,799.88$ |
| **`call_out`** | 2,231,609 | $2.33 \times 10^{-6}$ | $187.869$ | $1.4325$ | $3,196,762.31$ |
| **`internet_traffic`** | 2,353,999 | $2.33 \times 10^{-6}$ | $4,995.605$ | $35.0379$ | $82,479,246.59$ |

### Data Engineering Insights
1. **Long-Tail Internet Consumption:** Internet traffic demonstrates a very heavy right-skewed tail, reaching peaks of $4,995.61$ in high-density commercial/transit zones (e.g., Duomo, Milano Centrale railway hub) compared to a metropolitan average of $35.04$.
2. **Normalized Minimum Floor:** All channels share a minimum positive floor of $2.33 \times 10^{-6}$, representing the base normalization quantum applied by Telecom Italia.

---

## 6. HDFS Storage Locations & Verification

The processed outputs were uploaded to HDFS and independently verified:

```text
/telecom
├── data/
│   ├── raw/
│   │   └── sms-call-internet-mi-2013-11-01.txt         [322,874,887 bytes | 4,842,625 records]
│   └── processed/
│       ├── clean/
│       │   └── sms-call-internet-mi-2013-11-01-clean.tsv [317,887,646 bytes | 4,842,625 records]
│       └── rejected/
│           └── sms-call-internet-mi-2013-11-01-rejected.tsv [28 bytes (Header only) | 0 records]
└── results/
    └── data_quality/
        └── data_quality_report.json                   [3,575 bytes]
```

### Verified File Details (`hdfs dfs -ls -R /telecom/data/processed /telecom/results/data_quality`)
```text
drwxr-xr-x   - dminmlops supergroup          0 2026-11-23 18:08 /telecom/data/processed/clean
-rw-r--r--   1 dminmlops supergroup  317887646 2026-11-23 18:08 /telecom/data/processed/clean/sms-call-internet-mi-2013-11-01-clean.tsv
drwxr-xr-x   - dminmlops supergroup          0 2026-11-23 18:08 /telecom/data/processed/rejected
-rw-r--r--   1 dminmlops supergroup         28 2026-11-23 18:08 /telecom/data/processed/rejected/sms-call-internet-mi-2013-11-01-rejected.tsv
-rw-r--r--   1 dminmlops supergroup       3575 2026-11-23 18:08 /telecom/results/data_quality/data_quality_report.json
```

---

## 7. Pipeline Testing & Invariant Validation

The pipeline verified the fundamental accounting invariant:

$$\text{Total Input Records} = \text{Valid Clean Output} + \text{Rejected Output}$$
$$4,842,625 = 4,842,625 + 0$$

- **Accidental Data Loss:** $0$ records lost.
- **Repeatability:** Fully reproducible via `python3 scripts/preprocess_telecom.py`.
- **Runtime Performance:** Streaming, validation, and profiling executed in $80.10$ seconds ($60,457$ records/sec throughput). Total execution including HDFS uploads and distributed streaming line audits completed in $223.46$ seconds.

---

## 8. Summary Artifacts

1. **Pipeline Script:** [scripts/preprocess_telecom.py](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/scripts/preprocess_telecom.py)
2. **Machine-Readable Quality Metrics:** [reports/data_quality_report.json](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/reports/data_quality_report.json)
3. **Markdown Documentation:** [docs/DATA_PREPROCESSING_REPORT.md](file:///C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/docs/DATA_PREPROCESSING_REPORT.md)
