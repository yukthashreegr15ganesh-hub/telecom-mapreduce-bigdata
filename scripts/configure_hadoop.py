import subprocess
import json
import os
import sys

WORKSPACE_CONF_DIR = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\config\hadoop"
REPORT_FILE = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\reports\hadoop_configuration_report.json"

def run_wsl(bash_cmd, as_root=False):
    cmd = ["wsl.exe"]
    if as_root:
        cmd.extend(["-u", "root"])
    cmd.extend(["-d", "Ubuntu", "-e", "bash", "-c", bash_cmd])
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

CORE_SITE_XML = """<?xml version="1.0" encoding="UTF-8"?>
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
"""

HDFS_SITE_XML = """<?xml version="1.0" encoding="UTF-8"?>
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
"""

MAPRED_SITE_XML = """<?xml version="1.0"?>
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
"""

HADOOP_ENV_SH_ADDITIONS = """
# ====================================================================
# TELECOM MAPREDUCE RESOURCE-CONSTRAINED SINGLE-NODE CONFIGURATION
# ====================================================================
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/opt/hadoop
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export HADOOP_LOG_DIR=/var/log/hadoop

# Conservative JVM Heap Allocations
export HADOOP_HEAPSIZE_MAX=1024m
export HADOOP_NAMENODE_OPTS="-Xms256m -Xmx512m $HADOOP_NAMENODE_OPTS"
export HADOOP_DATANODE_OPTS="-Xms256m -Xmx512m $HADOOP_DATANODE_OPTS"
"""

def execute_configuration():
    print("=" * 70)
    print("EXECUTING HADOOP 3.4.0 CONFIGURATION FOR SINGLE-NODE HDFS")
    print("=" * 70)

    report = {"tasks": {}, "validations": {}}

    # 1. Back up existing configuration
    print("\n[STEP 1] Backing up existing /opt/hadoop/etc/hadoop...")
    backup_script = """
    if [ ! -d "/opt/hadoop/etc/hadoop_backup_clean" ]; then
        cp -r /opt/hadoop/etc/hadoop /opt/hadoop/etc/hadoop_backup_clean
        echo "Created backup at /opt/hadoop/etc/hadoop_backup_clean"
    else
        echo "Backup already exists at /opt/hadoop/etc/hadoop_backup_clean"
    fi
    ls -d /opt/hadoop/etc/hadoop_backup_clean
    """
    code, out, err = run_wsl(backup_script, as_root=True)
    report["tasks"]["backup"] = {"exit_code": code, "stdout": out, "stderr": err}
    print(f"Backup Status: {out}")

    # 2. Create Required Storage Directories and Set Ownership
    print("\n[STEP 2] Creating storage directories and setting permissions...")
    dir_script = """
    mkdir -p /var/hadoop/hdfs/namenode
    mkdir -p /var/hadoop/hdfs/datanode
    mkdir -p /var/hadoop/tmp
    mkdir -p /var/log/hadoop

    chown -R dminmlops:dminmlops /var/hadoop /var/log/hadoop /opt/hadoop /opt/hadoop-3.4.0
    chmod 700 /var/hadoop/hdfs/namenode /var/hadoop/hdfs/datanode
    chmod 777 /var/hadoop/tmp
    chmod 755 /var/log/hadoop
    ls -la /var/hadoop /var/hadoop/hdfs
    """
    code, out, err = run_wsl(dir_script, as_root=True)
    report["tasks"]["directories"] = {"exit_code": code, "stdout": out, "stderr": err}
    print(f"Directory Creation Status:\n{out}")

    # 3. Save workspace backup copies
    print("\n[STEP 3] Staging configuration copies in project workspace...")
    os.makedirs(WORKSPACE_CONF_DIR, exist_ok=True)
    with open(os.path.join(WORKSPACE_CONF_DIR, "core-site.xml"), "w", encoding="utf-8") as f:
        f.write(CORE_SITE_XML)
    with open(os.path.join(WORKSPACE_CONF_DIR, "hdfs-site.xml"), "w", encoding="utf-8") as f:
        f.write(HDFS_SITE_XML)
    with open(os.path.join(WORKSPACE_CONF_DIR, "mapred-site.xml"), "w", encoding="utf-8") as f:
        f.write(MAPRED_SITE_XML)
    with open(os.path.join(WORKSPACE_CONF_DIR, "hadoop-env-telecom.sh"), "w", encoding="utf-8") as f:
        f.write(HADOOP_ENV_SH_ADDITIONS)
    print(f"Configurations saved to workspace: {WORKSPACE_CONF_DIR}")

    # 4. Deploy XML Configurations to /opt/hadoop/etc/hadoop
    print("\n[STEP 4] Deploying configuration XMLs to /opt/hadoop/etc/hadoop/...")
    deploy_script = f"""
    cat << 'EOF' > /opt/hadoop/etc/hadoop/core-site.xml
{CORE_SITE_XML}
EOF

    cat << 'EOF' > /opt/hadoop/etc/hadoop/hdfs-site.xml
{HDFS_SITE_XML}
EOF

    cat << 'EOF' > /opt/hadoop/etc/hadoop/mapred-site.xml
{MAPRED_SITE_XML}
EOF

    # Update hadoop-env.sh safely
    if ! grep -q "TELECOM MAPREDUCE" /opt/hadoop/etc/hadoop/hadoop-env.sh; then
        cat << 'EOF' >> /opt/hadoop/etc/hadoop/hadoop-env.sh
{HADOOP_ENV_SH_ADDITIONS}
EOF
    fi

    # Update ~/.bashrc for user dminmlops if not already set
    if ! grep -q "HADOOP_HOME=/opt/hadoop" /home/dminmlops/.bashrc; then
        cat << 'EOF' >> /home/dminmlops/.bashrc

# Hadoop Environment Variables
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/opt/hadoop
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
EOF
    fi

    chown -R dminmlops:dminmlops /opt/hadoop/etc/hadoop /home/dminmlops/.bashrc
    """
    code, out, err = run_wsl(deploy_script, as_root=True)
    report["tasks"]["deployment"] = {"exit_code": code, "stdout": out, "stderr": err}
    print(f"Deployment result: exit code {code}")

    # 5. Validate Configuration Using Hadoop Commands
    print("\n[STEP 5] Validating configurations using Hadoop inspection commands...")
    validation_script = """
    echo "--- FS_DEFAULT_FS ---"
    hdfs getconf -confKey fs.defaultFS
    echo "--- DFS_REPLICATION ---"
    hdfs getconf -confKey dfs.replication
    echo "--- DFS_NAMENODE_NAME_DIR ---"
    hdfs getconf -confKey dfs.namenode.name.dir
    echo "--- DFS_DATANODE_DATA_DIR ---"
    hdfs getconf -confKey dfs.datanode.data.dir
    echo "--- MAPREDUCE_FRAMEWORK ---"
    mapred getconf -confKey mapreduce.framework.name
    echo "--- HADOOP CHECKNATIVE ---"
    hadoop checknative 2>&1
    echo "--- CHECK JAVA_HOME ---"
    source /opt/hadoop/etc/hadoop/hadoop-env.sh
    echo "Resolved JAVA_HOME: $JAVA_HOME"
    $JAVA_HOME/bin/java -version 2>&1 | head -n 1
    """
    code, out, err = run_wsl(validation_script, as_root=False)
    report["validations"]["hadoop_getconf"] = {"exit_code": code, "stdout": out, "stderr": err}
    print(out)

    # Save summary report
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 70)
    print("CONFIGURATION & VALIDATION COMPLETE")
    print(f"Report saved to: {REPORT_FILE}")
    print("=" * 70)

if __name__ == "__main__":
    execute_configuration()
