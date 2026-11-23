import os
import sys

PART_PATH = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\data\raw\sms-call-internet-mi-2013-11-01.txt.part"
FULL_PATH = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\data\raw\sms-call-internet-mi-2013-11-01.txt"
SAMPLE_PATH = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\data\sample\sms-call-internet-mi-sample.txt"

def extract_sample(num_records=50000):
    source_path = FULL_PATH if os.path.exists(FULL_PATH) else PART_PATH
    if not os.path.exists(source_path):
        print(f"Source file not available at {source_path}")
        return False
    
    os.makedirs(os.path.dirname(SAMPLE_PATH), exist_ok=True)
    count = 0
    with open(source_path, "r", encoding="utf-8", errors="replace") as fin, \
         open(SAMPLE_PATH, "w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            fout.write(line)
            count += 1
            if count >= num_records:
                break
                
    sample_size = os.path.getsize(SAMPLE_PATH)
    print(f"Extracted {count:,} genuine records into {SAMPLE_PATH} ({sample_size:,} bytes / {sample_size/(1024*1024):.2f} MB)")
    return True

if __name__ == "__main__":
    extract_sample()
