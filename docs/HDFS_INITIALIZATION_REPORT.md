# Apache Hadoop HDFS Initialization & Cluster Verification Report

**Project:** Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce  
**Environment:** WSL2 (Ubuntu 24.04.3 LTS) on Windows 10/11  
**Hadoop Release:** Apache Hadoop 3.4.0  
**Java Runtime:** OpenJDK 11.0.33 (64-bit Server VM)  
**Verification Date:** November 23, 2026  
**Status:** **INITIALIZED AND OPERATIONAL**

---

## 1. Executive Summary

Phase 2 HDFS storage initialization and daemon bootstrap has been successfully completed. Following explicit user authorization, the NameNode storage directory was formatted in non-interactive mode, creating authentic metadata and a root filesystem image. The HDFS single-node pseudo-distributed daemons (`NameNode` and `DataNode`) have been deployed as managed `systemd` background services, resolving terminal session detachment (`SIGHUP`) challenges common to WSL environments.

The HDFS file system is online, healthy, and accessible at `hdfs://localhost:9000`. The project directory hierarchy has been established with appropriate directory permissions.

---

## 2. Cluster Health & Resource Metrics

| Metric | Measured Value | Description / Status |
| :--- | :--- | :--- |
| **Cluster Status** | `OPERATIONAL` | All core daemons running and responsive |
| **Configured Capacity** | `1,006.85 GB` (1,081,101,176,832 B) | Host disk space available to HDFS |
| **DFS Remaining** | `949.57 GB` (1,019,588,554,752 B) | Available HDFS block storage capacity |
| **DFS Used** | `24 KB` (24,576 B) | Initial filesystem metadata / block pool |
| **DFS Used %** | `0.00%` | Ample headroom for raw telecommunication data |
| **Live DataNodes** | `1` (`127.0.0.1:9866`) | DataNode registered and active |
| **Dead / Decommissioned Nodes**| `0 / 0` | No fault state detected |
| **Replicated Blocks** | `0` | No data blocks written yet |
| **Under-Replicated Blocks** | `0` | Clean block pool |
| **Corrupt / Missing Blocks** | `0 / 0` | 100% block health |

---

## 3. Active Daemons & Port Listeners

### Daemon Process Table (`jps -l`)
```text
412 org.apache.hadoop.hdfs.server.namenode.NameNode
413 org.apache.hadoop.hdfs.server.datanode.DataNode
```

### Network Ports & Endpoints
| Component | Port | Interface | Purpose | Status |
| :--- | :--- | :--- | :--- | :--- |
| **NameNode RPC** | `9000` | `127.0.0.1` | HDFS Client & DataNode IPC (`fs.defaultFS`) | `LISTEN` |
| **NameNode Web UI** | `9870` | `0.0.0.0` | HDFS Web Management Dashboard | `LISTEN` |
| **DataNode Web UI** | `9864` | `0.0.0.0` | DataNode HTTP Web Dashboard | `LISTEN` |
| **DataNode Data Transfer** | `9866` | `0.0.0.0` | Block streaming and replication pipeline | `LISTEN` |
| **DataNode IPC** | `9867` | `0.0.0.0` | DataNode RPC communication | `LISTEN` |

---

## 4. Storage Metadata Verification

### Cluster Identifiers
- **Cluster ID:** `CID-2a46756a-6e64-4cac-9e78-c6d38b2d925f`
- **Block Pool ID:** `BP-620093738-127.0.1.1-1795455466376`
- **Namespace ID:** `1423937088`
- **Layout Version:** NameNode: `-67` | DataNode: `-57`

### Storage Directory Layouts
1. **NameNode Directory:** `/var/hadoop/hdfs/namenode/current`
   - `VERSION` (ClusterID and BlockPoolID recorded)
   - `fsimage_0000000000000000000` + `.md5` (Initial checkpoint image)
   - `edits_inprogress_0000000000000000010` (Active journal)
   - `seen_txid` (Transaction tracker: `3`)

2. **DataNode Directory:** `/var/hadoop/hdfs/datanode/current/BP-620093738-127.0.1.1-1795455466376/current`
   - `VERSION` matches NameNode BlockPool ID and Cluster ID.
   - `scanner.cursor` active.

---

## 5. HDFS Project Directory Tree

The HDFS directory layout has been provisioned according to the big data engineering architecture specifications:

```text
/telecom
├── data/
│   ├── raw/         # Target for genuine Telecom Italia raw CDR/telecom datasets
│   └── processed/   # Target for cleaned, partitioned, and preprocessed datasets
├── output/          # Destination for MapReduce job outputs
└── results/         # Target for aggregated analytic metrics, reports, and KPIs
```

### Verified File Listing (`hdfs dfs -ls -R /telecom`)
```text
drwxr-xr-x   - dminmlops supergroup          0 2026-11-23 17:45 /telecom/data
drwxr-xr-x   - dminmlops supergroup          0 2026-11-23 17:45 /telecom/data/processed
drwxr-xr-x   - dminmlops supergroup          0 2026-11-23 17:45 /telecom/data/raw
drwxr-xr-x   - dminmlops supergroup          0 2026-11-23 17:45 /telecom/output
drwxr-xr-x   - dminmlops supergroup          0 2026-11-23 17:45 /telecom/results
```

---

## 6. Architecture & Process Management Note

### WSL2 Session Isolation & Lingering
In WSL2, ephemeral subshell sessions (`wsl.exe -e bash -c ...`) terminate their pty on completion. Because Hadoop registers custom signal handlers for `SIGHUP` and triggers graceful shutdown upon receipt, launching daemons using traditional backgrounding inside ephemeral WSL sessions caused the processes to shut down.

To ensure production reliability:
1. User lingering was enabled via `loginctl enable-linger dminmlops`.
2. Dedicated systemd unit services (`hadoop-namenode.service` and `hadoop-datanode.service`) were provisioned under `/etc/systemd/system/`.
3. Memory heap limits (`-Xms256m -Xmx512m` per daemon, total ~1 GB) are strictly preserved.
4. Services remain fully detached, highly stable, and persistent across host shell commands.

---

## 7. Next Steps & Phase Progression

- **Data Ingestion (Phase 3 Pre-requisite):** Ready to ingest verified authentic dataset `data/raw/sms-call-internet-mi-2013-11-01.txt` (322,874,887 bytes) into HDFS at `/telecom/data/raw/`.
- **Status:** **STOPPING AS INSTRUCTED.** Awaiting user review and authorization prior to initiating Phase 3.
