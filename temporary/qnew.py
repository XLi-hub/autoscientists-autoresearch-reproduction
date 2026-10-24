import json, requests, yaml
AGENT_NAME="ar_20261022hi_gpu4"; FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; st=json.load(open("/tmp/p0_state.json")); TEAM=st["TEAM_WS_ID"]
r=requests.get(f"{API}/workspaces/{TEAM}/files/queue.md",headers=H).json()
q=yaml.safe_load(r.get("content","").split("---")[1])
for it in q.get("pending",[]):
    print(f"\n{it.get('id')} [{it.get('priority')}] by={it.get('proposed_by')} axis={it.get('axis')} {it.get('direction')}={it.get('value')}")
    print("  ", str(it.get('description',''))[:220])
    print("   diff:", str(it.get('diff',''))[:220])
