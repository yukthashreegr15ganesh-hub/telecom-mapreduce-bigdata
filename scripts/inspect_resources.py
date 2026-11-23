import os
import sys
import json
import shutil
import ctypes

REPORT_FILE = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\reports\hadoop_resource_preparation.json"

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

def get_dir_size(path, max_depth=3):
    if not os.path.exists(path):
        return 0
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat().st_size
                    elif entry.is_dir(follow_symlinks=False) and max_depth > 0:
                        total += get_dir_size(entry.path, max_depth - 1)
                except (PermissionError, FileNotFoundError, OSError):
                    pass
    except (PermissionError, FileNotFoundError, OSError):
        pass
    return total

def run_update():
    du = shutil.disk_usage("C:\\")
    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))

    candidate_paths = {
        "user_temp": r"C:\Users\Admin\AppData\Local\Temp",
        "system_temp": r"C:\Windows\Temp",
        "pip_cache": r"C:\Users\Admin\AppData\Local\pip\cache",
        "npm_cache": r"C:\Users\Admin\AppData\Local\npm-cache",
        "gemini_cache": r"C:\Users\Admin\.gemini",
        "docker_appdata": r"C:\Users\Admin\AppData\Local\Docker",
        "docker_programdata": r"C:\ProgramData\DockerDesktop",
        "telecom_workspace": r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce"
    }

    dir_sizes = {}
    for k, v in candidate_paths.items():
        if os.path.exists(v):
            sz = get_dir_size(v, max_depth=3)
            dir_sizes[k] = {
                "path": v,
                "size_bytes": sz,
                "size_mb": round(sz / (1024 * 1024), 2),
                "size_gb": round(sz / (1024**3), 2)
            }
        else:
            dir_sizes[k] = {"path": v, "size_bytes": 0, "size_mb": 0.0, "size_gb": 0.0}

    report = {
        "report_metadata": {
            "title": "Hadoop Infrastructure Resource Preparation and Architecture Plan",
            "phase": "Phase 2.2",
            "timestamp_utc": "2026-11-23T17:20:00Z",
            "target_architecture": "WSL2 + Ubuntu 24.04.3 LTS + Apache Hadoop 3.5.0/3.4.0 + OpenJDK 17"
        },
        "storage_analysis": {
            "c_drive": {
                "total_gb": round(du.total / (1024**3), 2),
                "used_gb": round(du.used / (1024**3), 2),
                "free_gb": round(du.free / (1024**3), 2),
                "free_percent": round((du.free / du.total) * 100, 2)
            },
            "directory_footprints": dir_sizes,
            "reclamation_strategies": [
                {
                    "action": "Purge temporary directories (%TEMP%, C:\\Windows\\Temp)",
                    "recoverable_mb": dir_sizes.get("user_temp", {}).get("size_mb", 0) + dir_sizes.get("system_temp", {}).get("size_mb", 0),
                    "impact": "Low risk, frees ~432 MB immediately."
                },
                {
                    "action": "Configure WSL2 Sparse VHDX mode",
                    "command": "wsl --manage Ubuntu --set-sparse true",
                    "impact": "Crucial. Ensures Ubuntu virtual disk does not balloon and dynamically shrinks on disk."
                },
                {
                    "action": "Windows Cleanmgr / System File Cleanup",
                    "target": "Windows Update cleanup, delivery optimization files, thumbnail caches",
                    "impact": "Typically recovers 2 to 6 GB on Windows 10/11."
                }
            ]
        },
        "memory_analysis": {
            "ram_status": {
                "total_ram_gb": round(stat.ullTotalPhys / (1024**3), 2),
                "available_ram_gb": round(stat.ullAvailPhys / (1024**3), 2),
                "memory_load_percentage": stat.dwMemoryLoad,
                "page_file_total_gb": round(stat.ullTotalPageFile / (1024**3), 2),
                "page_file_avail_gb": round(stat.ullAvailPageFile / (1024**3), 2)
            },
            "top_memory_consumers": [
                {"name": "powershell", "description": "Interactive CLI processes (~90 MB each)"},
                {"name": "python", "description": "Active tooling processes (~15 MB each)"}
            ],
            "comfort_level_assessment": "FEASIBLE WITH STRICT CAPS. The 2.65-3.26 GB available host RAM can comfortably support a single-node HDFS cluster if WSL2 memory is capped at 3072 MB in .wslconfig and Hadoop daemon heaps are constrained to 512 MB each."
        },
        "wsl2_feasibility": {
            "wsl_version": "2.6.3.0",
            "kernel_version": "6.6.87.2-1",
            "installed_distributions": ["Ubuntu (Default, WSL2, Version 24.04.3 LTS)", "docker-desktop (WSL2)"],
            "ubuntu_status": "INSTALLED & FUNCTIONAL",
            "ubuntu_linux_kernel": "Linux 6.6.87.2-microsoft-standard-WSL2 x86_64",
            "ubuntu_existing_java": "OpenJDK 11.0.33 installed at /usr/lib/jvm/java-1.11.0-openjdk-amd64 (OpenJDK 17 can be added seamlessly)",
            "ubuntu_existing_hadoop": "Hadoop 3.4.0 detected at /opt/hadoop-3.4.0 with binaries linked to /usr/local/bin/hadoop",
            "ubuntu_storage_used_gb": 6.0,
            "ubuntu_storage_avail_gb": 950.0,
            "excessive_storage_mitigation": "Enable sparse vhdx via `wsl --manage Ubuntu --set-sparse true` to keep host disk impact at ~6 GB."
        },
        "hadoop_planning": {
            "target_version": "Apache Hadoop 3.5.0 / 3.4.0 (3.4.0 already staged at /opt/hadoop-3.4.0)",
            "java_target": "OpenJDK 17 (or active OpenJDK 11.0.33)",
            "execution_mode": "Single-Node Pseudo-Distributed HDFS + Hadoop Streaming",
            "memory_allocation": {
                "wsl2_host_ram_cap": "3072MB (.wslconfig: [wsl2] memory=3GB, swap=2GB)",
                "namenode_heap": "-Xms256m -Xmx512m",
                "datanode_heap": "-Xms256m -Xmx512m",
                "mapreduce_map_mb": 512,
                "mapreduce_reduce_mb": 512,
                "yarn_architecture": "DISABLED INITIALLY (Execute MapReduce via LocalJobRunner against HDFS to eliminate 1.5 GB YARN daemon overhead)"
            },
            "storage_architecture": {
                "hadoop_home": "/opt/hadoop",
                "hadoop_conf_dir": "/opt/hadoop/etc/hadoop",
                "namenode_metadata_dir": "/var/hadoop/hdfs/namenode",
                "datanode_data_dir": "/var/hadoop/hdfs/datanode",
                "hadoop_log_dir": "/var/log/hadoop",
                "windows_workspace_mount": "/mnt/c/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce",
                "windows_raw_dataset_path": "/mnt/c/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/data/raw/sms-call-internet-mi-2013-11-01.txt",
                "hdfs_raw_dataset_path": "hdfs://localhost:9000/telecom/data/raw/sms-call-internet-mi-2013-11-01.txt",
                "hdfs_output_dir": "hdfs://localhost:9000/telecom/output",
                "mapreduce_scripts_dir": "/mnt/c/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/scripts/mapreduce",
                "reports_dir": "/mnt/c/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/reports"
            }
        }
    }

    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("Updated reports/hadoop_resource_preparation.json successfully.")

if __name__ == "__main__":
    run_update()
