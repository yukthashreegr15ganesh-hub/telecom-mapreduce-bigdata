# Big Data Infrastructure & Hadoop Environment Audit

## Project Details
* **Project Name:** Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce
* **Project Location:** `C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce`
* **Phase:** Phase 2.1 – Read-Only Environment Inspection & Architecture Assessment
* **Audit Execution Time:** November 23, 2026 (Local Time: 22:38 IST / UTC: 17:08)
* **Engineer:** Senior Hadoop Administrator, Big Data Architect & Distributed Systems Engineer

---

## 1. Operating System & Hardware Inspection

| Specification | Inspection Finding | Engineering Assessment |
| :--- | :--- | :--- |
| **Operating System** | Windows 10 Home Single Language (Platform: Windows-10-10.0.26300-SP0) | 64-bit Windows client platform (Build 26300 / 26H2 release). |
| **System Architecture** | `AMD64` (x86_64) | Standard 64-bit architecture compatible with all Hadoop & JDK distributions. |
| **Logical Processors** | **16 Cores** | Substantial CPU capacity for multi-threaded map/reduce task concurrency. |
| **Total Physical RAM** | **15.71 GB** (16,873,545,728 bytes) | Ample total hardware capacity. |
| **Available Free RAM** | **2.65 GB** (2,849,931,264 bytes) | **High Memory Load (83%)**. Daemons and JVMs must be tuned with strict memory limits (`-Xmx1024m`). |
| **Disk Storage (C:)** | Total: **279.40 GB** \| Used: **269.84 GB** \| Free: **9.57 GB** (3.42% free) | **CRITICAL CONSTRAINT**: Limited storage headroom. Virtual machine disk provisioning (`vhdx`) must be avoided. |
| **Shell / CLI** | PowerShell Version `5.1.26100.9818` | Windows native automation shell. |

---

## 2. Java Runtime & Development Kit Inspection

| Property | Inspection Finding | Status / Compatibility Analysis |
| :--- | :--- | :--- |
| **Java Installed** | **Yes** | Active on system PATH. |
| **Java Version** | `openjdk version "25.0.4" 2026-07-21 LTS` | **INCOMPATIBLE WITH HADOOP 3.x**. |
| **Java Vendor** | Eclipse Adoptium Temurin (`build 25.0.4+7-LTS, mixed mode, sharing`) | 64-bit Hotspot VM. |
| **Java Binary Location** | `C:\Program Files\Eclipse Adoptium\jdk-25.0.4.7-hotspot\bin\java.exe` | Detected via `where.exe java`. |
| **Java Compiler (`javac`)** | `javac 25.0.4` (`C:\Program Files\Eclipse Adoptium\jdk-25.0.4.7-hotspot\bin\javac.exe`) | Compiler is available. |
| **`JAVA_HOME` Variable** | **NOT SET** (Empty) | Required by Hadoop startup scripts. |
| **Multiple JDKs on Disk** | Only 1 JDK installation detected (`Eclipse Adoptium jdk-25.0.4.7-hotspot`). | No legacy Java 8 or Java 11 JDKs currently exist on host. |

> [!WARNING]
> **Java Version Incompatibility Hazard:**
> Apache Hadoop (including the latest 3.3.x and 3.4.0 releases) officially supports **Java 8 (JDK 1.8) and Java 11**. Hadoop relies extensively on low-level JVM internals (`sun.misc.Unsafe`, direct memory buffer access, reflection into `java.nio.DirectByteBuffer`, and security managers). Running Hadoop daemons or native MapReduce jobs on Java 25 triggers immediate fatal reflection access exceptions and illegal reflective access blocks. A dedicated Java 8 or Java 11 runtime must be provisioned.

---

## 3. Apache Hadoop Status

| Property | Inspection Finding | Status |
| :--- | :--- | :--- |
| **Hadoop Installed** | **No** | Binary not found on system. |
| **`HADOOP_HOME`** | **NOT SET** | Missing from environment. |
| **`HADOOP_CONF_DIR`** | **NOT SET** | Missing from environment. |
| **Hadoop Binaries** | None found on PATH or in common paths (`C:\hadoop`, `C:\tools\hadoop`). | Clean slate for fresh deployment. |
| **Existing Configuration** | No pre-existing `core-site.xml`, `hdfs-site.xml`, `mapred-site.xml`, or `yarn-site.xml`. | No risk of legacy configuration collisions. |

---

## 4. Supporting Tooling & Dependencies

| Tool / Dependency | Version / Status | Assessment |
| :--- | :--- | :--- |
| **Python** | `Python 3.10.11` | **Available**. Fully compatible with Hadoop Streaming MapReduce and PySpark. |
| **Git** | `git version 2.53.0.windows.1` | **Available**. Ready for source version control. |
| **Apache Maven (`mvn`)** | **Not installed / Not on PATH** | Required if compiling custom Java MapReduce JARs from source. |
| **Windows Binaries (`winutils.exe`)** | **Not installed** | Required for native Windows Hadoop execution (POSIX simulation). |
| **WSL (Windows Subsystem for Linux)**| **Not configured / No registered distributions** | Cannot run Linux workloads without distro installation. |
| **Docker Engine** | `Docker version 29.7.2, build a7dcaa6` (Daemon currently **STOPPED**) | Engine installed, but daemon is inactive. |
| **Active HDFS Processes** | **0 running processes** (`jps` returned only its own PID). | No conflicting Hadoop ports or locks. |

---

## 5. Architectural Compatibility & Deployment Evaluation

We evaluated three potential deployment models against the specific constraints of this machine:

### Option A: Native Windows Hadoop (Pseudo-Distributed / Local Mode)
* **Mechanics:** Apache Hadoop 3.3.6 binaries running directly on Windows with `winutils.exe` and `hadoop.dll` under a scoped Java 11 runtime.
* **Resource Footprint:** **Lowest (~1.2 GB disk, ~1.0 GB RAM)**.
* **Storage Feasibility:** Excellent. Fits safely inside the 9.57 GB available disk space without risking OS starvation.
* **Memory Feasibility:** Excellent. Single-node local MapReduce runner or scoped JVM instances can be capped at `-Xmx1024m`, fitting cleanly within the 2.65 GB free RAM.
* **Operational Considerations:** Requires handling Windows path quoting (avoiding spaces in paths like `Program Files`) and placing matching `winutils.exe` in `%HADOOP_HOME%\bin`.

### Option B: Hadoop via WSL2 (Ubuntu Linux)
* **Mechanics:** Provisioning an Ubuntu 22.04/24.04 WSL2 virtual machine, installing OpenJDK 11, and configuring Linux native Hadoop.
* **Resource Footprint:** **High (~6–10 GB disk for `ext4.vhdx`, ~4–6 GB RAM for `vmmem`)**.
* **Storage Feasibility:** **CRITICAL RISK**. WSL2 dynamically allocates a virtual hard disk that immediately consumes 4–8 GB of host disk space. With only 9.57 GB remaining on C:, running WSL2 risks **100% disk exhaustion**, causing Windows crash dumps.
* **Memory Feasibility:** **HIGH RISK**. WSL2 default configuration reserves 50% of host RAM (8 GB). Given only 2.65 GB available RAM, the host will immediately enter heavy paging and disk thrashing.

### Option C: Hadoop via Docker Container
* **Mechanics:** Running unified or multi-container Hadoop clusters (NameNode, DataNode, ResourceManager) via Docker Compose.
* **Resource Footprint:** **Highest (~5–8 GB Docker image layers + volumes, ~3–5 GB RAM)**.
* **Storage Feasibility:** **CRITICAL RISK**. Pulling full Hadoop multi-node images will exceed the 9.57 GB storage threshold.
* **Memory Feasibility:** **HIGH RISK**. Docker Desktop on Windows requires WSL2 or Hyper-V, compounding the memory exhaustion issue.

---

## 6. Recommended Deployment Architecture

### **Recommendation: Portable Scoped Native Hadoop (Option A)**
To ensure maximum reliability without risking host disk saturation or memory starvation:

1. **Dedicated Java Runtime:** Provision a portable, non-intrusive OpenJDK 11 distribution (e.g., Eclipse Adoptium Temurin 11 or Corretto 11) scoped to the project or standard path, leaving the system's Java 25 undisturbed for other applications.
2. **Hadoop Binary Distribution:** Deploy Apache Hadoop 3.3.6 with matching, community-verified `winutils.exe` and `hadoop.dll` (x64 architecture).
3. **Execution Modes:**
   - **Local Job Runner (Development & Rapid Prototyping):** High-speed in-process MapReduce testing on the verified 50,000-record sample without daemon overhead.
   - **Pseudo-Distributed HDFS Cluster (Production Pipeline):** Configured with single-replica HDFS (`dfs.replication = 1`) and strict JVM heap caps (`HADOOP_HEAPSIZE_MAX=1024`) to process the complete 322.8 MB raw dataset cleanly inside memory limits.
4. **Zero Global Pollution:** Maintain all configurations in project-level scripts (`config/`) and local path definitions, avoiding disruptive modifications to global Windows environment variables.

---

## 7. Missing Dependencies Summary (Prerequisites for Phase 2.2)

To advance to installation upon user approval, the following components are required:
1. **Java 11 (JDK 11 x64):** Required for Hadoop 3.x runtime compatibility (replaces Java 25 for Hadoop tasks).
2. **Apache Hadoop 3.3.6 Binary Archive (`hadoop-3.3.6.tar.gz`):** Core framework binaries.
3. **Windows Native Utilities (`winutils.exe` & `hadoop.dll` for Hadoop 3.3.6):** Required for Windows POSIX simulation.
4. **Apache Maven (Optional / Recommended):** If building custom Java MapReduce jobs; alternatively, Python Hadoop Streaming can execute immediately without Maven.

---

*End of Environment Audit Report. No software installed. System state remains unmodified.*
