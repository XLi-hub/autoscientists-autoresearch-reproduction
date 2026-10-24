import json, math, requests, yaml
from datetime import datetime, timezone
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu2"; MY_TEAM="gradient-quality"; TEAM_WS_ID="005cb9ec-6fce-4bba-9340-21c08ab914c5"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
NOW = datetime.now(timezone.utc).isoformat()
def pf(r):
    c=r.get("content","").split("---"); return yaml.safe_load(c[1]) if len(c)>=3 else {}

# fresh champion (Step 5 race check)
ch = requests.get(f"{API}/workspaces/{MAIN}/files/champion.md", headers=H).json()
cf = pf(ch); champ_metric = float(cf.get("metric_value"))
our = 1.162970; delta = our - champ_metric
print("champion:", cf.get("experiment_id"), champ_metric, "v", ch.get("version"), "delta(minimize)=", round(delta,6))
outcome = "KEEP" if our < champ_metric else "DISCARD"
print("outcome", outcome)

md = f"""# exp_gq_warmdown_025 — WARMDOWN_RATIO 0.5 -> 0.25

- metric: **val_bpb = 1.162970**
- outcome: **{outcome}** vs champion {cf.get('experiment_id')} = {champ_metric} (worse by {abs(delta):.6f})
- agent: {AGENT_NAME} (GPU 1), team: gradient-quality
- timestamp: {NOW}
- axis: warmdown_ratio | direction: decrease | value: 0.25 (current 0.5)
- base: current champion (TOTAL_BATCH_SIZE 2**18, MLP_EXPANSION 3, DEVICE_BATCH_SIZE 64)

## Change
```python
WARMDOWN_RATIO = 0.25   # was 0.5
```
LR holds at 1.0 until progress = 0.75, then anneals to 0 over the last 25% (was the last 50%).

## Result
| run | val_bpb | steps | tok/s |
|---|---|---|---|
| champion (warmdown 0.5) | 1.158107 | 410 | 348K |
| this run (warmdown 0.25) | 1.162970 | 416 | 352K |
| seed noise band (2 sigma) | +/-0.0057 | | |

- Delta -0.004863 (worse) is INSIDE the 2-sigma seed-noise band (0.0057), so this is not
  distinguishable from noise on one seed. It does not refute the axis, but there is no evidence
  of improvement, and holding LR high longer did not increase steps materially (416 vs 410; the
  step count is set by throughput, not by the LR schedule).
- The other arm (exp_gq_warmdown_075) remains open; a bracket minimum at 0.5 is NOT established.

## Training Dynamics
- 416 optimizer steps in 300.7s; 109.1M tokens; ~352K tok/s; MFU 7.65%; peak VRAM 20.7GB.
- Loss 9.0 -> 3.251; still decreasing at end (undertrained), 0.0 remaining budget.
- Final ~10% of steps ran at LR multiplier < 0.05 in both runs, so the exercise of the tail is brief.
"""
print("md PUT", requests.put(f"{API}/workspaces/{MAIN}/files/results/exp_gq_warmdown_025.md", headers=H, json={"content": md}).status_code)

# queue: release + complete
q = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=H).json()
fm = yaml.safe_load(q.get("content","").split("---")[1])
fm.get("claims",{}).pop(AGENT_NAME, None)
pending = fm.get("pending") or []; completed = fm.get("completed") or []; rem=[]
for it in pending:
    if it.get("id")=="exp_gq_warmdown_025":
        it=dict(it); it.update({"completed_at":NOW,"completed_by":AGENT_NAME,"outcome":outcome,
                                 "val_score":our,"champion_at_completion":champ_metric})
        completed.append(it)
    else: rem.append(it)
fm["pending"]=rem; fm["completed"]=completed
body=q.get("content","").split("---",2)[-1]
new=f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}"
assert yaml.safe_load(new.split('---')[1])==fm
print("queue PUT", requests.put(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md",
      headers={**H,"If-Match":str(q.get("version",0))}, json={"content":new}).status_code)

# dead ends
if outcome=="DISCARD":
    de = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/dead_ends.md", headers=H).json()
    entry=(f"\n- exp_id: exp_gq_warmdown_025\n  axis: warmdown_ratio\n  direction: decrease\n  value: 0.25\n"
           f"  delta: {delta:+.6f} (worse; inside 2-sigma band 0.0057)\n  family: exp_gq\n  date: 2026-10-24\n"
           f"  reason: Shorter anneal gave no improvement and no step-count gain (416 vs 410). Single seed, inside noise; axis not refuted. Arm B (0.75) still open.\n")
    print("dead_ends PUT", requests.put(f"{API}/workspaces/{TEAM_WS_ID}/files/dead_ends.md",
          headers={**H,"If-Match":str(de.get("version",0))}, json={"content":de.get("content","")+entry}).status_code)

# post
r = requests.post(f"{API}/posts", headers=H, json={
 "workshop": WORKSHOP,
 "title": f"[RESULT] exp_gq_warmdown_025: val_bpb={our} ({outcome}) — inside noise band",
 "content": (f"## Experiment\nWARMDOWN_RATIO 0.5 -> 0.25 (hold LR at peak until 75% of budget, then anneal), "
             f"on the current champion base (TOTAL_BATCH_SIZE 2**18, MLP_EXPANSION 3).\n\n"
             f"## Result\nval_bpb: {our}\nChampion: {champ_metric} ({cf.get('experiment_id')})\n"
             f"Delta: {delta:+.6f} (worse)\nOutcome: {outcome}\n"
             f"Steps: 416 in 300.7s vs 410 champion; 109.1M tokens; ~352K tok/s; MFU 7.65%\n\n"
             f"## Reading\nDelta is inside the measured 2-sigma seed band (0.0057), so this is not "
             f"distinguishable from noise. No step-count gain either, so the 'hold LR high to buy steps' "
             f"intuition does not apply — step count is throughput-bound. Arm B (0.75) stays open; "
             f"a bracket minimum at 0.5 is not established.\n\n## Team\ngradient-quality"),
 "tags": [f"team:{MY_TEAM}","type:result",f"outcome:{outcome.lower()}"]})
print("post", r.status_code)
post_id = r.json().get("post",{}).get("id") if r.ok else None

# sentinel
from pathlib import Path
p = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace/result_latest.json")
d = json.loads(p.read_text())
d.update({"status":"posted","posted_to_workshop":True,"exp_id":"exp_gq_warmdown_025","val_score":our,
          "direction":"minimize","result_post_id":post_id,"posted_at":NOW,
          "champion_at_completion":champ_metric,"outcome":outcome})
p.write_text(json.dumps(d, indent=2, default=str))
print("sentinel posted")
