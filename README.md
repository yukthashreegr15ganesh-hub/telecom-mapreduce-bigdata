# Large-Scale Telecommunication Data Processing & Performance Monitoring Using MapReduce

[![Hadoop](https://img.shields.io/badge/Apache%20Hadoop-3.4.0-red.svg)](https://hadoop.apache.org/)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://telecom-mapreduce-bigdata-bwpsylums7mgnz4yngwact.streamlit.app/)
[![Firebase Hosting](https://img.shields.io/badge/Firebase-Landing%20Page-orange.svg?logo=firebase)](https://telecom-bigdata-analytics.web.app)
[![License: ODbL](https://img.shields.io/badge/License-ODbL%20v1.0-green.svg)](https://opendatacommons.org/licenses/odbl/)

> 🚀 **Live Deployments:**
> - **Interactive Streamlit Dashboard:** [telecom-mapreduce-bigdata-bwpsylums7mgnz4yngwact.streamlit.app](https://telecom-mapreduce-bigdata-bwpsylums7mgnz4yngwact.streamlit.app/)
> - **Project Showcase Landing Page:** [telecom-bigdata-analytics.web.app](https://telecom-bigdata-analytics.web.app)

An end-to-end, reproducible Big Data Engineering and Distributed Systems project designed to process, aggregate, profile, and monitor large-scale telecommunication Call Detail Records (CDRs) using **Apache Hadoop MapReduce** and **HDFS**.

---

## 📋 Table of Contents
- [1. Project Overview](#1-project-overview)
- [2. Problem Statement](#2-problem-statement)
- [3. System Architecture](#3-system-architecture)
- [4. Technology Stack](#4-technology-stack)
- [5. Dataset Source & Attribution](#5-dataset-source--attribution)
- [6. Dataset Acquisition](#6-dataset-acquisition)
- [7. Installation & Prerequisites](#7-installation--prerequisites)
- [8. Hadoop & HDFS Configuration](#8-hadoop--hdfs-configuration)
- [9. End-to-End Pipeline Execution](#9-end-to-end-pipeline-execution)
- [10. Interactive Streamlit Dashboard](#10-interactive-streamlit-dashboard)
- [11. Measured Benchmarks & Results](#11-measured-benchmarks--results)
- [12. Testing & Quality Validation](#12-testing--quality-validation)
- [13. Known Limitations & Architectural Disclosure](#13-known-limitations--architectural-disclosure)

---

## 1. Project Overview
This repository contains a production-ready Big Data processing architecture for metropolitan-scale telecommunications data. The pipeline ingests **4,842,625 authentic Call Detail Records** (322.87 MB) from Telecom Italia covering the Milan metropolitan area, stores them across a distributed HDFS block topology, performs multi-dimensional MapReduce aggregations, extracts traffic insights, detects empirical network anomalies, and visualizes KPIs in a low-latency interactive Streamlit dashboard.

---

## 2. Problem Statement
Modern cellular networks generate hundreds of millions of CDR events daily across distributed radio towers. Telecommunications operators face three critical data challenges:
1. **High Volume & Spatial Density:** Processing millions of multi-channel communication events (SMS, Voice, Packet Data) across thousands of geometric grid cells without data loss or memory overflow.
2. **Extreme Traffic Sparsity:** Real-world CDR logs have heavy missing-value rates (40% to 68% per channel) where cellular activity was absent. Naive data pipelines incorrectly replace missing values with zeros, corrupting statistical variance and density models.
3. **Operational Monitoring & Anomaly Detection:** Network engineers require explainable, non-parametric anomaly detection to distinguish between routine diurnal variations, sudden rate-of-change spikes, and localized urban hotspotting.

This project solves these challenges using **Apache Hadoop Streaming MapReduce**, the **In-Mapper Combining design pattern**, and **Median Absolute Deviation (MAD)** anomaly modeling.

---

## 3. System Architecture

```text
+---------------------------------------------------------------------------------------+
|                                  DATA INGESTION                                      |
|  Harvard Dataverse (DOI: 10.7910/DVN/EGZHFV) -> scripts/download_dataset.py          |
|  Verified Raw CDRs (322.87 MB, 4,842,625 records) -> MD5 Checksum Verification       |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                             HADOOP HDFS STORAGE LAYER                                |
|  /telecom/data/raw/sms-call-internet-mi-2013-11-01.txt (3 HDFS Blocks, Repl: 1)       |
|  Persistent Services: hadoop-namenode.service & hadoop-datanode.service (systemd)     |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                        STREAMING PREPROCESSING & VALIDATION                          |
|  scripts/preprocess_telecom.py -> Validates 8-field schema, preserves sparsity        |
|  Clean TSV: /telecom/data/processed/clean/ (4,842,625 valid | 0 rejected | 0 loss)    |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                       HADOOP STREAMING MAPREDUCE AGGREGATION                          |
|  scripts/mapper.py (In-Mapper Combining) -> scripts/reducer.py                       |
|  Hadoop Streaming 3.4.0 -> Emits 10,390 aggregated keys (Cell, Time, Country)       |
|  Throughput: 302,565 records/sec in 16.01s -> /telecom/output/mapreduce/part-00000   |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                    ANALYTICS & ANOMALY DETECTION ENGINES                             |
|  scripts/generate_analytics.py -> Spatial Gini (0.5952), Pareto 80/20, Ratios         |
|  scripts/anomaly_detector.py -> Non-parametric Median/MAD Modified Z-Score (56 Flagged)
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                     INTERACTIVE STREAMLIT DASHBOARD (PORT 8501)                       |
|  scripts/dashboard.py -> @st.cache_data (<50ms latency) -> Executive, Cells, Anomalies|
+---------------------------------------------------------------------------------------+
```

---

## 4. Technology Stack
- **Distributed Processing:** Apache Hadoop 3.4.0 (Hadoop Streaming, MapReduce v2, HDFS)
- **Java Runtime:** OpenJDK 11.0.33 (64-bit Server VM)
- **Host OS & Virtualization:** Windows 10/11 Host + Ubuntu 24.04.3 LTS on WSL2
- **Process Orchestration:** Linux `systemd` daemon unit services with session lingering (`loginctl`)
- **Programming Languages:** Python 3.12 (WSL2 Data Pipeline) & Python 3.10 (Host Dashboard)
- **Data Engineering Libraries:** Pandas, Matplotlib, Requests, Urllib3
- **Visualization & Web App:** Streamlit (Headless production mode, Arrow in-memory caching)
- **Quality Assurance:** Python `unittest` framework (automated pipeline regression tests)

---

## 5. Dataset Source & Attribution
- **Dataset Name:** Telecommunications: SMS, Call, Internet - MI (Milan)
- **Originating Entity:** Telecom Italia (TIM Big Data Challenge)
- **Repository:** Harvard Dataverse Repository
- **Persistent Identifier (DOI):** [doi:10.7910/DVN/EGZHFV](https://doi.org/10.7910/DVN/EGZHFV)
- **Scientific Citation:** Barlacchi, G., De Nadai, M., Larcher, R., Casella, A., Chitic, C., Torrisi, G., Tucci, F., Vespignani, A., Pentland, A., & Lepri, B. (2015). *A multi-source dataset of urban life in the city of Milan and the Province of Trentino.* Nature Scientific Data, 2:150055.
- **License:** Open Database License (ODbL v1.0).

---

## 6. Dataset Acquisition

### Authentic Day 1 File Specifications
- **Filename:** `sms-call-internet-mi-2013-11-01.txt`
- **Exact Size:** `322,874,887 bytes` (307.92 MB uncompressed)
- **Record Count:** Exactly `4,842,625 lines`
- **MD5 Checksum:** `658c49f8e3c7910bd3bb2bafbf62cdce` (100% cryptographic match against official manifest)

### Automated Acquisition
```bash
# Negotiates Harvard Dataverse Guestbook ID 96 and acquires the authenticated stream
python scripts/download_dataset.py --date 2013-11-01
```

### Manual Acquisition
1. Visit the [Harvard Dataverse Repository](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/EGZHFV).
2. Select the `Files` tab and locate `sms-call-internet-mi-2013-11-01.txt`.
3. Complete the Guestbook terms and place the downloaded file into `data/raw/sms-call-internet-mi-2013-11-01.txt`.

---

## 7. Installation & Prerequisites

### Windows Host Dependencies
```powershell
pip install -r requirements.txt
```

### WSL2 Ubuntu Environment
```bash
sudo apt update
sudo apt install -y openjdk-11-jdk python3 python3-pip
```

---

## 8. Hadoop & HDFS Configuration

### 1. Configure HDFS Directories & Permissions
```bash
sudo mkdir -p /var/hadoop/hdfs/namenode /var/hadoop/hdfs/datanode /var/log/hadoop
sudo chown -R dminmlops:dminmlops /var/hadoop /var/log/hadoop
```

### 2. Environment Variables (`/opt/hadoop/etc/hadoop/hadoop-env.sh`)
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/opt/hadoop
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export HADOOP_LOG_DIR=/var/log/hadoop
export HADOOP_HEAPSIZE_MAX=1024m
export HDFS_NAMENODE_OPTS="-Xms256m -Xmx512m $HADOOP_NAMENODE_OPTS"
export HDFS_DATANODE_OPTS="-Xms256m -Xmx512m $HADOOP_DATANODE_OPTS"
```

### 3. Deploy Systemd Units for Persistent Daemons
```bash
# Prevent WSL2 from killing background daemons upon session logout
sudo loginctl enable-linger dminmlops

# Enable and start HDFS daemons
sudo systemctl enable --now hadoop-namenode hadoop-datanode
```

---

## 9. End-to-End Pipeline Execution

Execute the pipeline in sequential order:

```bash
# Step 1: Ingest verified raw dataset into HDFS and audit checksum
python scripts/ingest_to_hdfs.py

# Step 2: Stream, validate, and clean dataset from HDFS
wsl -d Ubuntu -u dminmlops -e python3 scripts/preprocess_telecom.py

# Step 3: Run Hadoop Streaming MapReduce aggregation job
python scripts/run_mapreduce.py

# Step 4: Extract multi-channel telecom analytics & concentration metrics
python scripts/generate_analytics.py

# Step 5: Execute Median/MAD anomaly detection engine
python scripts/anomaly_detector.py

# Step 6: Compile performance benchmark telemetry
python scripts/generate_benchmark.py

# Step 7: Run automated unit & integration test suite
python scripts/test_pipeline.py
```

---

## 10. Interactive Streamlit Dashboard

Launch the optimized, low-latency dashboard:

```bash
python scripts/run_dashboard.py
```
Open your browser at **`http://localhost:8501`**.

### Dashboard Features
1. **Executive Overview:** Headline KPI cards, traffic distribution, and grid boundary metadata.
2. **Telecom Traffic Analytics:** Inbound vs outbound SMS & Call balance charts, channel volume breakdown.
3. **Cell Tower Performance:** Interactive Top $N$ slider (5 to 20), sorting metrics, Gini inequality indicator.
4. **Country-Level Traffic:** International calling code search and Top 20 partner bar charts.
5. **Temporal Monitoring:** 24-hour diurnal line charts with Morning/Afternoon/Night filtering slices.
6. **Anomaly Detection:** Explainable anomaly cards categorized by Severity (Critical, High, Moderate).
7. **MapReduce Metrics:** Hadoop job counter audits and HDFS directory verification.

---

## 11. Measured Benchmarks & Results

All benchmarks represent authentic wall-clock execution metrics:

| Metric Category | Measured Result | Performance Analysis |
| :--- | :---: | :--- |
| **Total Ingested Records** | `4,842,625` | 100% of authentic Telecom Italia Day 1 CDRs |
| **Clean Output Records** | `4,842,625` | Validated against 8-column schema (0 malformed) |
| **Data Loss Rate** | **`0.00%`** | $\text{Input} (4,842,625) = \text{Valid} (4,842,625) + \text{Rejected} (0)$ |
| **MapReduce Execution Time** | **`16.01 seconds`** | Fast in-memory combining pattern |
| **MapReduce Throughput** | **`302,565 records/sec`** | $18.94\text{ MB/sec}$ processing bandwidth |
| **Reduced Summary Keys** | `10,390` | Consolidates 10,000 Cells + 144 Intervals + 246 Countries |
| **Metropolitan Network Traffic** | `95,727,626.19` | Normalized usage units across Milan |
| **Mobile Internet Share** | **`86.16%`** | `82,479,246.58` units (dominant communication channel) |
| **SMS Inbound / Outbound Ratio** | **`1.632x`** | Inbound biased (4.6M received vs 2.8M sent) |
| **Voice Inbound / Outbound Ratio**| **`0.820x`** | Outbound dominant (2.6M received vs 3.2M originated) |
| **Spatial Gini Coefficient** | **`0.5952`** | High spatial concentration |
| **Pareto 80/20 Distribution** | **`63.11%`** | Top 20% of cell towers carry 63.11% of metropolitan traffic |
| **Peak Traffic Interval** | `10:10 UTC` | `868,986.91` volume (2.50x higher than night baseline) |
| **Detected CDR Anomalies** | **`56`** | 5 interval rate-of-change spikes, 51 cell hotspots |
| **Dashboard HTTP Latency** | **`17.68 ms`** | In-memory Arrow caching, zero disk crawling |

---

## 12. Testing & Quality Validation

Run the automated regression test suite:
```bash
python scripts/test_pipeline.py
python scripts/validate_dashboard_performance.py
```

### Verified Test Coverage
- `test_01_mapper_normal_record`: Validates multi-key emission for cells, timestamps, and country codes.
- `test_02_mapper_missing_values`: Verifies proper handling of empty tab fields without fabricating zeros.
- `test_03_mapper_skips_malformed`: Confirms strict rejection of invalid field lengths or non-numeric tokens.
- `test_04_reducer_aggregation`: Validates arithmetic accumulation, non-null counts, and mean calculations.
- `test_05_mapreduce_output_file_exists_and_valid`: Confirms exact 10,390 output keys and 19 TSV columns.
- `test_06_record_reconciliation_invariant`: Enforces mathematical identity across all partition keys.
- `test_07_analytics_report_integrity`: Verifies presence and consistency of top rankings and ratios.
- `test_08_anomaly_report_integrity`: Tests statistical MAD models and modified Z-score boundaries.

---

## 13. Known Limitations & Architectural Disclosure

To maintain scientific integrity and academic transparency:
1. **Single-Node Execution:** The MapReduce job is executed on a single-node host via Hadoop `LocalJobRunner` reading from and writing to distributed HDFS block storage. It is **not** a multi-node distributed cluster.
2. **Dataset Temporal Scope:** In accordance with project instructions, this pipeline processes Day 1 of the dataset (`2013-11-01`, containing `4,842,625 records`). The remaining 61 daily files are not downloaded.
3. **Normalized CDR Indices:** Activity measurements are dimensionless indices normalized by Telecom Italia to protect commercial confidentiality and subscriber privacy; they represent proportional density rather than raw call or byte counts.
4. **Statistical Anomaly Disclaimer:** Detected anomalies represent empirical mathematical outliers in CDR traffic volume (surges, commuter spikes, transit clusters) and do not represent confirmed physical telecommunications hardware failures.
