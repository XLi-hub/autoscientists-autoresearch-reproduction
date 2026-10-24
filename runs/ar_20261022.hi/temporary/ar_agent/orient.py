import json, os, requests, yaml
from pathlib import Path
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_analyst2"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": AGENT_NAME}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
TEAM_WS_ID = "032e5282-1362-4eef-9226-3d40299116aa"

def pf(resp):
    c = resp.get("content","")
    p = c.split("---")
    return yaml.safe_load(p[1]) if len(p)>=3 else {}

for label, wid in [("MAIN", MAIN_WS_ID), ("TEAM", TEAM_WS_ID)]:
    files = requests.get(f"{API}/workspaces/{wid}/files", headers=HEADERS).json().get("files", [])
    print(f"=== {label} FILES ({len(files)}) ===")
    for f in files:
        print(f"  {f['path']:55s} v{f.get('version')} {f.get('updatedAt','')[:19]} {f.get('updatedBy','')}")

print("\n=== CHAMPION.MD ===")
c = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/champion.md", headers=HEADERS).json()
print(c.get("content","")[:3000])
print("\n=== TEAM QUEUE ===")
q = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=HEADERS).json()
print(q.get("content","")[:4000])
