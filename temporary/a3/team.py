import json, requests, yaml
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME="ar_20261022hi_analyst3"
AGENT_DIR=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds=json.load(open(AGENT_DIR/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API="http://localhost:3000/api/v1"
MAIN_WS_ID=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAM_WS_ID="3a33313e-18ff-4e17-9c47-66b54cfe576d"
print("="*15,"TEAM FILE LIST","="*15)
tf=requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files",headers=HEADERS).json().get("files",[])
for f in tf: print(f["path"], f.get("version"), f.get("updatedAt"))
print("="*15,"QUEUE.MD","="*15)
q=requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md",headers=HEADERS).json()
print("version",q.get("version")); print(q.get("content","")[:6000])
