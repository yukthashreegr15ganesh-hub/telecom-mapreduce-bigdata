# Hadoop Configuration & Environment Verification Guide

## Executive Overview
* **Project:** Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce
* **Project Workspace:** `C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce`
* **Target Environment:** Windows 10/11 + WSL2 + Ubuntu 24.04.3 LTS (Noble Numbat)
* **Configuration State:** Successfully Deployed & Validated
* **Status:** **STOPPED & WAITING FOR APPROVAL BEFORE HDFS FORMATTING**

---

## 1. Updated Configuration Files

### A. `core-site.xml` (`/opt/hadoop/etc/hadoop/core-site.xml`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
        <description>Default file system URI for HDFS NameNode</description>
    </property>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/var/hadoop/tmp</value>
        <description>Base directory for temporary Hadoop runtime files</description>
    </property>
</configuration>
```

### B. `hdfs-site.xml` (`/opt/hadoop/etc/hadoop/hdfs-site.xml`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
        <description>Single-node block replication factor</description>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>file:///var/hadoop/hdfs/namenode</value>
        <description>Directory for NameNode metadata storage (fsimage and edits)</description>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>file:///var/hadoop/hdfs/datanode</value>
        <description>Directory for DataNode block storage</description>
    </property>
    <property>
        <name>dfs.permissions.enabled</name>
        <value>false</value>
        <description>Disable permission checking for single-node local development</description>
    </property>
</configuration>
```

### C. `mapred-site.xml` (`/opt/hadoop/etc/hadoop/mapred-site.xml`)
```xml
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>mapreduce.framework.name</name>
        <value>local</value>
        <description>Execution framework set to LocalJobRunner (in-process MapReduce engine reading/writing directly from HDFS)</description>
    </property>
    <property>
        <name>mapreduce.job.maps</name>
        <value>2</value>
        <description>Concurrent local mapper threads</description>
    </property>
    <property>
        <name>mapreduce.job.reduces</name>
        <value>1</value>
        <description>Concurrent local reducer tasks</description>
    </property>
</configuration>
```

### D. `hadoop-env.sh` (`/opt/hadoop/etc/hadoop/hadoop-env.sh`)
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/opt/hadoop
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export HADOOP_LOG_DIR=/var/log/hadoop

# Conservative JVM Heap Allocations
export HADOOP_HEAPSIZE_MAX=1024m
export HADOOP_NAMENODE_OPTS="-Xms256m -Xmx512m $HADOOP_NAMENODE_OPTS"
export HADOOP_DATANODE_OPTS="-Xms256m -Xmx512m $HADOOP_DATANODE_OPTS"
```

---

## 2. Technical MapReduce Execution Mode Evaluation

Per engineering rigor, execution frameworks are defined accurately:

* **LocalJobRunner (`mapreduce.framework.name = local`):**
  - **Mechanics:** An in-process MapReduce engine running on the client node within a single JVM. It reads splits directly from HDFS blocks (`hdfs://localhost:9000/...`) and streams outputs directly to HDFS, but task scheduling and execution are handled by a multi-threaded local runner rather than independent distributed worker daemons.
  - **Memory Footprint:** ~512 MB client heap. Zero background daemon memory consumption.
  - **Selection Rationale:** Selected as the primary execution mode for this resource-constrained environment (3.26 GB available host RAM), saving ~1.5 to 2.0 GB of YARN daemon overhead.
* **YARN (`mapreduce.framework.name = yarn`):**
  - **Mechanics:** True distributed container execution engine requiring ResourceManager, NodeManager, and ApplicationMaster daemons.
  - **Memory Footprint:** > 2.5 GB RAM. Reserved for environments with > 6 GB free RAM.

---

## 3. Storage Hierarchy & Permissions Matrix

| Filesystem Path | Owner:Group | Mode | Purpose |
| :--- | :--- | :---: | :--- |
| `/var/hadoop/hdfs/namenode` | `dminmlops:dminmlops` | `700` (`drwx------`) | Isolated NameNode metadata storage (`fsimage` & `edits`). |
| `/var/hadoop/hdfs/datanode` | `dminmlops:dminmlops` | `700` (`drwx------`) | Isolated DataNode block storage. |
| `/var/hadoop/tmp` | `dminmlops:dminmlops` | `777` (`drwxrwxrwx`) | Shared temporary runtime files. |
| `/var/log/hadoop` | `dminmlops:dminmlops` | `755` (`drwxr-xr-x`) | Hadoop daemon logging directory. |
| `/opt/hadoop/etc/hadoop_backup_clean` | `dminmlops:dminmlops` | `755` | Pristine backup of unconfigured templates. |

---

## 4. Configuration Verification Results

Command outputs from official Hadoop validation tools:

1. **XML Schema Integrity (`hadoop conftest`):**
   ```text
   /opt/hadoop/etc/hadoop/core-site.xml: valid
   /opt/hadoop/etc/hadoop/hdfs-site.xml: valid
   /opt/hadoop/etc/hadoop/mapred-site.xml: valid
   /opt/hadoop/etc/hadoop/yarn-site.xml: valid
   OK
   ```
2. **HDFS Keys Query (`hdfs getconf`):**
   - `fs.defaultFS`: `hdfs://localhost:9000`
   - `dfs.replication`: `1`
   - `dfs.namenode.name.dir`: `file:///var/hadoop/hdfs/namenode`
   - `dfs.datanode.data.dir`: `file:///var/hadoop/hdfs/datanode`
3. **Native Libraries (`hadoop checknative`):**
   - Hadoop native library: `true /opt/hadoop-3.4.0/lib/native/libhadoop.so.1.0.0`
   - zlib compression: `true /lib/x86_64-linux-gnu/libz.so.1`
   - zstd compression: `true /lib/x86_64-linux-gnu/libzstd.so.1`
   - bzip2 compression: `true /lib/x86_64-linux-gnu/libbz2.so.1`

---

## 5. Detected Issues & Resolutions

| Issue Detected | Root Cause | Engineering Resolution |
| :--- | :--- | :--- |
| **`bin/mapred` and `bin/yarn` script errors** | The files contained 14-byte `404: Not Found` text from an earlier broken download. | Restored the authentic Apache Hadoop 3.4.0 `mapred` and `yarn` scripts directly from the official Apache Git release tag (`rel/release-3.4.0`) and confirmed execution via `mapred` and `yarn version`. |
| **Missing directory permissions** | `/var/hadoop` and `/var/log/hadoop` did not exist. | Created directories with strict permissions (`700` for HDFS storage, `755` for logs) and assigned ownership to user `dminmlops`. |

---
*The environment is fully configured and validated. HDFS formatting has not been executed.*
