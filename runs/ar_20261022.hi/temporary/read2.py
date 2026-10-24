import json, requests, yaml
from pathlib import Path
AGENT_NAME="ar_20261022hi_analyst1"; FOCUS="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FOCUS}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds['agent_name']}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS}/WORKSPACE_ID").read().strip(); TEAM="54202fe1-b766-43f1-b374-9e4ed188c153"
def g(ws,p):
    r=requests.get(f"{API}/workspaces/{ws}/files/{p}",headers=H); return r.json() if r.status_code==200 else None
for ws,label,paths in [(TEAM,"TEAM",["dead_ends.md","knowledge/noise_floor.md","knowledge/baseline_coverage.md","knowledge/axis_priors.md","knowledge/unqueued_axes.md","hypotheses.md"]),
                       (MAIN,"MAIN",["knowledge/unqueued_axes.md","results/exp_batch_2e17.md","results/exp_aspect_ratio_32.md","results/exp_ve_all_layers.md","results/exp_depth_10.md","teams/roster.md"])]:
    for p in paths:
        f=g(ws,p)
        print(f"\n{'='*20} {label} {p} {'='*20}")
        print(f.get("content","MISSING") if f else "MISSING")
