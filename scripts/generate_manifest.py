import json
import csv
import os

METADATA_FILE = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\data\metadata\dataset_metadata.json"
MANIFEST_CSV = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\data\metadata\download_manifest.csv"

def generate_manifest():
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    files = data["data"]["latestVersion"]["files"]
    manifest_rows = []
    
    for item in files:
        df = item["dataFile"]
        fid = df["id"]
        filename = df["filename"]
        filesize = df["filesize"]
        md5 = df.get("md5", "")
        # Extract date from filename: sms-call-internet-mi-YYYY-MM-DD.txt
        date_str = filename.replace("sms-call-internet-mi-", "").replace(".txt", "")
        download_url = f"https://dataverse.harvard.edu/api/access/datafile/{fid}"
        
        manifest_rows.append({
            "file_id": fid,
            "filename": filename,
            "activity_date": date_str,
            "filesize_bytes": filesize,
            "filesize_mb": round(filesize / (1024 * 1024), 2),
            "md5_checksum": md5,
            "download_url": download_url
        })
    
    # Sort by filename / date
    manifest_rows.sort(key=lambda x: x["filename"])
    
    os.makedirs(os.path.dirname(MANIFEST_CSV), exist_ok=True)
    with open(MANIFEST_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["file_id", "filename", "activity_date", "filesize_bytes", "filesize_mb", "md5_checksum", "download_url"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)
        
    print(f"Generated manifest with {len(manifest_rows)} daily files at {MANIFEST_CSV}")
    print(f"Total size: {sum(r['filesize_bytes'] for r in manifest_rows):,} bytes ({sum(r['filesize_bytes'] for r in manifest_rows)/(1024**3):.2f} GB)")

if __name__ == "__main__":
    generate_manifest()
