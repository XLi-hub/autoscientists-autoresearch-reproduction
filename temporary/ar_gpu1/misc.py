import json, requests, yaml
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAM=json.load(open("/tmp/ar_gpu1/part0.json"))["TEAM_WS_ID"]
def pf(r):
    c=r.get("content",""); p=c.split("---"); return yaml.safe_load(p[1]) if len(p)>=3 else {}
r=requests.get(f"{API}/workspaces/{MAIN}/files/teams/roster.md",headers=HEADERS).json()
print("ROSTER:\n", r.get("content",""))
print("="*80)
for p in ["results/exp_warmdown_070.md","knowledge/unqueued_axes.md"]:
    d=requests.get(f"{API}/workspaces/{MAIN}/files/{p}",headers=HEADERS).json()
    print(f"--- {p} ---\n", d.get("content","")[:4500])
