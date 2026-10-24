import json, requests
from pathlib import Path
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
creds = json.load(open(f"{FOCUS_ROOT}/agents/ar_20261024_gpu2/credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": "ar_20261024_gpu2"}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
r = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/baseline_lock.md", headers=HEADERS)
print(r.status_code, r.json().get("version"), r.json().get("updatedBy"))
print(r.json().get("content"))
c = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/champion.md", headers=HEADERS).json()
print("champion v", c.get("version"))
