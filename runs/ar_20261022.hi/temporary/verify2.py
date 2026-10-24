import json, os, requests, yaml
from pathlib import Path
AGENT_NAME = "ar_20261022hi_gpu5"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
creds = json.load(open(Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")/"credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
st = json.load(open("/tmp/part0_state.json")); TEAM_WS_ID=st["TEAM_WS_ID"]
def pf(r):
    p=r.get("content","").split("---"); return yaml.safe_load(p[1]) if len(p)>=3 else {}
ch = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/champion.md", headers=HEADERS).json()
print("CHAMPION v", ch.get("version"), "=", pf(ch).get("metric_value"), pf(ch).get("experiment_id"))
nf = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/knowledge/noise_floor_data.md", headers=HEADERS).json()
print("NOISE FLOOR v", nf.get("version"), "n_pairs", pf(nf).get("n_pairs"))
q = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=HEADERS).json(); fm=pf(q)
print("QUEUE v", q.get("version"), "claims", fm.get("claims"))
print(" pending:", [i.get("id") for i in (fm.get("pending") or [])])
print(" completed:", [(i.get("id"), i.get("outcome")) for i in (fm.get("completed") or [])])
rec = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=6", headers=HEADERS).json().get("data",[])
print("RECENT POSTS:")
for p in rec: print(" ", p.get("id"), "|", (p.get("title") or "")[:105])
for f in ["results/exp_head_dim_64.md","results/exp_activation_silu.md"]:
    print(f, requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/{f}", headers=HEADERS).status_code)
print("\nRESULT LATEST:", json.loads(Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace/result_latest.json").read_text()).get("status"))
