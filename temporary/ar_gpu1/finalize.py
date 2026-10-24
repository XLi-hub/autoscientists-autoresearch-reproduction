import json, yaml, requests
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAM=json.load(open("/tmp/ar_gpu1/part0.json"))["TEAM_WS_ID"]
agent_md=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/AGENT.md").read_text()
r=requests.put(f"{API}/workspaces/{MAIN}/files/agents/{AGENT_NAME}.md",headers=H,json={"content":agent_md})
print("AGENT.md mirror:",r.status_code)
# session count
sc=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/memory/.session_count"); sc.write_text("2")
# final state checks
q=requests.get(f"{API}/workspaces/{TEAM}/files/queue.md",headers=H).json()
c=q.get("content","").split("---"); fm=yaml.safe_load(c[1])
print("team claims:",fm.get("claims"))
print("pending:",[i.get('id') for i in (fm.get('pending') or [])])
print("last 3 completed:",[(i.get('id'),i.get('outcome'),i.get('val_score')) for i in (fm.get('completed') or [])[-3:]])
ch=requests.get(f"{API}/workspaces/{MAIN}/files/champion.md",headers=H).json()
cf=yaml.safe_load(ch.get("content","").split("---")[1])
print("champion:",cf.get("experiment_id"),cf.get("metric_value"),"v",ch.get("version"))
sent=json.loads(Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace/result_latest.json").read_text())
print("sentinel:",sent.get("exp_id"),sent.get("status"),"posted=",sent.get("posted_to_workshop"))
