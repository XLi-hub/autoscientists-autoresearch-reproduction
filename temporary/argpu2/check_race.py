import json, requests, yaml
from pathlib import Path
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
creds = json.load(open(f"{FOCUS_ROOT}/agents/ar_20261024_gpu2/credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": "ar_20261024_gpu2"}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
c = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/champion.md", headers=HEADERS).json()
print("champion v", c.get("version"), "updatedBy", c.get("updatedBy"), "updatedAt", c.get("updatedAt"))
print(c.get("content"))
print("=== main files ===")
fs = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files", headers=HEADERS).json().get("files", [])
for f in fs: print(f["path"], f["version"], f.get("updatedAt"), f.get("updatedBy"))
print("=== recent result posts ===")
posts = requests.get(f"{API}/posts?workshop=ar_ar_20261024&limit=20", headers=HEADERS).json().get("data", [])
for p in posts: print(p.get("title"))
