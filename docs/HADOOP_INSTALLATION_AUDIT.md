# Hadoop Installation & Existing Configuration Audit

## Executive Summary
* **Project:** Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce
* **Project Workspace:** `C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce`
* **Target Environment:** Windows 10/11 + WSL2 + Ubuntu 24.04.3 LTS (Noble Numbat)
* **Phase:** Phase 2.3 – Existing Installation & Configuration Audit
* **Audit Mode:** Strictly Read-Only (0 files modified, 0 services started, 0 format operations executed)
* **Engineer:** Senior Hadoop Administrator & Distributed Systems Engineer

---

## 1. Java Environment Audit (WSL2 Ubuntu)

| Audit Check | Command Executed | Result / Output |
| :--- | :--- | :--- |
| **Java Runtime Version** | `java -version` | `openjdk version "11.0.33" 2026-10-20` |
| **Java Build / Vendor** | `java -version` | OpenJDK Runtime Environment (`build 11.0.33+9-post-1ubuntu1-24.04.1-Ubuntu`) |
| **Java Compiler Version** | `javac -version` | `javac 11.0.33` (Available) |
| **Binary Location** | `which java` | `/usr/bin/java` |
| **Resolved Symlink Target**| `readlink -f $(which java)` | `/usr/lib/jvm/java-11-openjdk-amd64/bin/java` |
| **Actual `JAVA_HOME` Path**| `dirname $(dirname ...)` | **`/usr/lib/jvm/java-11-openjdk-amd64`** |
| **Global `$JAVA_HOME`** | `echo $JAVA_HOME` | Empty in global interactive shell (Handled explicitly in `hadoop-env.sh`) |

---

## 2. Hadoop Installation & Binary Hierarchy Audit

| Audit Check | Inspection Target | Verified Result |
| :--- | :--- | :--- |
| **Hadoop Core Version** | `hadoop version` | **Apache Hadoop 3.4.0** (Built 2024-03-04T06:35Z, checksum `f7fe694a3613358b38812ae9c31114e`) |
| **Hadoop Command Path** | `which hadoop` | `/usr/local/bin/hadoop` |
| **Base Installation Directory**| `/opt/hadoop-3.4.0` | Pristine extracted Apache Hadoop 3.4.0 binary release tree |
| **Standard Symlink** | `/opt/hadoop` | Active symlink pointing to `/opt/hadoop-3.4.0` (`lrwxrwxrwx 1 root root 17 Nov 16 15:18 /opt/hadoop -> /opt/hadoop-3.4.0`) |
| **Binaries Directory** | `/opt/hadoop-3.4.0/bin/` | Includes `hadoop`, `hdfs`, `mapred`, `yarn`, `container-executor`, `oom-listener` |
| **Administration Scripts** | `/opt/hadoop-3.4.0/sbin/` | Includes `start-dfs.sh`, `stop-dfs.sh`, `start-all.sh`, `hadoop-daemon.sh` |
| **HDFS Libraries** | `/opt/hadoop/share/hadoop/hdfs/` | `hadoop-hdfs-3.4.0.jar`, `hadoop-hdfs-client-3.4.0.jar` |
| **MapReduce Libraries** | `/opt/hadoop/share/hadoop/mapreduce/` | `hadoop-mapreduce-client-core-3.4.0.jar`, `hadoop-mapreduce-client-common-3.4.0.jar` |
| **Streaming Engine** | `/opt/hadoop/share/hadoop/tools/lib/` | **`hadoop-streaming-3.4.0.jar` (141,771 bytes)** |

---

## 3. Existing Configuration XML Audit (`/opt/hadoop/etc/hadoop/`)

All site configuration XML files were inspected for existing customizations:

1. **`core-site.xml`**:
   - Status: **Default Template**
   - Content: `<configuration>\n</configuration>` (No custom properties defined).
2. **`hdfs-site.xml`**:
   - Status: **Default Template**
   - Content: `<configuration>\n\n</configuration>` (No custom properties defined).
3. **`mapred-site.xml`**:
   - Status: **Default Template**
   - Content: `<configuration>\n\n</configuration>` (No custom properties defined).
4. **`yarn-site.xml`**:
   - Status: **Default Template**
   - Content: `<configuration>\n\n<!-- Site specific YARN configuration properties -->\n\n</configuration>`.
5. **`hadoop-env.sh`**:
   - Status: Pre-configured with:
     ```bash
     export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
     ```
   - No daemon heap limits or memory caps have been applied yet.

---

## 4. HDFS State & Metadata Audit

* **NameNode Metadata Check:**
  - Scanned `/tmp` for `dfs/name`, `fsimage*`, `edits*` — **0 records found**.
  - Scanned `/var/hadoop` and `/var/data` — **Directories do not exist**.
* **Cluster Identification (`VERSION` file):**
  - No cluster ID, layout version, or block pool ID files exist anywhere on the filesystem.
* **Active Daemons (`jps -l`):**
  - Result: Only `jdk.jcmd/sun.tools.jps.Jps` active.
  - NameNode (`org.apache.hadoop.hdfs.server.namenode.NameNode`): **INACTIVE**
  - DataNode (`org.apache.hadoop.hdfs.server.datanode.DataNode`): **INACTIVE**
  - SecondaryNameNode: **INACTIVE**
  - ResourceManager / NodeManager: **INACTIVE**
* **Active Network Ports (`ss -tulpn`):**
  - Port 9000 (HDFS IPC): **FREE**
  - Port 9870 (NameNode Web UI): **FREE**
  - Port 9864 (DataNode Web UI): **FREE**
  - Port 8088 (YARN Web UI): **FREE**
* **HDFS State Assessment:** **UNINITIALIZED & UNFORMATTED**. The filesystem is in a completely fresh state ready for initial formatting in Phase 2.4.

---

## 5. Hadoop Streaming & Python Environment Audit

* **Streaming JAR Location:** `/opt/hadoop-3.4.0/share/hadoop/tools/lib/hadoop-streaming-3.4.0.jar`
* **Python Runtime:** `/usr/bin/python3` (`Python 3.12.3`)
* **Execution Compatibility:**
  - Python standard I/O streams (`sys.stdin`, `sys.stdout`) are natively accessible without external dependencies.
  - Streaming execution command syntax verified:
    ```bash
    hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.4.0.jar \
      -input /telecom/data/raw/sms-call-internet-mi-2013-11-01.txt \
      -output /telecom/output \
      -mapper "/usr/bin/python3 mapper.py" \
      -reducer "/usr/bin/python3 reducer.py" \
      -file mapper.py \
      -file reducer.py
    ```

---

## 6. Lightweight Resource Configuration Plan (Phase 2.4 Blueprint)

Based on host available RAM (3.26 GB) and free disk space (9.38 GB):

### Daemon Heap Limits (`hadoop-env.sh`)
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HEAPSIZE_MAX=1024m
export HADOOP_NAMENODE_OPTS="-Xms256m -Xmx512m $HADOOP_NAMENODE_OPTS"
export HADOOP_DATANODE_OPTS="-Xms256m -Xmx512m $HADOOP_DATANODE_OPTS"
```

### Core Configuration (`core-site.xml`)
```xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
        <description>Default HDFS filesystem URI</description>
    </property>
</configuration>
```

### HDFS Configuration (`hdfs-site.xml`)
```xml
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
        <description>Single-node replication factor</description>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>file:///var/hadoop/hdfs/namenode</value>
        <description>Isolated NameNode fsimage and edits storage</description>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>file:///var/hadoop/hdfs/datanode</value>
        <description>Isolated DataNode block storage</description>
    </property>
</configuration>
```

### MapReduce Engine (`mapred-site.xml`)
```xml
<configuration>
    <property>
        <name>mapreduce.framework.name</name>
        <value>local</value>
        <description>LocalJobRunner execution against HDFS (zero YARN daemon overhead)</description>
    </property>
</configuration>
```

---

## 7. Configuration Backup Strategy (Pre-requisite for Phase 2.4)
Before any configuration edits are performed in Phase 2.4, an automated backup of `/opt/hadoop/etc/hadoop` will be created at:
`/opt/hadoop/etc/hadoop_backup_clean/`

---
*End of Audit Report. No configuration files were overwritten. NameNode was not formatted. No daemons were started.*
