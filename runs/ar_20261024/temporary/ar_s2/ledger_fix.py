import json, os, requests, time
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"; AGENT_NAME="ar_20261024_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
for attempt in range(3):
    r=requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/unqueued_axes.md",headers=HEADERS).json()
    ver=r.get("version"); c=r.get("content","")
    old_wd="| warmdown_ratio | increase | 0.75 | analyst2 c1 audit; 2be7ed75 | tested | 2026-10-24 | 0.25 arm DISCARD at +0.0049 (inside 2-sigma) with no step-count gain; axis OPEN. The 0.75 row below still completes the 3-point bracket. |"
    new_wd="| warmdown_ratio | increase | 0.75 | analyst2 c1 audit; 2be7ed75 | queued | 2026-10-24 | gq bracket high arm, still queued as exp_gq_warmdown_075 (medium priority). Earlier decay on an undertrained base has low expected value; run after adam_betas and MLP-2x. |"
    old_mlp="| mlp_expansion | increase | 5 (bracket high) | analyst1 c1 audit; 40efd6b0 | queued | 2026-10-24 | 3x KEEPed (1.169258 -> 1.158107). 5x arm still queued by throughput; gq filed the 2x arm this cycle -> a 2/3/5 bracket when all three land. |"
    new_mlp="| mlp_expansion | increase | 5 (bracket high) | analyst1 c1 audit; 40efd6b0 | queued | 2026-10-24 | Still queued by throughput (exp_tput_mlp_exp_5). With the 3x KEEP and gq's 2x arm this cycle, the three arms form a 2/3/5 bracket that separates cheaper-step from smaller-capacity. |"
    assert old_wd in c, "wd row not found"
    assert old_mlp in c, "mlp row not found"
    c=c.replace(old_wd,new_wd).replace(old_mlp,new_mlp)
    c=c.replace("version: 5","version: 6",1).replace("merged v5 by analyst3","merged v6: analyst3 v5 + analyst2 c2")
    resp=requests.put(f"{API}/workspaces/{MAIN}/files/knowledge/unqueued_axes.md",
        headers={**HEADERS,"If-Match":str(ver)},json={"content":c})
    print("PUT",resp.status_code,resp.text[:200])
    if resp.status_code==200: break
    time.sleep(2)
