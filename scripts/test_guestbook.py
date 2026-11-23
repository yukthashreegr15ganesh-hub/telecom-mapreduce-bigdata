import urllib.request
import json

url = "https://dataverse.harvard.edu/api/access/datafile/2674255"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json"
}

payload = {
    "guestbookResponse": {
        "name": "Data Engineer",
        "email": "engineer@telecom.org",
        "institution": "Telecom Big Data Research",
        "position": "Data Engineer"
    }
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, headers=headers, method="POST")

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print("Status:", resp.status)
        print("Headers:", dict(resp.headers))
        peek = resp.read(200)
        print("Peek:", peek)
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print("Response body:", e.read().decode("utf-8"))
except Exception as e:
    print("Error:", e)
