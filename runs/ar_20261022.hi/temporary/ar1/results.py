import json, os, requests
from pathlib import Path
FOCUS=Path("/root/autodl-tmp/ar_20261022.hi")
creds=json.load(open(FOCUS/"agents/ar_20261022hi_analyst1/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name")}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN=open(FOCUS/"WORKSPACE_ID").read().strip()
for p in ["champion.md","results/exp_batch_2e17.md","results/exp_batch_2e16.md","results/exp_warmdown_070.md","results/exp_ve_all_layers.md","results/exp_depth_10.md","results/exp_aspect_ratio_32.md"]:
    r=requests.get(f"{API}/workspaces/{MAIN}/files/{p}",headers=HEADERS)
    print(f"\n########## {p} (HTTP {r.status_code}) ##########")
    if r.status_code==200:
        print(r.json().get("content","")[:4500])
