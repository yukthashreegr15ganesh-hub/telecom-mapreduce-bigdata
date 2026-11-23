import urllib.request
import json
import sys

DOI = "doi:10.7910/DVN/EGZHFV"
API_URL = f"https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId={DOI}"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

print(f"Querying Harvard Dataverse API for DOI: {DOI}...")
try:
    req = urllib.request.Request(API_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        if resp.status == 200:
            content = resp.read().decode("utf-8")
            data = json.loads(content)
            version_data = data["data"]["latestVersion"]
            files = version_data.get("files", [])
            print(f"Dataset Title: {version_data.get('metadataBlocks', {}).get('citation', {}).get('fields', [{}])[0].get('value')}")
            print(f"Total files available: {len(files)}")
            total_size = sum(f.get("dataFile", {}).get("filesize", 0) for f in files)
            print(f"Total dataset size: {total_size:,} bytes ({total_size / (1024**3):.2f} GB)")
            
            # Save raw metadata to data/metadata/dataset_metadata.json
            metadata_path = "C:/Users/Admin/.gemini/antigravity/scratch/telecom-mapreduce/data/metadata/dataset_metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as out:
                json.dump(data, out, indent=2)
            print(f"Successfully saved metadata to {metadata_path}")
            
            print("\nFirst 10 files in dataset:")
            for i, f in enumerate(files[:10]):
                df = f.get("dataFile", {})
                print(f"[{i+1:02d}] ID: {df.get('id')}, Filename: {df.get('filename')}, Size: {df.get('filesize'):,} bytes, MD5: {df.get('md5')}")
            
            # Check date range of filenames
            filenames = sorted([f.get("dataFile", {}).get("filename", "") for f in files])
            print(f"\nFilename range: from '{filenames[0]}' to '{filenames[-1]}'")
        else:
            print(f"Unexpected status: {resp.status}")
except Exception as e:
    print(f"Failed to query Dataverse API: {e}", file=sys.stderr)
    sys.exit(1)
