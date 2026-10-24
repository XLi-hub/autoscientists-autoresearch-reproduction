import json, requests, yaml
FOCUS="/root/autodl-tmp/ar_20261022.hi"; AGENT="ar_20261022hi_analyst1"
c=json.load(open(f"{FOCUS}/agents/{AGENT}/credentials.json"))
H={"Authorization":f"Bearer {c['api_key']}","Content-Type":"application/json","X-Agent-Name":c['agent_name']}
API="http://localhost:3000/api/v1"; TEAM="54202fe1-b766-43f1-b374-9e4ed188c153"

def pf(resp):
    p=resp.get("content","").split("---")
    return (yaml.safe_load(p[1]) or {}) if len(p)>=3 else {}

raw=requests.get(f"{API}/workspaces/{TEAM}/files/queue.md",headers=H).json()
fm=pf(raw); version=raw.get("version",0)
pending=fm.get("pending",[]) or []; claims=fm.get("claims",{}) or {}
print("before: pending",len(pending),"claims",claims,"version",version)
for it in pending: print("  -",it.get("id"),it.get("priority"))

new_items=[
 {"id":"exp_gqa_kv1","priority":"high","bold_bet":True,
  "description":"n_kv_head 4 -> 1 (GQA 4:1) at unchanged width 512: -7.9% FLOPs/token (-18.9M), params 50.3M -> 34.6M (-31%), predicted 719 -> ~776 steps (+8%). Structural step-buyer; does NOT touch n_embd/n_head/MLP.",
  "axis":"n_kv_head","direction":"decrease","value":"1","current_value":"4",
  "diff":"In build_model_config() change `n_layer=depth, n_head=num_heads, n_kv_head=num_heads, n_embd=model_dim,` to `n_layer=depth, n_head=num_heads, n_kv_head=max(1, num_heads // 4), n_embd=model_dim,`. Single line, unconditional. VRAM falls; do NOT change DEVICE_BATCH_SIZE.",
  "proposed_by":AGENT,"proposal_post":"a1018d68-44ba-4f45-aff9-b27e246ec223",
  "discussion_pending":True,"expected_delta":"-0.005 to -0.009","confidence":"medium"},
 {"id":"exp_unembedding_lr_lo","priority":"medium",
  "description":"UNEMBEDDING_LR 0.004 -> 0.0013 (3x lower; low arm of the cold readout-LR bracket). lm_head only, 4.19M params, effective LR 0.0049 vs embedding group 0.735.",
  "axis":"unembedding_lr","direction":"decrease","value":"0.0013","current_value":"0.004",
  "diff":"In train.py change `UNEMBEDDING_LR = 0.004  # learning rate for lm_head (Adam)` to `UNEMBEDDING_LR = 0.0013`. Only the lm_head param group uses this constant.",
  "proposed_by":AGENT,"proposal_post":"eadcb5fd-edfd-478e-b066-868c65424058",
  "discussion_pending":True,"paired_with":"exp_unembedding_lr_hi","confidence":"low-medium"},
 {"id":"exp_unembedding_lr_hi","priority":"low",
  "description":"UNEMBEDDING_LR 0.004 -> 0.012 (3x higher; high arm of the readout-LR bracket, tests readout starvation at 719 updates).",
  "axis":"unembedding_lr","direction":"increase","value":"0.012","current_value":"0.004",
  "diff":"In train.py change `UNEMBEDDING_LR = 0.004  # learning rate for lm_head (Adam)` to `UNEMBEDDING_LR = 0.012`. Only the lm_head param group uses this constant.",
  "proposed_by":AGENT,"proposal_post":"eadcb5fd-edfd-478e-b066-868c65424058",
  "discussion_pending":True,"paired_with":"exp_unembedding_lr_lo","confidence":"low-medium"},
]
existing={it.get("id") for it in pending}
added=[]
for it in new_items:
    if it["id"] not in existing:
        pending.append(it); added.append(it["id"])

# Demote aspect_ratio_80 to medium: mandatory Step 1e scale-up probe stays in queue,
# but new evidence (depth_10, ve_all_layers) predicts it DISCARDs.
for it in pending:
    if it.get("id")=="exp_aspect_ratio_80":
        it["priority"]="medium"
        it["prediction_note"]=("scale_up_probe (Step 1e mandate); NEW EVIDENCE 2026-10-22T12:50Z predicts DISCARD: "
            "-31% steps at the current-rung rate = +0.025, capacity direction at best neutral "
            "(ve_all_layers +33% params/0 step cost = +0.006 worse). Read as a falsification probe for H-capacity."
        )

# Empirical priors from logs/experiments.jsonl (flat records)
import collections, math
recs=[json.loads(l) for l in open(f"{FOCUS}/logs/experiments.jsonl") if l.strip()]
pri=collections.defaultdict(list)
for r in recs:
    ax=r.get("axis"); d=r.get("direction_of_change") or r.get("direction")
    dv=r.get("delta")
    if ax and d and dv is not None: pri[(ax,d)].append(abs(float(dv)))
axis_scores={k:sum(v)/len(v) for k,v in pri.items() if len(v)>=3}
cold={k for k,v in pri.items() if len(v)<3}
for it in pending:
    for k in list(pri):
        if k[0]==it.get("axis"): cold.add(k)
# any axis not in pri is cold too
for it in pending:
    if (it.get("axis"),it.get("direction")) not in pri: cold.add((it.get("axis"),it.get("direction")))

PR={"high":0,"medium":1,"low":2}
OPP={"increase":"decrease","decrease":"increase"}
cnt=collections.Counter((it.get("axis"),it.get("direction")) for it in pending if it.get("axis"))
def rank(it):
    ax,dr=it.get("axis"),it.get("direction"); key=(ax,dr); opp=(ax,OPP.get(dr,dr))
    if cnt.get(opp,0)>=2 and cnt.get(key,0)<=1: tier=-1
    elif key in cold or (ax,None) in cold: tier=0
    else:
        s=axis_scores.get(key,0); tier=2 if s<0.003 else 1
    return (tier, PR.get(it.get("priority"),1), -axis_scores.get(key,0))
pending.sort(key=rank)
fm["pending"]=pending; fm["claims"]=claims
body=raw.get("content","").split("---",2)[-1]
newc="---\n"+yaml.safe_dump(fm,sort_keys=False)+"---"+body
r=requests.put(f"{API}/workspaces/{TEAM}/files/queue.md",headers={**H,"If-Match":str(version)},json={"content":newc})
print("PUT",r.status_code,"added:",added)
print({k:v for k,v in (r.json() or {}).items() if k in ("version","error")})
raw2=requests.get(f"{API}/workspaces/{TEAM}/files/queue.md",headers=H).json()
fm2=pf(raw2)
print("\nafter: pending",len(fm2.get("pending",[])),"claims",fm2.get("claims"))
for it in fm2.get("pending",[]): print(f"  {it.get('priority'):7s} {it.get('id'):26s} axis={it.get('axis'):18s} dir={it.get('direction')}")
