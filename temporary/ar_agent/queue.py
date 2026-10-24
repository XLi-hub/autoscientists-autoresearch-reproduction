import json, requests, yaml
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; A="ar_20261022hi_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{A}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":A}
API="http://localhost:3000/api/v1"; SHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
TEAM_WS="032e5282-1362-4eef-9226-3d40299116aa"
posts=requests.get(f"{API}/posts?workshop={SHOP}&limit=50",headers=H).json().get("data",[])
ids={}
for p in posts:
    if "exp_muon_mom_ramp60" in p["title"]: ids["mom"]=p["id"]
    if "exp_matrix_lr_bracket" in p["title"]: ids["mat"]=p["id"]
print("POST IDS:", ids, "| total posts:", len(posts))

def pf(r):
    c=r.get("content","");p=c.split("---");return yaml.safe_load(p[1]) if len(p)>=3 else {}
q=requests.get(f"{API}/workspaces/{TEAM_WS}/files/queue.md",headers=H).json()
qm=pf(q); claims=qm.get("claims",{}) or {}; pending=qm.get("pending",[]) or []
existing={i["id"] for i in pending}
new=[
 {"id":"exp_muon_mom_ramp60","description":"Shorten Muon momentum ramp min(step/300,1) -> min(step/60,1) so momentum reaches designed 0.95 within the ~100-step budget",
  "priority":"high","axis":"muon_momentum_ramp","direction":"decrease","value":"60",
  "diff":"In train.py get_muon_momentum(): change `frac = min(step / 300, 1)` to `frac = min(step / 60, 1)`. Endpoint 0.95 unchanged.",
  "proposed_by":A,"proposal_post":ids.get("mom"),"discussion_pending":True,
  "rationale":"300-step ramp was calibrated for long runs; fixed 300s budget yields ~100 steps so effective momentum tops out ~0.88"},
 {"id":"exp_matrix_lr_lo","description":"MATRIX_LR 0.04 -> 0.02 (bracket low probe)",
  "priority":"medium","axis":"matrix_lr","direction":"decrease","value":"0.02",
  "diff":"In train.py change `MATRIX_LR = 0.04` to `MATRIX_LR = 0.02`.",
  "proposed_by":A,"proposal_post":ids.get("mat"),"discussion_pending":True},
 {"id":"exp_matrix_lr_hi","description":"MATRIX_LR 0.04 -> 0.08 (bracket high probe)",
  "priority":"medium","axis":"matrix_lr","direction":"increase","value":"0.08",
  "diff":"In train.py change `MATRIX_LR = 0.04` to `MATRIX_LR = 0.08`.",
  "proposed_by":A,"proposal_post":ids.get("mat"),"discussion_pending":True},
]
added=[]
for it in new:
    if it["id"] not in existing:
        pending.append(it); added.append(it["id"])
qm["claims"]=claims; qm["pending"]=pending
body=q.get("content","").split("---",2)[-1]
content="---\n"+yaml.safe_dump(qm,sort_keys=False)+"---"+body
r=requests.put(f"{API}/workspaces/{TEAM_WS}/files/queue.md",headers={**H,"If-Match":str(q.get("version",0))},json={"content":content})
print("QUEUE PUT", r.status_code, "added:", added)
print("PENDING IDS NOW:", [i["id"] for i in pending], "CLAIMS:", claims)
