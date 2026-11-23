# Telecommunication Dataset Technical Documentation

## 1. Dataset Overview & Source

* **Dataset Name:** Telecommunications - SMS, Call, Internet - MI (Milan)
* **Official Source (Dataverse):** Harvard Dataverse Repository
* **Persistent Identifier (DOI):** [doi:10.7910/DVN/EGZHFV](https://doi.org/10.7910/DVN/EGZHFV)
* **Citation:** Barlacchi, G., De Nadai, M., Larcher, R., Casella, A., Chitic, C., Torrisi, G., Tucci, F., Vespignani, A., Pentland, A., & Lepri, B. (2015). *A multi-source dataset of urban life in the city of Milan and the Province of Trentino.* Nature Scientific Data, 2:150055.
* **Originating Entity:** Telecom Italia (TIM Big Data Challenge)

---

## 2. Dataset Description

The Telecom Italia Milan Call Detail Records (CDR) dataset captures spatial and temporal telecommunications activity over the Milan metropolitan area. The measurements quantify communication intensity across multiple mobile network service channels:
- Short Message Service (SMS incoming and outgoing)
- Circuit-switched voice calls (incoming and outgoing)
- Mobile packet internet traffic (browsing, background data, streaming sessions)

Activity measurements are aggregated both spatially (onto a fixed geometric grid) and temporally (into uniform 10-minute intervals).

---

## 3. Spatial & Temporal Architecture

### Spatial Grid
* **Grid Bounds:** Milan metropolitan area, Italy (UTM Zone 32N / WGS84).
* **Grid Topology:** 10,000 square grid cells arranged in a 100 × 100 matrix.
* **Cell Dimensions:** Each grid cell measures approximately 235 meters × 235 meters (~0.055 km²).
* **Identifier:** `cell_id` (integer from 1 to 10,000). Cell numbering starts at the South-West corner of the bounding box and proceeds row-by-row to the North-East corner.

### Temporal Profiling
* **Collection Window:** November 1, 2013 00:00:00 CET through January 1, 2014 23:50:00 CET (62 consecutive calendar days).
* **Interval Duration:** Non-overlapping 10-minute time slots (600,000 milliseconds).
* **Slots per Day:** Exactly 144 discrete observation windows per 24-hour cycle per cell.
* **Timestamp Representation:** Milliseconds elapsed since Unix Epoch (`1383260400000` = 2013-11-01 00:00:00 CET / 2013-10-31 23:00:00 UTC).

---

## 4. Feature Schema & Data Dictionary

Each line in the daily activity files corresponds to a single CDR aggregate event formatted as an uncompressed, tab-separated record without a header:

| Field Index | Field Name | Data Type | Constraints / Format | Description |
| :---: | :---: | :---: | :---: | :--- |
| **1** | `cell_id` | Integer | `[1, 10000]` | Spatial identifier of the grid cell in the Milan tessellation. |
| **2** | `timestamp` | Long / BigInt | Unix epoch milliseconds | Start of the 10-minute aggregation window. |
| **3** | `country_code` | Integer | ITU-T E.164 (`39` = Italy, `0` = internal/unknown) | Country calling code representing the international origin or destination of the communication. |
| **4** | `sms_in` | Float / Double | Non-negative or Null (`\t\t`) | Directional traffic volume of SMS messages received inside the cell. |
| **5** | `sms_out` | Float / Double | Non-negative or Null (`\t\t`) | Directional traffic volume of SMS messages sent from within the cell. |
| **6** | `call_in` | Float / Double | Non-negative or Null (`\t\t`) | Directional traffic volume of voice calls received inside the cell. |
| **7** | `call_out` | Float / Double | Non-negative or Null (`\t\t`) | Directional traffic volume of voice calls originated from within the cell. |
| **8** | `internet_traffic` | Float / Double | Non-negative or Null (`\t\t`) | Volume of internet CDR traffic events (connections/sessions) logged in the cell. |

### Note on Activity Units & Normalization
Activity values are proportionally normalized by Telecom Italia for competitive privacy and protection of commercial proprietary information. They are dimensionless indices reflecting proportional usage density.

---

## 5. Storage & File Organization

* **Total Daily Files:** 62 files.
* **Naming Scheme:** `sms-call-internet-mi-YYYY-MM-DD.txt` (e.g., `sms-call-internet-mi-2013-11-01.txt`).
* **Total Dataset Size:** 20,804,803,507 bytes (19.38 GB uncompressed).
* **Average Daily File Size:** ~335.5 MB.
* **Delimiter:** Tab character (`\t`).
* **Hadoop Block Allocation:** At default HDFS 128 MB block size, the full dataset spans approximately 152 HDFS blocks, facilitating extensive distributed parallelism.

---

## 6. Dataset Limitations & Engineering Considerations

1. **Sparsity / Missing Metrics:** In activity windows where no traffic was recorded for a specific channel (e.g., zero incoming calls from a particular country code), the field is left empty between adjacent tabs (`\t\t`). In MapReduce mappers, records must be split carefully with boundary-preserving parsers (e.g., `line.split("\t", -1)`) to avoid `ArrayIndexOutOfBoundsException`.
2. **Dimensionless Normalized Metrics:** Because raw counts are obscured into normalized indices, metrics should be analyzed via relative aggregations, standard deviations, distributions, and spatial-temporal rank orderings rather than literal phone call counts.
3. **Anonymized Cell Aggregation:** Records do not contain individual subscriber IDs (IMSI/IMEI) or device hardware identifiers, satisfying privacy constraints and preventing individual tracking while preserving macroeconomic mobility patterns.

---

## 7. Licensing & Attribution

* **License:** Open Database License (ODbL v1.0).
* **Terms of Use:** Users are free to share, modify, and build upon the dataset, provided attribution is given to Telecom Italia and any derivative databases remain available under equivalent open database licensing terms.
* **Attribution Requirement:** "Dataset provided by Telecom Italia under the Open Database License (ODbL 1.0) via Harvard Dataverse (doi:10.7910/DVN/EGZHFV)."

---

## 8. Acquisition & Download Instructions

### Automated Resumable Acquisition (Production)
The project includes a Python ingestion engine (`scripts/download_dataset.py`) that handles Harvard Dataverse Guestbook negotiation, downloads signed URL streams, and verifies MD5 checksums.

```bash
# 1. Generate or verify the dataset download manifest
python scripts/generate_manifest.py

# 2. Download the initial verification file (Day 1: 308 MB)
python scripts/download_dataset.py --limit 1

# 3. Download a specific date
python scripts/download_dataset.py --date 2013-11-01

# 4. Acquire the complete 62-day enterprise archive (19.38 GB)
python scripts/download_dataset.py --all
```

### Manual Download Instructions
If automatic acquisition is prevented by network or proxy restrictions:
1. Open a browser and navigate to: `https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/EGZHFV`
2. Select the **Files** tab.
3. Locate `sms-call-internet-mi-2013-11-01.txt` (or click *Download All*).
4. Fill in the Harvard Dataverse Guestbook prompt (Name, Email, Institution) and accept the ODbL license terms.
5. Save the downloaded `.txt` files directly into the raw data storage folder:
   `telecom-mapreduce/data/raw/`

---

## 9. Verification & Quality Assurance Results

Dataset verification is executed by `scripts/validate_dataset.py`, which validates schema consistency, file size, MD5 checksums, record counts, and anomaly indicators.

* **Reference Manifest:** `data/metadata/download_manifest.csv` (contains all 62 official Harvard Dataverse File IDs, MD5 hashes, and byte sizes).
* **Initial Raw Day Verified:** `data/raw/sms-call-internet-mi-2013-11-01.txt`
  - **File Size:** Exactly `322,874,887 bytes` (307.92 MB).
  - **MD5 Checksum:** `658c49f8e3c7910bd3bb2bafbf62cdce` (100% Match against official Dataverse manifest).
  - **Total Valid Records:** `4,842,625`.
  - **Malformed / Corrupted Records:** `0`.
  - **Time Range (UTC):** `2013-10-31 23:00:00` to `2013-11-01 22:50:00` (144 observation windows of 10-minutes each).
* **Sample Verification:** `data/sample/sms-call-internet-mi-sample.txt` (50,000 authentic records profiled, 0 synthetic records).
* **Summary Reports:** `reports/dataset_summary.json` and `reports/phase1_final_verification.json`.

---

## 10. HDFS Ingestion & Distributed Storage Verification

The authentic Day 1 dataset has been ingested into the Hadoop Distributed File System (HDFS) for distributed MapReduce processing.

### Storage & Transfer Parameters
* **HDFS Destination Path:** `/telecom/data/raw/sms-call-internet-mi-2013-11-01.txt`
* **Local Ingestion Source:** `data/raw/sms-call-internet-mi-2013-11-01.txt` (Original Windows file preserved intact)
* **Transfer Command:** `hdfs dfs -put /mnt/c/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/data/raw/sms-call-internet-mi-2013-11-01.txt /telecom/data/raw/sms-call-internet-mi-2013-11-01.txt`
* **Upload Duration:** `28.85 seconds`
* **Upload Throughput:** `10.67 MB/s`
* **Replication Factor:** `1` (Single-node pseudo-distributed environment)
* **Ingestion Timestamp:** `2026-11-23T17:52:31Z`

### Round-Trip Data Integrity Audit
* **HDFS File Size:** `322,874,887 bytes` (Exact 1:1 byte match with local source)
* **HDFS Internal Checksum:** `MD5-of-262144MD5-of-512CRC32C 00000200000000000004000036717c3ec5380d6b5d21faf9b2adeadc`
* **Streamed HDFS MD5 Checksum:** `658c49f8e3c7910bd3bb2bafbf62cdce` (100% Match against local file and official Dataverse DOI manifest)
* **Streamed HDFS Record Count:** `4,842,625 records` (Exact 1:1 match)
* **Ingestion Telemetry Artifact:** `reports/hdfs_dataset_ingestion.json`

