import json, os, requests, sys
AGENT_NAME="ar_20261024_analyst2"; FOCUS_ROOT="/root/autodl-tmp/ar_20261024"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
GQ="005cb9ec-6fce-4bba-9340-21c08ab914c5"; CAP="d7c6f814-aab0-4029-a887-04345d274f9b"; TP="6e6d22a0-cee2-4b39-b6df-799fea80be27"
targets=[(GQ,"queue.md"),(GQ,"strategy.md"),(GQ,"dead_ends.md"),(GQ,"knowledge/noise_floor.md"),
         (MAIN,"knowledge/noise_floor_data.md"),(MAIN,"knowledge/unqueued_axes.md"),(MAIN,"knowledge/exhausted.md"),
         (MAIN,"knowledge/patterns.md"),(CAP,"queue.md"),(TP,"queue.md"),(GQ,"knowledge/axis_priors.md"),
         (GQ,"knowledge/baseline_coverage.md"),(CAP,"analysis/capacity-rebase-cycle2.md"),
         (CAP,"analysis/depth-width-coupling-and-param-budget.md")]
for ws,path in targets:
    r=requests.get(f"{API}/workspaces/{ws}/files/{path}",headers=HEADERS).json()
    print("\n"+"="*100); print(f"### {path} (ws={ws[:8]}) version={r.get('version')}")
    print(r.get("content",""))
