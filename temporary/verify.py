import json, os, requests, yaml
from pathlib import Path
AGENT_NAME = "ar_20261022hi_gpu5"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
creds = json.load(open(Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")/"credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
st = json.load(open("/tmp/part0_state.json")); TEAM_WS_ID = st["TEAM_WS_ID"]
def pf(resp):
    c = resp.get("content",""); p = c.split("---")
    return yaml.safe_load(p[1]) if len(p)>=3 else {}
q = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=HEADERS).json()
fm = pf(q)
print("QUEUE v", q.get("version"))
print("claims:", fm.get("claims"))
print("pending:", [(i.get("id"), i.get("outcome")) for i in (fm.get("pending") or [])])
print("completed:", [(i.get("id"), i.get("outcome"), i.get("val_score")) for i in (fm.get("completed") or [])])
recent = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=8", headers=HEADERS).json().get("data",[])
print("\nRECENT POSTS:")
for p in recent: print(p.get("id"), "|", p.get("createdAt"), "|", (p.get("title") or "")[:110])
# result file exists?
rf = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/results/exp_head_dim_64.md", headers=HEADERS)
print("\nresult file status:", rf.status_code, "len", len(rf.json().get("content","") or ""))
# sentinel
print("\nSENTINEL:", json.loads(Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace/result_latest.json").read_text()).get("status"))
