#!/usr/bin/env python3
"""
High-Performance Dashboard Launcher
Project: Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce
Workspace: C:\\Users\\Admin\\.gemini\\antigravity\\scratch\\telecom-mapreduce
"""

import subprocess
import sys
import os

def main():
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")
    cmd = [
        sys.executable, "-m", "streamlit", "run", dashboard_path,
        "--server.port=8501",
        "--server.headless=true",
        "--server.runOnSave=false",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false"
    ]
    print("Launching Optimized Streamlit Telecom Dashboard on http://localhost:8501 ...")
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("Stopping dashboard...")
        proc.terminate()

if __name__ == "__main__":
    main()
