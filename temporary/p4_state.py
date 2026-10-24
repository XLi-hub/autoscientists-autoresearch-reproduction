import json, os, requests, yaml
from pathlib import Path
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_analyst3"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAM_WS_ID = "3a33313e-18ff-4e17-9c47-66b54cfe576d"

def get(ws, path):
    return requests.get(f"{API}/workspaces/{ws}/files/{path}", headers=HEADERS, timeout=20).json()

print("=== MAIN FILES ===")
mf = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files", headers=HEADERS, timeout=30).json()["files"]
for f in sorted(mf, key=lambda x: x.get("updatedAt","")):
    print(f"{f.get('updatedAt')} v{f.get('version')} {f['path']}")
print("\n=== TEAM FILES ===")
tf = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files", headers=HEADERS, timeout=30).json()["files"]
for f in sorted(tf, key=lambda x: x.get("updatedAt","")):
    print(f"{f.get('updatedAt')} v{f.get('version')} {f['path']}")

print("\n=== CHAMPION.md ===")
print(get(MAIN_WS_ID, "champion.md").get("content","")[:2500])
print("\n=== TEAM QUEUE.md ===")
q = get(TEAM_WS_ID, "queue.md")
print("version", q.get("version"))
print(q.get("content","")[:6000])
