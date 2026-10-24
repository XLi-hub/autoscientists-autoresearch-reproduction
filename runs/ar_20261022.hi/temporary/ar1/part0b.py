import json, os, requests, yaml
from pathlib import Path
FOCUS=Path("/root/autodl-tmp/ar_20261022.hi")
AGENT_NAME="ar_20261022hi_analyst1"
AGENT_DIR=FOCUS/"agents"/AGENT_NAME
creds=json.load(open(AGENT_DIR/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN_WS_ID=open(FOCUS/"WORKSPACE_ID").read().strip()
WORKSHOP=open(FOCUS/"WORKSHOP_NAME").read().strip()
def pf(resp):
    c=resp.get("content","")
    parts=c.split("---")
    return yaml.safe_load(parts[1]) if len(parts)>=3 else {}
roster_raw=requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md",headers=HEADERS).json()
print("ROSTER STATUS", type(roster_raw), list(roster_raw)[:5] if isinstance(roster_raw,dict) else "")
roster=pf(roster_raw)
print(json.dumps(roster, indent=1)[:3000])
