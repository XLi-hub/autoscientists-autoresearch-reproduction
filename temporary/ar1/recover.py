import json, os, requests
from pathlib import Path
FOCUS=Path("/root/autodl-tmp/ar_20261022.hi")
creds=json.load(open(FOCUS/"agents/ar_20261022hi_analyst1/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name")}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN=open(FOCUS/"WORKSPACE_ID").read().strip()
for v in [3,2,1]:
    r=requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/noise_floor_data.md?version={v}",headers=H)
    print(f"===== noise_floor_data v{v} (HTTP {r.status_code}) =====")
    print(r.json().get("content","")[:2500] if r.status_code==200 else r.text[:200])
print("\n===== results/exp_adam_beta2_hi.md =====")
r=requests.get(f"{API}/workspaces/{MAIN}/files/results/exp_adam_beta2_hi.md",headers=H)
print(r.json().get("content","")[:3500] if r.status_code==200 else r.status_code)
print("\n===== main knowledge/noise_floor.md (v1 - someone else's) =====")
r=requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/noise_floor.md?version=0",headers=H)
print(r.json().get("content","")[:1500] if r.status_code==200 else r.status_code)
