import json, requests
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_analyst3"
creds=json.load(open(Path(FOCUS_ROOT)/"agents"/AGENT_NAME/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
for a in ["ar_20261022hi_analyst2","ar_20261022hi_analyst1","ar_20261022hi_gpu5"]:
    c=requests.get(f"{API}/workspaces/{MAIN}/files/agents/{a}.md",headers=HEADERS,timeout=20).json().get("content","")
    print("="*25,a,"="*25)
    print(c[:3000])
