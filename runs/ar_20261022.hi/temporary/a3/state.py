import json, os, requests, yaml
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME="ar_20261022hi_analyst3"
AGENT_DIR=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds=json.load(open(AGENT_DIR/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API="http://localhost:3000/api/v1"
MAIN_WS_ID=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
def pf(resp):
    c=resp.get("content","");p=c.split("---")
    return yaml.safe_load(p[1]) if len(p)>=3 else {}
print("="*20,"ROSTER","="*20)
r=requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md",headers=HEADERS).json()
print(r["content"])
print("="*20,"CHAMPION.MD","="*20)
c=requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/champion.md",headers=HEADERS).json()
print(c.get("content","")[:3000])
print("="*20,"MAIN FILE LIST","="*20)
mf=requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files",headers=HEADERS).json()["files"]
for f in mf: print(f["path"], f.get("version"), f.get("updatedAt"))
