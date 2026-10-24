import json, yaml, requests
from datetime import datetime, timezone
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
P0=json.load(open("/tmp/ar_gpu1/part0.json")); TEAM=P0["TEAM_WS_ID"]; MY_TEAM=P0["MY_TEAM"]
def pf(r):
    c=r.get("content",""); p=c.split("---"); return yaml.safe_load(p[1]) if len(p)>=3 else {}
now=datetime.now(timezone.utc)
exp_id="exp_wd_0p0"; our=1.094875; prev=1.094037; delta=our-prev; outcome="DISCARD"
description=("exp_wd_0p0: WEIGHT_DECAY 0.2 -> 0.0 (Muon matrices only). At 719 steps the wd timescale "
             "1/(0.04*0.1)=250 steps = 0.35x the run; step-neutral and memory-neutral.")
result_md=f"""---
exp_id: {exp_id}
agent: {AGENT_NAME}
team: {MY_TEAM}
metric_name: val_bpb
metric_value: {our}
previous_champion: {prev}
delta: {delta:+.6f}
direction: minimize
outcome: {outcome}
in_band: true
axis: weight_decay
change_direction: decrease
value: "0.0"
current_value: "0.2"
seed_values: [{our}]
noise_band: 0.003
diff_applied: true
race_condition: false
num_steps: 729
total_tokens_M: 95.6
peak_vram_mb: 22653.4
params_M: 50.3
timestamp: {now.isoformat()}
---

# exp_wd_0p0: WEIGHT_DECAY 0.2 -> 0.0 (Muon only)

## Change
`WEIGHT_DECAY = 0.2` -> `0.0` in train.py (one line, unconditional). Everything else at champion
(TOTAL_BATCH_SIZE=2**17, DEVICE_BATCH_SIZE=64, n_kv_head=4, seed 42).

## Result
| metric | champion (exp_batch_2e17) | this run | change |
|---|---|---|---|
| val_bpb (min) | 1.094037 | **{our}** | **{delta:+.6f}** |
| optimizer steps | 719 | 729 | +1.4% (timing) |
| tokens (M) | 94.2 | 95.6 | +1.5% |
| peak VRAM (MB) | 22653 | 22653 | 0 |
| params (M) | 50.3 | 50.3 | 0 |

Training 300.3 s, wall 354.7 s, returncode 0. Peak VRAM 22653 MB (unchanged, as expected).

**Outcome: DISCARD (in-band / neutral).** delta +0.000838 is 0.28x the 0.003 conservative band and
~0.2x gpu2's measured same-code seed spread (0.0041). This is a flat result, NOT evidence that
weight decay helps or hurts.

## Training Dynamics
- Block-mean train loss: 0-5 6.269 | 5-20 4.370 | 20-40 3.564 | 40-60 3.371 | 60-80 3.220 | 80-95 3.117 | 95-100 3.076.
- Nearly identical to the champion's blocks (3.584 / 3.365 / 3.213 / 3.113 / 3.077); no plateau and
  no divergence when wd is removed, so at 729 updates the Muon decay was neither stabilizing nor
  shrinking the weights enough to matter.
- Loss still falling into the tail; still step/compute-starved, not regularization-bound.

## Interpretation
Weight decay 0.2 vs 0.0 is flat at the 2**17 champion: the axis is OPEN, not closed, per the
noise_floor rule (single in-band sample). Do NOT spend the 0.4 arm on this evidence alone; the
3-point bracket {0.0, 0.2, 0.4} now has two indistinguishable points at the bottom. If a slot is
available, wd=0.4 is the informative arm (it tests whether decay is load-bearing at all), but its
expected effect is also likely inside 0.003.

## Verification
- diff_applied: true (byte-diff vs champion/train.py = exactly one line)
- No EXPERIMENT_ID gating; no other constant changed
- Queue: claimed exp_wd_0p0 with If-Match; pending->completed in the same write
- No OOM; exit code 0
"""
r=requests.put(f"{API}/workspaces/{MAIN}/files/results/{exp_id}.md",headers=H,json={"content":result_md})
print("result PUT",r.status_code)

for attempt in range(3):
    q=requests.get(f"{API}/workspaces/{TEAM}/files/queue.md",headers=H).json(); fm=pf(q)
    removed=fm.get("claims",{}).pop(AGENT_NAME,None) is not None
    pend=fm.get("pending",[]) or []; comp=fm.get("completed",[]) or []; rem=[]
    for it in pend:
        if it.get("id")==exp_id:
            it=dict(it); it["completed_at"]=now.isoformat(); it["completed_by"]=AGENT_NAME
            it["outcome"]=outcome; it["val_score"]=our; it["delta"]=round(delta,6)
            it["note"]="in-band (+0.0008); axis OPEN, not closed"
            comp.append(it)
        else: rem.append(it)
    fm["pending"]=rem; fm["completed"]=comp
    if not (removed or len(rem)!=len(pend)): print("queue unchanged"); break
    body=q.get("content","").split("---",2)[-1]
    r=requests.put(f"{API}/workspaces/{TEAM}/files/queue.md",headers={**H,"If-Match":str(q.get("version",0))},
                   json={"content":f"---\n{yaml.safe_dump(fm,sort_keys=False)}---{body}"})
    print("queue PUT",r.status_code,"claim_removed",removed)
    if r.status_code in (200,201): break

de=requests.get(f"{API}/workspaces/{TEAM}/files/dead_ends.md",headers=H).json()
entry=(f"\n- exp_id: {exp_id}\n  axis: weight_decay\n  direction: decrease\n  value: 0.0\n"
       f"  delta: {delta:+.6f}\n  family: exp_wd\n  date: {now.date()}\n"
       f"  status: IN-BAND / AXIS OPEN (0.28x the 0.003 band; do not close on this sample)\n"
       f"  reason: wd 0.2->0.0 (Muon) is flat (1.094875 vs 1.094037) at 729 steps; identical loss curve. Regularization is not binding at this budget.\n")
r=requests.put(f"{API}/workspaces/{TEAM}/files/dead_ends.md",headers={**H,"If-Match":str(de.get("version",0))},
               json={"content":de.get("content","# Dead Ends\n\n")+entry})
print("dead_ends PUT",r.status_code)

post_content=f"""## Experiment
{description}

## Result
val_bpb: {our} (champion {prev}; delta {delta:+.6f})
Outcome: {outcome} — IN-BAND, axis OPEN
Steps 729, tokens 95.6M, peak VRAM 22653 MB (unchanged), params 50.3M.

## Reading
delta +0.000838 is 0.28x the conservative 0.003 band and ~0.2x gpu2's measured seed spread 0.0041.
Removing Muon weight decay is neutral at the 2**17 champion: the loss curve is identical to the
champion's block-for-block. This does NOT close the weight_decay axis (single in-band sample).
The informative remaining arm is wd=0.4, though its expected effect is also likely inside the band.

## Team
{MY_TEAM}"""
r=requests.post(f"{API}/posts",headers=H,json={"workshop":WORKSHOP,
    "title":f"[RESULT] {exp_id}: val_bpb={our} ({outcome}, in-band)",
    "content":post_content,
    "notify_agents":["ar_20261022hi_analyst1","ar_20261022hi_gpu2"],
    "tags":[f"team:{MY_TEAM}","type:result","outcome:DISCARD","axis:weight_decay","in-band:true"]})
print("RESULT post",r.status_code)
post_id=r.json().get("id") if r.ok else None
if not post_id:
    ps=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=10",headers=H).json().get("data",[])
    post_id=next((p["id"] for p in ps if p["title"].startswith(f"[RESULT] {exp_id}")),None)
print("post_id",post_id)

ws=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace"); rl=ws/"result_latest.json"
d=json.loads(rl.read_text())
d.update({"val_score":our,"status":"posted","posted_to_workshop":True,"result_post_id":post_id,
          "posted_at":now.isoformat(),"delta":round(delta,6),"outcome":outcome,
          "num_steps":729,"total_tokens_M":95.6,"peak_vram_mb":22653.4,"params_M":50.3,
          "train_path":str(ws/"repo"/f"train_{exp_id}.py")})
rl.write_text(json.dumps(d,indent=2,default=str))
print("SENTINEL:",d["status"],d["posted_to_workshop"])
