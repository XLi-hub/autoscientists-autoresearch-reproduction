import json, os, yaml, requests
from pathlib import Path
AGENT_NAME = "ar_20261024_gpu9"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
TEAM_WS_ID = "d7c6f814-aab0-4029-a887-04345d274f9b"

def pf(resp):
    content = resp.get("content","")
    parts = content.split("---")
    return yaml.safe_load(parts[1]) if len(parts)>=3 else {}

print("========== CHAMPION.md ==========")
c = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/champion.md", headers=HEADERS, timeout=30).json()
print("version:", c.get("version"))
print(c.get("content","")[:2500])
print("\n========== TEAM FILES ==========")
tf = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files", headers=HEADERS, timeout=30).json().get("files",[])
for f in tf: print(" ", f.get("path"), "v", f.get("version"), f.get("updatedAt"))
print("\n========== QUEUE.md (capacity) ==========")
q = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=HEADERS, timeout=30).json()
print("version:", q.get("version"))
print(q.get("content","")[:4000])
