import subprocess
import json
import sys

def run_wsl(bash_cmd):
    full_cmd = f"source /etc/profile; export PATH=/opt/hadoop/bin:/usr/lib/jvm/java-11-openjdk-amd64/bin:$PATH; {bash_cmd}"
    res = subprocess.run(
        ["wsl.exe", "-d", "Ubuntu", "-u", "dminmlops", "-e", "bash", "-c", full_cmd],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return res.returncode, res.stdout, res.stderr

print("--- Checking JPS ---")
rc, out, err = run_wsl("jps")
print(out)

print("--- Running dfsadmin -report ---")
rc, report_out, report_err = run_wsl("/opt/hadoop/bin/hdfs dfsadmin -report")
print("RC:", rc)
print("STDOUT:\n", report_out)
if report_err:
    print("STDERR:\n", report_err)

print("--- Creating HDFS directories ---")
rc_mkdir, mkdir_out, mkdir_err = run_wsl("/opt/hadoop/bin/hdfs dfs -mkdir -p /telecom/data/raw /telecom/data/processed /telecom/output /telecom/results")
print("MKDIR RC:", rc_mkdir)
if mkdir_err:
    print("MKDIR STDERR:", mkdir_err)

print("--- Listing /telecom recursively ---")
rc_ls, ls_out, ls_err = run_wsl("/opt/hadoop/bin/hdfs dfs -ls -R /telecom")
print("LS RC:", rc_ls)
print("LS OUTPUT:\n", ls_out)

# Save results to a temporary JSON for reporting
report_data = {
    "jps": out.strip().split("\n") if out.strip() else [],
    "dfsadmin_report": report_out.strip(),
    "mkdir_returncode": rc_mkdir,
    "hdfs_structure": ls_out.strip()
}

with open("reports/hdfs_cluster_status_raw.json", "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2)
print("Saved raw cluster status.")
