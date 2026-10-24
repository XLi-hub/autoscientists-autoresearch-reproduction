import json, os, requests
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"
MAIN_WS_ID=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAM_WS_ID=json.load(open("/tmp/ar_gpu1/part0.json"))["TEAM_WS_ID"]
for path in ["queue.md","dead_ends.md","strategy.md","knowledge/noise_floor.md","knowledge/axis_priors.md"]:
    r=requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/{path}",headers=HEADERS).json()
    print(f"\n######## {path} (v{r.get('version')}) ########\n"+r.get("content","")[:7000])
