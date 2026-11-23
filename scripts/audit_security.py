import os
import re

PATTERNS = [
    re.compile(r'(?i)(password|secret|token|api[_-]?key|bearer|private[_-]?key)\s*[:=]\s*["\']([^"\']+)["\']'),
    re.compile(r'-----BEGIN\s+[A-Z\s]+PRIVATE KEY-----')
]

workspace = r"C:\Users\Admin\.gemini\antigravity\scratch\telecom-mapreduce"
findings = []

for root, dirs, files in os.walk(workspace):
    if any(x in root for x in ["data", ".git", "__pycache__", "venv"]):
        continue
    for file in files:
        fpath = os.path.join(root, file)
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for p in PATTERNS:
                    m = p.findall(content)
                    if m:
                        findings.append((fpath, m))
        except Exception as e:
            pass

print(f"Secret scan completed. Found: {len(findings)} potential matches.")
for path, match in findings:
    print(f"File: {path} -> {match}")
