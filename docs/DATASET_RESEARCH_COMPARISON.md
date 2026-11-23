# Telecommunications Dataset Comparative Research

## Overview
As part of **Phase 1: Dataset Research, Acquisition, and Verification** for the project *"Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce"*, we conducted an in-depth investigation of three major open-source telecommunications and mobile network datasets.

---

## 1. Candidate Datasets Investigated

### A. Telecom Italia Milan CDR Dataset (Primary Dataset)
* **Official Source & DOI:** [10.7910/DVN/EGZHFV](https://doi.org/10.7910/DVN/EGZHFV) (Harvard Dataverse)
* **Citation Reference:** Barlacchi, G. et al. *A multi-source dataset of urban life in the city of Milan and the Province of Trentino.* Scientific Data 2:150055 (Nature Publishing Group, 2015).
* **Publisher / Originator:** Telecom Italia (TIM) via the Telecom Italia Big Data Challenge 2014.
* **Collection Window:** November 1, 2013 to January 1, 2014 (62 consecutive daily measurement files).
* **Spatial Granularity:** Milan metropolitan area partitioned into a spatial grid of 10,000 square cells (each cell approximately 235m × 235m, EPSG:32632).
* **Temporal Granularity:** Aggregated into regular 10-minute time intervals across 24 hours per day (144 time intervals daily per cell).
* **Available Features / Metrics:**
  - `cell_id` (Spatial grid index: 1 to 10,000)
  - `timestamp` (Epoch millisecond integer timestamp)
  - `country_code` (ITU-T E.164 country calling code of interacting parties, e.g., 39 for Italy)
  - `sms_in` (Incoming SMS directional traffic volume metric)
  - `sms_out` (Outgoing SMS directional traffic volume metric)
  - `call_in` (Incoming voice call activity metric)
  - `call_out` (Outgoing voice call activity metric)
  - `internet_traffic` (Mobile internet connection CDR activity volume metric)
* **Total Size:** 20,804,803,507 bytes (~19.38 GB uncompressed across 62 daily `.txt` tab-separated files).
* **Record Count Estimate:** ~310 million records across the entire two-month period (~4.5 to 5.5 million records per daily file).
* **Licensing:** Open Database License (ODbL v1.0). Attribution: Telecom Italia / Open Data Trentino.

---

### B. MONROE Operational Mobile Network Dataset
* **Official Source:** MONROE Consortium (EU Horizon 2020), [https://www.monroe-project.eu/](https://www.monroe-project.eu/) and Zenodo repository.
* **Scope & Architecture:** Large-scale distributed hardware testbed with hundreds of multi-homed nodes mounted on stationary sites and public transit vehicles (trains, buses) across Norway, Sweden, Italy, and Spain.
* **Available Features / Metrics:**
  - Network-layer performance: TCP Round-Trip Time (RTT), Tstat passive flow traces, packet loss, retransmissions.
  - Application KPIs: HTTP/FTP throughput, DNS lookup latency, video streaming buffer stalling / QoE.
  - Physical modem telemetry: Radio Access Technology (3G UMTS, 4G LTE), signal power (RSRP), signal quality (RSRQ, RSSI), Band, and Carrier Aggregation state.
* **Data Format:** JSON-lines and CSV logs.
* **Total Size:** Hundreds of gigabytes to terabytes distributed across heterogeneous measurement campaigns.
* **Licensing:** Creative Commons Attribution 4.0 International (CC BY 4.0).

---

### C. Public 4G/5G Network Measurement Dataset (UCC MISL Traces)
* **Official Source:** Mobile and Internet Systems Laboratory (MISL), University College Cork (UCC), [https://github.com/uccmisl/5Gdataset](https://github.com/uccmisl/5Gdataset).
* **Citation Reference:** Raca, D., Leahy, D., Sreenan, C. J., & Quinlan, J. J. *Beyond Throughput: a 5G Dataset with Channel and Context Metrics.* ACM MMSys 2020.
* **Scope:** Real-world cellular traces collected from Irish mobile network operators across pedestrian, bicycle, bus, and automobile mobility scenarios.
* **Available Features / Metrics:**
  - Physical channel metrics: RSRP (dBm), RSRQ (dB), SINR (dB), CQI, MCS.
  - Transport & Application metrics: Uplink/Downlink throughput (kbps), packet inter-arrival times, video segment bitrate.
  - Contextual metrics: GPS velocity, latitude, longitude, cell handovers.
* **Data Format:** CSV trace files.
* **Total Size:** ~500 MB to 2 GB (focused trace files).
* **Licensing:** Academic Open Access.

---

## 2. Comparative Matrix

| Evaluation Criteria | Telecom Italia Milan CDR Dataset | MONROE Testbed Dataset | UCC 4G/5G Measurement Dataset |
| :--- | :--- | :--- | :--- |
| **Primary Domain** | Large-scale Telco Activity & CDRs | Active MBB Performance & Flows | Device-level Radio Channel KPIs |
| **Raw Storage Size** | **19.38 GB** (62 daily files) | > 500 GB (fragmented campaigns) | ~1.5 GB |
| **Total Record Volume** | **~310,000,000 records** | > 100,000,000 trace events | ~500,000 data points |
| **Data Format** | Tab-separated values (`.txt` TSV) | JSON / CSV / PCAP | CSV |
| **Spatial Coverage** | Uniform 100x100 grid (Milan urban) | Multi-country nodes (NO, SE, IT, ES) | Specific transit routes (Cork, Ireland) |
| **Temporal Coverage** | Continuous 2-month span (Nov-Dec 2013) | Multi-year periodic bursts | Short-duration test runs (15-min runs) |
| **Network Performance Indicators** | Aggregated call traffic, SMS volume, internet consumption, international interconnectivity | RTT, jitter, loss, RSRP, RSRQ, TCP retransmission, page load times | RSRP, RSRQ, SINR, CQI, DL/UL throughput, handover count |
| **Hadoop / MapReduce Suitability** | **Exceptional** (Uniform schema, block-friendly TSV, high volume, natural key partitioning by `cell_id`, `timestamp`, `country_code`) | Moderate (Irregular JSON hierarchies, requires heavy pre-parsing) | Low (Dataset size is too small to warrant distributed MapReduce) |
| **Download Mechanism** | Harvard Dataverse REST API with Guestbook token | Zenodo / HTTP download endpoints | GitHub raw repository / direct HTTP |
| **Licensing** | Open Database License (ODbL 1.0) | Open Access (CC BY 4.0) | MIT / Academic Open Access |

---

## 3. Engineering Justification for Selecting Telecom Italia Milan CDR

1. **Volume & Scale:** With 19.38 GB of uncompressed data and ~310 million activity records, this dataset fulfills enterprise big data engineering requirements. It naturally creates hundreds of HDFS blocks (at standard 128 MB block size: ~152 HDFS blocks), enabling multi-node distributed parallel processing in MapReduce.
2. **Schema Uniformity & High Cardinality:** The uniform tabular schema with well-defined spatial indices (`cell_id`), temporal stamps (`timestamp`), and international dimensions (`country_code`) offers ideal conditions for demonstrating partitioners, combiners, secondary sorting, and multi-metric aggregation algorithms in MapReduce.
3. **Traceability & Reliability:** Hosted permanently on Harvard Dataverse (`doi:10.7910/DVN/EGZHFV`) with verified MD5 checksums for every single file.
