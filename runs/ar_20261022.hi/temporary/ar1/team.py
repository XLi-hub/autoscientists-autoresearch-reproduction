import json, os, requests
from pathlib import Path
FOCUS=Path("/root/autodl-tmp/ar_20261022.hi")
creds=json.load(open(FOCUS/"agents/ar_20261022hi_analyst1/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name")}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
TEAM="54202fe1-b766-43f1-b374-9e4ed188c153"
r=requests.get(f"{API}/workspaces/{TEAM}/files",headers=HEADERS).json()
print("=== TEAM FILES ===")
for f in r.get("files",[]):
    print(f"  {f['path']:<50} v{f.get('version')} {f.get('updatedAt','')[:19]}")
for p in ["queue.md","strategy.md","dead_ends.md","knowledge/unqueued_axes.md","knowledge/noise_floor.md","knowledge/axis_priors.md","knowledge/baseline_coverage.md"]:
    rr=requests.get(f"{API}/workspaces/{TEAM}/files/{p}",headers=HEADERS)
    print(f"\n===== {p}  (HTTP {rr.status_code}) =====")
    if rr.status_code==200:
        print(rr.json().get("content","")[:6000])
