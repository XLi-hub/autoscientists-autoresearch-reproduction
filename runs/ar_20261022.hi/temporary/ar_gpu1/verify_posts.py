import json, requests
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
ps=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=10",headers=H).json().get("data",[])
for p in ps[:8]:
    if "exp_gqa_kv1" in p.get("title",""):
        print(p["id"], "|", p.get("created_at") or p.get("createdAt"), "|", p["title"][:100])
# update sentinel with both ids
ws="/root/autodl-tmp/ar_20261022.hi/agents/ar_20261022hi_gpu1/workspace/result_latest.json"
d=json.load(open(ws))
res=[p["id"] for p in ps if p["title"].startswith("[RESULT] exp_gqa_kv1")]
nm=[p["id"] for p in ps if p["title"].startswith("[NEAR-MISS] exp_gqa_kv1")]
d["result_post_id"]=res[0] if res else None
d["near_miss_post_id"]=nm[0] if nm else None
open(ws,"w").write(json.dumps(d,indent=2,default=str))
print("sentinel post ids:",res,nm)
