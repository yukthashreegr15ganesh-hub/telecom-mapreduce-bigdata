import subprocess

def inspect_logs():
    cmd = """
    echo "=== RECENT NAMENODE LOG ==="
    tail -n 35 /var/log/hadoop/hadoop-dminmlops-namenode-LAPTOP-R0TENJC5.log 2>/dev/null || true
    echo ""
    echo "=== RECENT DATANODE LOG ==="
    tail -n 35 /var/log/hadoop/hadoop-dminmlops-datanode-LAPTOP-R0TENJC5.log 2>/dev/null || true
    echo ""
    echo "=== /tmp start logs ==="
    cat /tmp/nn_start.log 2>/dev/null || true
    cat /tmp/dn_start.log 2>/dev/null || true
    """
    res = subprocess.run(
        ["wsl.exe", "-d", "Ubuntu", "-u", "dminmlops", "-e", "bash", "-c", cmd],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)

if __name__ == "__main__":
    inspect_logs()
