import json, requests, yaml
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
r=requests.get(f"{API}/workspaces/{MAIN}/files/champion.md",headers=H).json()
c=r.get("content","").split("---"); fm=yaml.safe_load(c[1])
print("version:",r.get("version"),"| metric_value:",fm.get("metric_value"),"| exp:",fm.get("experiment_id"),"| agent:",fm.get("agent"))
