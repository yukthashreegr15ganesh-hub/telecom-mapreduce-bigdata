# Hadoop Infrastructure Resource Preparation & Architecture Plan

## Executive Overview
* **Project:** Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce
* **Project Location:** `C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce`
* **Phase:** Phase 2.2 – Resource Inspection & Architecture Planning
* **Proposed Architecture:** Ubuntu on WSL2 + Apache Hadoop (3.5.0 / 3.4.0) + OpenJDK 17 + Python 3 Streaming
* **Engineer:** Senior Linux Administrator, Hadoop Architect & Infrastructure Engineer

---

## 1. Storage Analysis & Reclamation Strategy

### Host Storage Status (C: Drive)
* **Total Drive Capacity:** 279.40 GB
* **Used Storage:** 270.02 GB
* **Free Available Space:** **9.38 GB (3.36% headroom)**
* **Assessment:** The C: drive has a tight storage headroom. Infrastructure planning must avoid unbounded disk growth and isolate dynamic allocations.

### Directory Footprints Profile
| Directory / Component | Path | Measured Size | Notes |
| :--- | :--- | :---: | :--- |
| **User Temp** | `C:\Users\Admin\AppData\Local\Temp` | **418.67 MB** | Accumulated application scratch files. |
| **System Temp** | `C:\Windows\Temp` | **13.71 MB** | Windows OS temporary installer logs. |
| **Telecom Workspace** | `C:\Users\Admin\.gemini\...\telecom-mapreduce` | **311.53 MB** | Verified raw dataset (`322.8 MB`) + sample (`3.4 MB`) + code. |
| **Pip Cache** | `C:\Users\Admin\AppData\Local\pip\cache` | **< 1 MB** | Python wheel cache. |
| **NPM Cache** | `C:\Users\Admin\AppData\Local\npm-cache` | **1.11 MB** | Node.js package cache. |
| **Gemini Cache** | `C:\Users\Admin\.gemini` (excluding workspace) | **~18.6 MB** | Assistant tooling and extension configs. |
| **Docker Desktop Data** | `C:\ProgramData\DockerDesktop` | **< 1 MB** | Inactive Docker configurations. |
| **Ubuntu WSL2 Virtual Disk** | Dynamic Virtual Hard Disk (`ext4.vhdx`) | **~6.0 GB** | Internal Ubuntu virtual rootfs. |

### Safe Storage Reclamation Recommendations (Non-Destructive)
1. **WSL2 Sparse VHDX Activation:** In Windows 11 / Build 26300, WSL2 supports the sparse VHDX feature (`wsl --manage Ubuntu --set-sparse true`). This automatically deallocates unwritten virtual disk space back to the Windows host, preventing Ubuntu from inflating C: usage.
2. **Purge User Temp Directory (`%TEMP%`):** Safely removing transient `.tmp` files in `AppData\Local\Temp` can immediately reclaim **~418 MB**.
3. **Windows System Disk Cleanup (`cleanmgr.exe`):** Running Windows Disk Cleanup on Windows Update caches and Delivery Optimization files typically reclaims **2.0 to 5.0 GB** of dormant storage on Windows 10/11 platforms.

---

## 2. Memory & CPU Analysis

### Physical Hardware Memory Profile
* **Total Physical RAM:** **15.71 GB**
* **Available Free RAM:** **3.26 GB (Memory Load: 79%)**
* **Page File Capacity:** 25.71 GB total (3.94 GB available)
* **Processor Architecture:** 16 Logical Cores (x86_64)

### Top Memory Consumer Analysis
Active processes are primarily system background applications, shell terminals (`powershell.exe` ~90 MB), and python runtimes (`python.exe` ~15 MB).

### Feasibility Verdict: **FEASIBLE WITH STRICT HEAP BUDGETING**
The host machine can comfortably support a single-node pseudo-distributed Hadoop environment inside WSL2 under the following constraints:
1. **WSL2 RAM Cap:** Configure `%USERPROFILE%\.wslconfig` with `memory=3GB` and `swap=2GB` to prevent the Linux VM from claiming more than 3 GB of host memory.
2. **Hadoop Daemon Heap Caps:** Configure NameNode and DataNode heaps to `-Xms256m -Xmx512m` each.
3. **MapReduce Memory Caps:** Allocate 512 MB per map/reduce container.

---

## 3. WSL2 Virtualization Feasibility

Inspection of the Windows host subsystem revealed:
* **WSL Engine Version:** `2.6.3.0` (Hyper-V / VirtualMachinePlatform active)
* **Linux Kernel Version:** `6.6.87.2-microsoft-standard-WSL2 x86_64`
* **Installed Distributions:**
  - `Ubuntu` (Default, WSL2, Version **Ubuntu 24.04.3 LTS**) — **ALREADY INSTALLED & FUNCTIONAL**
  - `docker-desktop` (WSL2, Stopped)
* **Environment Status inside Ubuntu:**
  - **Linux Distribution:** Ubuntu 24.04.3 LTS (Noble Numbat)
  - **Existing Java:** OpenJDK `11.0.33` installed at `/usr/lib/jvm/java-1.11.0-openjdk-amd64`
  - **Existing Hadoop:** Apache Hadoop `3.4.0` already deployed at `/opt/hadoop-3.4.0` (symlinked to `/opt/hadoop` and `/usr/local/bin/hadoop`).
  - **Python Runtime:** Python `3.12.3` installed at `/usr/bin/python3`.
  - **Active Daemons:** 0 running HDFS or YARN services.

---

## 4. Resource-Constrained Hadoop 3.5.0 / 3.4.0 Architecture Planning

To process the authentic 322.8 MB telecommunications dataset without exceeding memory or disk thresholds, the following architecture is specified:

```text
+-----------------------------------------------------------------------------------+
|                              WINDOWS HOST (15.7 GB RAM)                          |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                     WSL2 UBUNTU 24.04 VM (Capped at 3.0 GB RAM)             |  |
|  |                                                                             |  |
|  |   +--------------------------+         +--------------------------+         |  |
|  |   |    HDFS NameNode JVM     |         |    HDFS DataNode JVM     |         |  |
|  |   |    -Xms256m -Xmx512m     |         |    -Xms256m -Xmx512m     |         |  |
|  |   +--------------------------+         +--------------------------+         |  |
|  |                 |                                   |                       |  |
|  |                 +-----------------+-----------------+                       |  |
|  |                                   |                                         |  |
|  |                 +-----------------------------------+                       |  |
|  |                 |      Hadoop LocalJobRunner        |                       |  |
|  |                 |      (Zero YARN Daemon Overhead)  |                       |  |
|  |                 |      Map/Reduce: 512 MB Heap      |                       |  |
|  |                 +-----------------------------------+                       |  |
|  |                                   |                                         |  |
|  |                 +-----------------------------------+                       |  |
|  |                 |      Hadoop Streaming Engine      |                       |  |
|  |                 |     Python 3 Mapper & Reducer     |                       |  |
|  |                 +-----------------------------------+                       |  |
|  +-----------------------------------------------------------------------------+  |
|                                      |                                            |
|                 +--------------------+--------------------+                       |
|                 |                                         |                       |
|                 v                                         v                       |
|   +---------------------------+             +---------------------------+         |
|   |   HDFS Virtual Storage    |             | Windows Workspace (Mount) |         |
|   |   /telecom/data/raw/      |             | /mnt/c/.../data/raw/      |         |
|   |   (Single Replica = 1)    |             | (Original Pristine File)  |         |
|   +---------------------------+             +---------------------------+         |
+-----------------------------------------------------------------------------------+
```

### Memory Allocation Budget
* **HDFS NameNode Heap:** `-Xms256m -Xmx512m` (Max 512 MB)
* **HDFS DataNode Heap:** `-Xms256m -Xmx512m` (Max 512 MB)
* **Total HDFS Infrastructure RAM:** **~1024 MB (1.0 GB)**
* **MapReduce Job Execution:** Configured via `LocalJobRunner` (`mapreduce.framework.name = local`).
  - *Engineering Advantage:* LocalJobRunner executes real distributed MapReduce algorithms against HDFS blocks in a single lightweight JVM container, **eliminating 1.5 GB of YARN ResourceManager and NodeManager background memory overhead**.
  - Map task memory: `512 MB`
  - Reduce task memory: `512 MB`
* **Total Peak Stack RAM:** **~1.5 to 1.8 GB**, fitting comfortably inside the 3.26 GB available host memory.

---

## 5. Storage Architecture & Directory Topology

To ensure strict separation of concerns and prevent corruption of raw source data:

| Component | WSL Linux Filesystem Path | Host Windows Path (9P Mount) | Purpose |
| :--- | :--- | :--- | :--- |
| **Hadoop Home** | `/opt/hadoop` (symlink to `/opt/hadoop-3.4.0`) | N/A (Internal to Linux) | Core binaries, JAR libraries, and command scripts. |
| **Hadoop Configuration** | `/opt/hadoop/etc/hadoop` | N/A (Internal to Linux) | `core-site.xml`, `hdfs-site.xml`, `hadoop-env.sh`. |
| **NameNode Metadata** | `/var/hadoop/hdfs/namenode` | N/A (Linux ext4) | HDFS block namespace image (`fsimage`) and edit logs. |
| **DataNode Storage** | `/var/hadoop/hdfs/datanode` | N/A (Linux ext4) | Physical HDFS data block storage (`dfs.replication = 1`). |
| **Hadoop System Logs** | `/var/log/hadoop` | N/A (Linux ext4) | NameNode, DataNode, and audit logs. |
| **Pristine Raw Dataset** | `/mnt/c/Users/Admin/.gemini/.../data/raw` | `C:\Users\Admin\...data\raw` | Original `sms-call-internet-mi-2013-11-01.txt` (Never written to by HDFS). |
| **HDFS Raw Storage** | `hdfs://localhost:9000/telecom/data/raw` | HDFS Virtual Path | Ingested telecom dataset file for MapReduce consumption. |
| **HDFS Job Output** | `hdfs://localhost:9000/telecom/output` | HDFS Virtual Path | Target directory for partitioned MapReduce job outputs. |
| **MapReduce Code** | `/mnt/c/Users/Admin/.../scripts/mapreduce` | `C:\Users\Admin\...scripts\mapreduce` | Python mappers, reducers, and driver scripts. |
| **Reports & Metrics** | `/mnt/c/Users/Admin/.../reports` | `C:\Users\Admin\...reports` | JSON performance profiles and execution audits. |

> [!IMPORTANT]
> **HDFS Storage Isolation Rule:**
> HDFS metadata directories (`/var/hadoop/hdfs/namenode` and `/var/hadoop/hdfs/datanode`) are placed on the native Linux `ext4` filesystem. They are strictly segregated from the Windows workspace and never point to `data/raw/`, preserving raw dataset integrity.

---

## 6. Phase 2.3 Prerequisites Summary

When proceeding to Phase 2.3 upon approval:
1. **WSL Resource Policy:** Create `%USERPROFILE%\.wslconfig` defining `memory=3GB` and `swap=2GB`.
2. **Java Runtime:** Configure `JAVA_HOME=/usr/lib/jvm/java-1.11.0-openjdk-amd64` (or install OpenJDK 17).
3. **Hadoop Configuration:** Configure `core-site.xml` (`fs.defaultFS=hdfs://localhost:9000`), `hdfs-site.xml` (`dfs.replication=1`), and `hadoop-env.sh` (heap constraints).
4. **HDFS Format & Start:** Initialize NameNode (`hdfs namenode -format`) and launch single-node HDFS daemons (`start-dfs.sh`).
5. **Data Ingestion:** Ingest `sms-call-internet-mi-2013-11-01.txt` from `/mnt/c/.../data/raw` into HDFS `/telecom/data/raw/`.

---
*No software has been installed. No system files or environment variables were modified.*
