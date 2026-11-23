import subprocess

cmd = "/opt/hadoop/bin/hdfs dfs -cat /telecom/data/raw/sms-call-internet-mi-2013-11-01.txt"
proc = subprocess.Popen(
    ["wsl.exe", "-d", "Ubuntu", "-u", "dminmlops", "-e", "bash", "-c", cmd],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding="utf-8"
)

lines = []
for _ in range(10):
    line = proc.stdout.readline()
    if not line:
        break
    lines.append(line.rstrip("\r\n"))

proc.kill()
proc.wait()

for i, line in enumerate(lines):
    parts = line.split("\t")
    print(f"Row {i+1} ({len(parts)} fields): {parts}")
