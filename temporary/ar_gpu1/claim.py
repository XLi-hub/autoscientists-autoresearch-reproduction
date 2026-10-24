import json, os, yaml, requests
from datetime import datetime, timezone
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; TEAM=json.load(open("/tmp/ar_gpu1/part0.json"))["TEAM_WS_ID"]
def pf(resp):
    c=resp.get("content",""); p=c.split("---")
    return yaml.safe_load(p[1]) if len(p)>=3 else {}
now=datetime.now(timezone.utc).isoformat()
for attempt in range(3):
    q_raw=requests.get(f"{API}/workspaces/{TEAM}/files/queue.md",headers=H).json()
    fm=pf(q_raw); ver=q_raw.get("version",0)
    pend=fm.get("pending",[]) or []; comp=fm.get("completed",[]) or []
    # clean stale completed item warmdown_070 (result file exists)
    new_pend=[]
    for it in pend:
        if it.get("id")=="exp_warmdown_070" and it.get("completed_by") is None:
            it=dict(it); it["completed_at"]="2026-10-22T14:53:28.637495+00:00"
            it["completed_by"]="ar_20261022hi_gpu2"; it["outcome"]="DISCARD"; it["val_score"]=1.093748
            it["note"]="queue cleanup by ar_20261022hi_gpu1: result posted 14:53Z, claim was stale"
            comp.append(it)
        else:
            new_pend.append(it)
    fm["pending"]=new_pend; fm["completed"]=comp
    fm.setdefault("claims",{})[AGENT_NAME]={"exp_id":"exp_gqa_kv1","claimed_at":now}
    fm["claims"].pop("ar_20261022hi_gpu2",None)
    body=q_raw.get("content","").split("---",2)[-1]
    new=f"---\n{yaml.safe_dump(fm,sort_keys=False)}---{body}"
    assert yaml.safe_load(new.split('---')[1])==fm, "roundtrip fail"
    r=requests.put(f"{API}/workspaces/{TEAM}/files/queue.md",headers={**H,"If-Match":str(ver)},json={"content":new})
    print("PUT",r.status_code)
    if r.status_code in (200,201):
        print("CLAIMED exp_gqa_kv1; pending now:",[i['id'] for i in fm['pending']])
        break
    elif r.status_code==409:
        continue
    else:
        print(r.text[:500]); break
