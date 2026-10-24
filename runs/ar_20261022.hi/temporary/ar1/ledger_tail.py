import json, os, requests
from pathlib import Path
FOCUS=Path("/root/autodl-tmp/ar_20261022.hi")
creds=json.load(open(FOCUS/"agents/ar_20261022hi_analyst1/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name")}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN=open(FOCUS/"WORKSPACE_ID").read().strip()
led=requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/unqueued_axes.md",headers=H).json()
c=led.get("content","")
print("version",led.get("version"),"len",len(c))
i=c.find("| final_lr_frac")
print(c[i-200:])
for kw in ["softcap","tied","lm_head.weight"]:
    print(kw, "->", kw in c.lower())
