import json, yaml, requests
from datetime import datetime, timezone
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; TEAM=json.load(open("/tmp/ar_gpu1/part0.json"))["TEAM_WS_ID"]
def pf(r):
    c=r.get("content",""); p=c.split("---"); return yaml.safe_load(p[1]) if len(p)>=3 else {}
now=datetime.now(timezone.utc).isoformat()
for attempt in range(3):
    q=requests.get(f"{API}/workspaces/{TEAM}/files/queue.md",headers=H).json(); fm=pf(q)
    ids=[i.get("id") for i in (fm.get("pending") or [])]
    if "exp_wd_0p0" not in ids: print("NOT PENDING",ids); break
    fm.setdefault("claims",{})[AGENT_NAME]={"exp_id":"exp_wd_0p0","claimed_at":now}
    body=q.get("content","").split("---",2)[-1]
    new=f"---\n{yaml.safe_dump(fm,sort_keys=False)}---{body}"
    assert yaml.safe_load(new.split('---')[1])==fm
    r=requests.put(f"{API}/workspaces/{TEAM}/files/queue.md",headers={**H,"If-Match":str(q.get("version",0))},json={"content":new})
    print("claim PUT",r.status_code,"pending:",ids)
    if r.status_code in (200,201): break
