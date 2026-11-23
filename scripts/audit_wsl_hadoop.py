import subprocess
import json
import os

AUDIT_REPORT_PATH = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\reports\hadoop_installation_audit.json"

def run_wsl_cmd(bash_script):
    cmd = ["wsl.exe", "-d", "Ubuntu", "-e", "bash", "-c", bash_script]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def audit():
    print("=" * 70)
    print("STARTING HADOOP INSTALLATION & CONFIGURATION AUDIT IN WSL2")
    print("=" * 70)

    results = {}

    # TASK 1: Verify Java
    print("\n[TASK 1] Auditing Java Environment in Ubuntu...")
    java_script = """
    echo "--- JAVA_VERSION ---"
    java -version 2>&1
    echo "--- JAVAC_VERSION ---"
    javac -version 2>&1
    echo "--- JAVA_HOME_ENV ---"
    echo "$JAVA_HOME"
    echo "--- WHICH_JAVA ---"
    which java
    echo "--- READLINK_JAVA ---"
    readlink -f $(which java)
    echo "--- JVM_PARENT_DIR ---"
    dirname $(dirname $(readlink -f $(which java)))
    """
    code, out, err = run_wsl_cmd(java_script)
    results["task1_java_audit"] = {
        "exit_code": code,
        "raw_output": out,
        "error_output": err
    }
    print(out)

    # TASK 2: Verify Hadoop Installation & Directories
    print("\n[TASK 2] Auditing Hadoop Installation & Binaries...")
    hadoop_script = """
    echo "--- HADOOP_VERSION ---"
    hadoop version
    echo "--- WHICH_HADOOP ---"
    which hadoop
    echo "--- READLINK_HADOOP ---"
    readlink -f $(which hadoop)
    echo "--- HADOOP_DIR_LISTING ---"
    ls -la /opt/hadoop /opt/hadoop-3.4.0 2>&1
    echo "--- HADOOP_SUBDIRS ---"
    ls -d /opt/hadoop-3.4.0/* 2>&1
    echo "--- HADOOP_BINARIES ---"
    ls -l /opt/hadoop-3.4.0/bin/
    echo "--- HADOOP_SBIN ---"
    ls -l /opt/hadoop-3.4.0/sbin/
    echo "--- HDFS_JARS ---"
    ls -l /opt/hadoop-3.4.0/share/hadoop/hdfs/*.jar | head -n 5
    echo "--- MAPREDUCE_JARS ---"
    ls -l /opt/hadoop-3.4.0/share/hadoop/mapreduce/*.jar | head -n 5
    echo "--- STREAMING_JAR ---"
    find /opt/hadoop-3.4.0/share/hadoop/ -name "*streaming*.jar" 2>/dev/null
    """
    code, out, err = run_wsl_cmd(hadoop_script)
    results["task2_hadoop_audit"] = {
        "exit_code": code,
        "raw_output": out,
        "error_output": err
    }
    print(out)

    # TASK 3: Inspect Existing Configurations
    print("\n[TASK 3] Inspecting Existing Hadoop XML Configurations...")
    config_script = """
    CONF_DIR="/opt/hadoop/etc/hadoop"
    echo "=== core-site.xml ==="
    cat $CONF_DIR/core-site.xml 2>/dev/null || echo "MISSING"
    echo "=== hdfs-site.xml ==="
    cat $CONF_DIR/hdfs-site.xml 2>/dev/null || echo "MISSING"
    echo "=== mapred-site.xml ==="
    cat $CONF_DIR/mapred-site.xml 2>/dev/null || echo "MISSING"
    echo "=== yarn-site.xml ==="
    cat $CONF_DIR/yarn-site.xml 2>/dev/null || echo "MISSING"
    echo "=== hadoop-env.sh (JAVA_HOME / HEAP lines) ==="
    grep -E '^(export JAVA_HOME|export HADOOP_HEAPSIZE|export HADOOP_NAMENODE_OPTS|export HADOOP_DATANODE_OPTS)' $CONF_DIR/hadoop-env.sh 2>/dev/null || echo "No custom exports set in hadoop-env.sh"
    """
    code, out, err = run_wsl_cmd(config_script)
    results["task3_config_audit"] = {
        "exit_code": code,
        "raw_output": out,
        "error_output": err
    }
    print(out)

    # TASK 4: Check HDFS State & Metadata
    print("\n[TASK 4] Inspecting HDFS State, Metadata, and Processes...")
    hdfs_state_script = """
    echo "--- CHECKING DEFAULT TMP DFS LOCATIONS ---"
    find /tmp -name "dfs" -o -name "fsimage*" -o -name "edits*" 2>/dev/null || echo "None in /tmp"
    echo "--- CHECKING /var/hadoop OR /var/data LOCATIONS ---"
    ls -la /var/hadoop /var/data 2>/dev/null || echo "No /var/hadoop or /var/data directories"
    echo "--- CHECKING RUNNING JAVA/HADOOP PROCESSES ---"
    jps -l
    echo "--- CHECKING ACTIVE LISTENING PORTS (9000, 9870, 8088, 9864) ---"
    ss -tulpn 2>/dev/null | grep -E ':(9000|9870|8088|9864)' || echo "No active Hadoop ports"
    """
    code, out, err = run_wsl_cmd(hdfs_state_script)
    results["task4_hdfs_state"] = {
        "exit_code": code,
        "raw_output": out,
        "error_output": err
    }
    print(out)

    # TASK 5: Verify Hadoop Streaming & Python Environment
    print("\n[TASK 5] Auditing Hadoop Streaming & Python...")
    streaming_script = """
    echo "--- STREAMING JAR PATH ---"
    STREAMING_JAR=$(find /opt/hadoop-3.4.0/share/hadoop/tools/lib/ -name "hadoop-streaming-*.jar" 2>/dev/null | head -n 1)
    echo "Streaming JAR: $STREAMING_JAR"
    [ -f "$STREAMING_JAR" ] && echo "JAR Exists: YES (Size: $(stat -c%s "$STREAMING_JAR") bytes)" || echo "JAR Exists: NO"

    echo "--- PYTHON 3 IN UBUNTU ---"
    which python3
    python3 --version
    python3 -c "import sys; print('Python sys.executable:', sys.executable)"
    """
    code, out, err = run_wsl_cmd(streaming_script)
    results["task5_streaming_audit"] = {
        "exit_code": code,
        "raw_output": out,
        "error_output": err
    }
    print(out)

    # Save to reports/hadoop_installation_audit.json
    os.makedirs(os.path.dirname(AUDIT_REPORT_PATH), exist_ok=True)
    with open(AUDIT_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("AUDIT COMPLETE")
    print(f"Results saved to: {AUDIT_REPORT_PATH}")
    print("=" * 70)

if __name__ == "__main__":
    audit()
