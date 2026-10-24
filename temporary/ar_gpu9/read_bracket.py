import json, requests
from pathlib import Path
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu9"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": AGENT_NAME}
API = "http://localhost:3000/api/v1"
d = requests.get(f"{API}/posts/552e2db3-5221-498b-a61e-83f155016948", headers=HEADERS, timeout=30).json()
print(d.get("content","")[3000:8000])
