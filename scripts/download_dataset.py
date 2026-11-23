import os
import sys
import csv
import hashlib
import time
import urllib.request
import json
import argparse

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
CHUNK_SIZE = 1024 * 1024  # 1 MB chunk

GUESTBOOK_PAYLOAD = {
    "guestbookResponse": {
        "name": "Data Engineer",
        "email": "engineer@telecom.org",
        "institution": "Telecom Big Data Research",
        "position": "Data Engineer"
    }
}

def compute_md5(file_path):
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_signed_url(file_id):
    endpoint = f"https://dataverse.harvard.edu/api/access/datafile/{file_id}"
    data = json.dumps(GUESTBOOK_PAYLOAD).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data, headers={
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json"
    }, method="POST")
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status == 200:
            res_json = json.loads(resp.read().decode("utf-8"))
            signed_url = res_json.get("data", {}).get("signedUrl")
            return signed_url
        else:
            raise RuntimeError(f"Unexpected status code {resp.status} while obtaining signed URL")

def download_file(file_id, target_path, expected_md5=None, expected_size=None):
    temp_path = target_path + ".part"
    filename = os.path.basename(target_path)
    
    # 1. Check if already exists and matches size and MD5
    if os.path.exists(target_path):
        actual_size = os.path.getsize(target_path)
        if expected_size and actual_size != expected_size:
            print(f"Existing file {filename} size ({actual_size:,}) != expected ({expected_size:,}). Re-downloading.")
        else:
            if expected_md5:
                print(f"Verifying existing file checksum for {filename}...")
                actual_md5 = compute_md5(target_path)
                if actual_md5.lower() == expected_md5.lower():
                    print(f"[ALREADY EXISTS & VERIFIED] {filename} (MD5: {actual_md5})")
                    return True
                else:
                    print(f"MD5 mismatch on existing {filename}: expected {expected_md5}, got {actual_md5}. Re-downloading.")
            else:
                print(f"[ALREADY EXISTS] {filename}")
                return True

    # 2. Obtain Signed Download URL
    print(f"Obtaining signed download URL for file ID {file_id} ({filename})...")
    signed_url = get_signed_url(file_id)
    if not signed_url:
        print(f"[ERROR] Could not obtain signed URL for file ID {file_id}", file=sys.stderr)
        return False

    # 3. Check for partial download
    downloaded_bytes = 0
    if os.path.exists(temp_path):
        downloaded_bytes = os.path.getsize(temp_path)
        print(f"Resuming partial download for {filename} from byte {downloaded_bytes:,}...")

    req = urllib.request.Request(signed_url, headers={"User-Agent": USER_AGENT})
    if downloaded_bytes > 0:
        req.add_header("Range", f"bytes={downloaded_bytes}-")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            status = resp.status
            content_length = resp.headers.get("Content-Length")
            total_size = int(content_length) + downloaded_bytes if content_length else expected_size
            
            mode = "ab" if downloaded_bytes > 0 and status == 206 else "wb"
            if mode == "wb":
                downloaded_bytes = 0

            start_time = time.time()
            last_report = start_time
            with open(temp_path, mode) as f:
                while True:
                    chunk = resp.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded_bytes += len(chunk)
                    
                    now = time.time()
                    if now - last_report >= 2.0:
                        speed = downloaded_bytes / (now - start_time + 0.001) / (1024 * 1024)
                        if total_size:
                            pct = (downloaded_bytes / total_size) * 100
                            print(f"\rDownloading {filename}: {downloaded_bytes:,}/{total_size:,} bytes ({pct:.1f}%) at {speed:.2f} MB/s", end="", flush=True)
                        else:
                            print(f"\rDownloading {filename}: {downloaded_bytes:,} bytes at {speed:.2f} MB/s", end="", flush=True)
                        last_report = now
            print()

        # Atomic rename after download completion
        if os.path.exists(target_path):
            os.remove(target_path)
        os.rename(temp_path, target_path)

        # 4. Checksum verification
        if expected_md5:
            print(f"Computing MD5 checksum for {filename}...")
            actual_md5 = compute_md5(target_path)
            if actual_md5.lower() != expected_md5.lower():
                print(f"[FATAL CHECK ERROR] Checksum mismatch for {filename}!\nExpected: {expected_md5}\nActual:   {actual_md5}", file=sys.stderr)
                return False
            print(f"[CHECKSUM VERIFIED] MD5 matched: {actual_md5}")

        print(f"[SUCCESS] Downloaded and verified: {filename} ({os.path.getsize(target_path):,} bytes)")
        return True

    except Exception as e:
        print(f"\n[ERROR] Download failed for {filename}: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Resumable downloader for Telecom Italia Milan CDR dataset.")
    parser.add_argument("--manifest", default=r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\data\metadata\download_manifest.csv", help="Path to manifest CSV")
    parser.add_argument("--output-dir", default=r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce\data\raw", help="Target directory")
    parser.add_argument("--limit", type=int, default=1, help="Number of files to download (default: 1 for verification)")
    parser.add_argument("--date", type=str, help="Specific date to download (YYYY-MM-DD)")
    parser.add_argument("--all", action="store_true", help="Download all files in manifest")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    with open(args.manifest, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    if args.date:
        targets = [r for r in reader if r["activity_date"] == args.date]
    elif args.all:
        targets = reader
    else:
        targets = reader[:args.limit]

    print(f"Queueing {len(targets)} file(s) for download into {args.output_dir}...")
    success_count = 0
    for item in targets:
        target_path = os.path.join(args.output_dir, item["filename"])
        expected_size = int(item["filesize_bytes"])
        expected_md5 = item["md5_checksum"]
        file_id = item["file_id"]

        print(f"\n--- Target: {item['filename']} (ID: {file_id}, Size: {expected_size:,} bytes / {item['filesize_mb']} MB) ---")
        if download_file(file_id, target_path, expected_md5, expected_size):
            success_count += 1
        else:
            print(f"[FAILED] Could not acquire {item['filename']}")

    print(f"\n==========================================")
    print(f"Download Summary: {success_count}/{len(targets)} files completed successfully.")
    print(f"==========================================")

if __name__ == "__main__":
    main()
