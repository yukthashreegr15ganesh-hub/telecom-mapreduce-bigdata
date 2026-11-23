import os
import sys
import time

RAW_DIR = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\data\raw"
PART_FILE = os.path.join(RAW_DIR, "sms-call-internet-mi-2013-11-01.txt.part")
FINAL_FILE = os.path.join(RAW_DIR, "sms-call-internet-mi-2013-11-01.txt")
TOTAL_EXPECTED = 322874887

def probe():
    final_exists = os.path.exists(FINAL_FILE)
    part_exists = os.path.exists(PART_FILE)

    if final_exists:
        sz = os.path.getsize(FINAL_FILE)
        print(f"Final file already exists: {sz} bytes")
        return

    if not part_exists:
        print("Error: Part file not found")
        return

    size_1 = os.path.getsize(PART_FILE)
    t0 = time.time()
    print(f"Reading 1 (t=0s): {size_1} bytes")

    time.sleep(60)

    size_2 = os.path.getsize(PART_FILE)
    t1 = time.time()
    elapsed = round(t1 - t0, 2)
    growth = size_2 - size_1
    pct = round((size_2 / TOTAL_EXPECTED) * 100, 2)

    print(f"Reading 2 (t={elapsed}s): {size_2} bytes")
    print(f"Growth: {growth} bytes ({round(growth / (1024*1024), 2)} MB)")
    print(f"Download Progress: {pct}%")
    print(f"Progressing: {growth > 0}")

if __name__ == "__main__":
    probe()
