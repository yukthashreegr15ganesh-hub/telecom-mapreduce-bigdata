import os
import sys
import json
import shutil
import subprocess
import platform
import ctypes

REPORT_FILE = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\reports\environment_audit.json"

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

def get_ram_info():
    try:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return {
            "total_ram_bytes": stat.ullTotalPhys,
            "total_ram_gb": round(stat.ullTotalPhys / (1024**3), 2),
            "available_ram_bytes": stat.ullAvailPhys,
            "available_ram_gb": round(stat.ullAvailPhys / (1024**3), 2),
            "memory_load_percentage": stat.dwMemoryLoad
        }
    except Exception as e:
        return {"error": str(e)}

def get_disk_info(path="C:\\"):
    try:
        usage = shutil.disk_usage(path)
        return {
            "drive": path,
            "total_bytes": usage.total,
            "total_gb": round(usage.total / (1024**3), 2),
            "used_bytes": usage.used,
            "used_gb": round(usage.used / (1024**3), 2),
            "free_bytes": usage.free,
            "free_gb": round(usage.free / (1024**3), 2),
            "free_percentage": round((usage.free / usage.total) * 100, 2)
        }
    except Exception as e:
        return {"error": str(e)}

def run_cmd(cmd_list):
    try:
        proc = subprocess.run(cmd_list, capture_output=True, text=True, timeout=15)
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        return {
            "command": " ".join(cmd_list),
            "exit_code": proc.returncode,
            "stdout": out,
            "stderr": err,
            "success": proc.returncode == 0
        }
    except Exception as e:
        return {
            "command": " ".join(cmd_list),
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }

def run_powershell(ps_command):
    cmd = ["powershell", "-NoProfile", "-Command", ps_command]
    return run_cmd(cmd)

def audit_environment():
    print("=" * 70)
    print("EXECUTING READ-ONLY HADOOP ENVIRONMENT AUDIT")
    print("=" * 70)

    audit = {}

    # 1. Operating System & Hardware Inspection
    print("[1/5] Inspecting Operating System & Hardware...")
    ram_info = get_ram_info()
    disk_info = get_disk_info("C:\\")
    ps_version = run_powershell("$PSVersionTable.PSVersion.ToString()")

    # Query registry / Windows version details
    win_reg_ps = run_powershell("Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion' | Select-Object ProductName, DisplayVersion, CurrentBuild, ReleaseId | ConvertTo-Json")
    win_details = {}
    try:
        win_details = json.loads(win_reg_ps["stdout"])
    except:
        win_details = {"raw": win_reg_ps["stdout"]}

    audit["operating_system"] = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "processor_count": os.cpu_count(),
        "windows_edition_details": win_details,
        "ram": ram_info,
        "disk_c": disk_info,
        "powershell_version": ps_version["stdout"]
    }

    # 2. Java Inspection
    print("[2/5] Inspecting Java Runtime & Development Kit...")
    java_ver = run_cmd(["java", "-version"])
    javac_ver = run_cmd(["javac", "-version"])
    where_java = run_powershell("where.exe java")
    where_javac = run_powershell("where.exe javac")
    java_home = os.environ.get("JAVA_HOME", "")

    # Look for all Java JDKs installed across Program Files
    common_java_roots = [
        r"C:\Program Files\Java",
        r"C:\Program Files\Eclipse Adoptium",
        r"C:\Program Files\Amazon Corretto",
        r"C:\Program Files\Microsoft",
        r"C:\Program Files\Zulu",
        r"C:\Program Files (x86)\Java",
        r"C:\Users\Admin\.jdks"
    ]
    detected_jdks = []
    for r in common_java_roots:
        if os.path.exists(r):
            for entry in os.listdir(r):
                full_path = os.path.join(r, entry)
                if os.path.isdir(full_path):
                    java_bin = os.path.join(full_path, "bin", "java.exe")
                    javac_bin = os.path.join(full_path, "bin", "javac.exe")
                    detected_jdks.append({
                        "jdk_path": full_path,
                        "has_java": os.path.exists(java_bin),
                        "has_javac": os.path.exists(javac_bin)
                    })

    audit["java"] = {
        "installed": java_ver["success"] or (len(where_java["stdout"]) > 0),
        "java_version_output": java_ver["stderr"] if java_ver["stderr"] else java_ver["stdout"],
        "javac_version_output": javac_ver["stdout"] if javac_ver["stdout"] else javac_ver["stderr"],
        "javac_available": javac_ver["success"],
        "java_home_env": java_home,
        "java_binary_locations": where_java["stdout"].splitlines() if where_java["success"] else [],
        "javac_binary_locations": where_javac["stdout"].splitlines() if where_javac["success"] else [],
        "all_installed_jdks_found": detected_jdks,
        "compatibility_note": "Java 25 is currently active on PATH. Hadoop 3.x officially requires Java 8 or Java 11."
    }

    # 3. Hadoop Inspection
    print("[3/5] Inspecting Hadoop Environment & Configurations...")
    hadoop_ver = run_cmd(["hadoop", "version"])
    where_hadoop = run_powershell("where.exe hadoop")
    hadoop_home = os.environ.get("HADOOP_HOME", "")
    hadoop_conf_dir = os.environ.get("HADOOP_CONF_DIR", "")

    common_hadoop_paths = [
        r"C:\hadoop",
        r"C:\tools\hadoop",
        r"C:\Program Files\hadoop",
        r"C:\hadoop-3.3.6",
        r"C:\hadoop-3.3.5",
        r"C:\hadoop-3.3.4"
    ]
    existing_hadoop_dirs = [p for p in common_hadoop_paths if os.path.exists(p)]

    audit["hadoop"] = {
        "installed": hadoop_ver["success"] or (len(where_hadoop["stdout"]) > 0),
        "hadoop_home_env": hadoop_home,
        "hadoop_conf_dir_env": hadoop_conf_dir,
        "hadoop_version_output": hadoop_ver["stdout"] if hadoop_ver["stdout"] else hadoop_ver["stderr"],
        "hadoop_binary_locations": where_hadoop["stdout"].splitlines() if where_hadoop["success"] else [],
        "detected_hadoop_dirs": existing_hadoop_dirs
    }

    # 4. Supporting Dependencies (Python, Git, Maven, Winutils, WSL, Docker, JPS)
    print("[4/5] Inspecting Supporting Dependencies (Python, Git, Maven, Winutils, WSL, Docker, Processes)...")
    python_ver = run_cmd(["python", "--version"])
    git_ver = run_cmd(["git", "--version"])
    mvn_ver = run_cmd(["mvn", "-version"])
    wsl_status = run_powershell("wsl.exe --status")
    wsl_list = run_powershell("wsl.exe -l -v")
    docker_ver = run_cmd(["docker", "--version"])
    docker_info = run_cmd(["docker", "info"])
    jps_run = run_cmd(["jps"])

    # Winutils check
    where_winutils = run_powershell("where.exe winutils")
    common_winutils = [
        os.path.join(hadoop_home, "bin", "winutils.exe") if hadoop_home else "",
        r"C:\hadoop\bin\winutils.exe",
        r"C:\winutils\bin\winutils.exe"
    ]
    detected_winutils = [p for p in common_winutils if p and os.path.exists(p)]

    # Java processes
    java_procs = run_powershell("Get-Process -Name java -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, WorkingSet | ConvertTo-Json")

    audit["dependencies"] = {
        "python": {
            "available": python_ver["success"],
            "version": python_ver["stdout"]
        },
        "git": {
            "available": git_ver["success"],
            "version": git_ver["stdout"]
        },
        "maven": {
            "available": mvn_ver["success"],
            "version_output": mvn_ver["stdout"] if mvn_ver["success"] else mvn_ver["stderr"]
        },
        "winutils": {
            "available": where_winutils["success"] or (len(detected_winutils) > 0),
            "binary_locations": where_winutils["stdout"].splitlines() if where_winutils["success"] else detected_winutils
        },
        "wsl": {
            "status_output": wsl_status["stdout"] if wsl_status["success"] else wsl_status["stderr"],
            "distros_output": wsl_list["stdout"] if wsl_list["success"] else wsl_list["stderr"],
            "available": wsl_list["success"]
        },
        "docker": {
            "installed": docker_ver["success"],
            "version_output": docker_ver["stdout"],
            "daemon_running": docker_info["success"]
        },
        "processes": {
            "jps_output": jps_run["stdout"] if jps_run["success"] else jps_run["stderr"],
            "java_processes": java_procs["stdout"]
        }
    }

    # Save report
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)

    print("=" * 70)
    print("ENVIRONMENT AUDIT COMPLETED")
    print(f"Results saved to: {REPORT_FILE}")
    print("=" * 70)

if __name__ == "__main__":
    audit_environment()
