import subprocess
import json
import os
import time

REPORT_FILE = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\reports\hdfs_initialization_report.json"

def run_wsl(bash_cmd):
    cmd = ["wsl.exe", "-d", "Ubuntu", "-e", "bash", "-c", bash_cmd]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def run_step(step_name, cmd):
    print(f"\n--- {step_name} ---")
    code, out, err = run_wsl(cmd)
    print(out)
    if err:
        print(f"[STDERR]:\n{err}")
    return {"command": cmd, "exit_code": code, "stdout": out, "stderr": err}

def main():
    print("=" * 70)
    print("EXECUTING HDFS INITIALIZATION & CLUSTER STARTUP")
    print("=" * 70)

    report = {"stages": {}}

    # 1. Format NameNode
    format_cmd = "hdfs namenode -format -nonInteractive 2>&1"
    res_format = run_step("FORMAT NAMENODE", format_cmd)
    report["stages"]["format"] = res_format

    # 2. Inspect created metadata in /var/hadoop/hdfs/namenode/current
    meta_cmd = "ls -la /var/hadoop/hdfs/namenode/current 2>&1; cat /var/hadoop/hdfs/namenode/current/VERSION 2>&1"
    res_meta = run_step("INSPECT NAMENODE METADATA", meta_cmd)
    report["stages"]["namenode_metadata"] = res_meta

    # 3. Start HDFS daemons (NameNode and DataNode only, NO YARN)
    start_cmd = """
    hdfs --daemon start namenode
    sleep 3
    hdfs --daemon start datanode
    sleep 5
    """
    res_start = run_step("START HDFS DAEMONS", start_cmd)
    report["stages"]["start_daemons"] = res_start

    # 4. Verify running daemons via jps
    jps_cmd = "jps -l"
    res_jps = run_step("VERIFY RUNNING DAEMONS (JPS)", jps_cmd)
    report["stages"]["jps"] = res_jps

    # 5. Check DFS cluster report
    report_cmd = "hdfs dfsadmin -report"
    res_report = run_step("HDFS DFSADMIN REPORT", report_cmd)
    report["stages"]["dfsadmin_report"] = res_report

    # 6. Verify filesystem root
    ls_root_cmd = "hdfs dfs -ls /"
    res_ls_root = run_step("VERIFY ROOT HDFS FILESYSTEM", ls_root_cmd)
    report["stages"]["ls_root"] = res_ls_root

    # 7. Create Telecom project directories
    mkdir_cmd = """
    hdfs dfs -mkdir -p /telecom/data/raw
    hdfs dfs -mkdir -p /telecom/data/processed
    hdfs dfs -mkdir -p /telecom/output
    hdfs dfs -mkdir -p /telecom/results
    hdfs dfs -ls -R /telecom
    """
    res_mkdir = run_step("CREATE PROJECT DIRECTORIES", mkdir_cmd)
    report["stages"]["create_directories"] = res_mkdir

    # Save summary report
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 70)
    print("HDFS INITIALIZATION & DIRECTORY SETUP COMPLETE")
    print(f"Report saved to: {REPORT_FILE}")
    print("=" * 70)

if __name__ == "__main__":
    main()
