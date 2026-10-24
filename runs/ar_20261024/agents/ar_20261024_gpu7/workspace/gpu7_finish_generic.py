import json, os, re, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
import requests, yaml

DRY = os.environ.get("DRY_RUN", "1") == "1"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu7"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
     "X-Agent-Name": AGENT_NAME}
API = "http://localhost:3000/api/v1"
MAIN = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
TEAM_WS = "005cb9ec-6fce-4bba-9340-21c08ab914c5"
ws = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace")
rep = ws / "repo"
NOW = datetime.now(timezone.utc).isoformat()

BLURB = {
 "exp_gq_matrix_lr_lo": (
   "MATRIX_LR 0.04 -> 0.02 in `champion/train.py` (single variable). Low arm of the first-ever "
   "Muon-LR bracket; the axis had n=0 before this pair. MATRIX_LR is the Muon LR for all eight "
   "blocks' matrix weights: 16.78M/41.94M params (40.0%) and 80.0% of the 6N FLOP-relevant count. "
   "0.02 is also setup_optimizer()'s signature default and the value that classic LR~batch (or "
   "LR~sqrt(batch)) scaling predicts after TOTAL_BATCH_SIZE fell 2**19 -> 2**17.",
   "`muon_step_fused` decays as `lr * wd * p`, so halving MATRIX_LR also halves effective per-step "
   "decay from 0.8% to 0.4% at progress 0. This arm is LR+WD, not LR alone. Companion arm "
   "exp_gq_matrix_lr_hi (0.08) came back +0.003688, inside the 2-sigma band.",
 ),
}


def pf(resp):
    parts = resp.get("content", "").split("---")
    return yaml.safe_load(parts[1]) if len(parts) >= 3 else {}


def body_of(resp):
    return resp.get("content", "").split("---", 2)[-1]


sentinel = json.loads((ws / "result_latest.json").read_text())
EXP_ID = sentinel["exp_id"]
item = sentinel.get("item") or {}
axis = item.get("axis", "matrix_lr"); direction = item.get("direction", "decrease")
value = item.get("value"); current_value = item.get("current_value")
log = Path(sentinel["stdout_path"]).read_text(errors="ignore")

m = re.search(r"val_bpb:\s+([0-9.]+)", log)
if not m:
    print("HARD FAIL: no val_bpb in stdout"); sys.exit(1)
our_metric = float(m.group(1))


def grab(name, cast=float):
    mm = re.search(rf"{name}:\s+([0-9.]+)", log)
    return cast(mm.group(1)) if mm else None


steps = grab("num_steps", int); tokens_M = grab("total_tokens_M")
peak_vram = grab("peak_vram_mb"); mfu = grab("mfu_percent"); params_M = grab("num_params_M")

pts = [(int(a), float(b)) for a, b in re.findall(r"step (\d+) \(\s*[\d.]+%\) \| loss: ([0-9.]+)", log)]
loss_curve = None
if len(pts) > 10:
    losses = [p[1] for p in pts]; rng = max(losses) - min(losses)
    final_step, final_loss = pts[-1]
    near = min(pts, key=lambda p: abs(p[0] - int(0.8 * final_step)))
    drop20 = near[1] - final_loss
    loss_curve = dict(final_step=final_step, final_loss=final_loss, loss_at_80pct=near[1],
                      step_at_80pct=near[0], final20_drop=drop20,
                      final20_pct=100 * drop20 / rng if rng else 0.0)
    print("[DYNAMICS]", json.dumps(loss_curve, indent=2))

champ_raw = requests.get(f"{API}/workspaces/{MAIN}/files/champion.md", headers=H).json()
champ = pf(champ_raw)
metric_name = champ.get("metric_name"); dirn = champ.get("direction", "minimize")
cur = champ.get(metric_name) if metric_name else None
if cur is None: cur = champ.get("metric_value")
if cur is None:
    print("HARD FAIL: champion metric unparseable; refusing to default to inf"); sys.exit(1)
cur = float(cur); champ_version = champ_raw.get("version", 0); exp_champ = champ.get("experiment_id")
delta = our_metric - cur; improvement = cur - our_metric
print(f"[CMP] ours={our_metric} champ={cur} ({exp_champ}) delta={delta:+.6f}")

nf = requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/noise_floor_data.md", headers=H)
sigma = 0.002865
if nf.status_code == 200:
    sigma = float(pf(nf.json()).get("sigma_estimate", sigma) or sigma)
band2 = 2 * sigma
print(f"[NOISE] sigma={sigma} 2sigma={band2:.6f}")
better = our_metric < cur if dirn == "minimize" else our_metric > cur
inside_band = abs(delta) <= band2
outcome = ("KEEP" if (better and not inside_band) else
           "KEEP-UNCONFIRMED" if better else "DISCARD")
print(f"[PLAN] outcome={outcome} inside_band={inside_band}")

blurb, confound = BLURB.get(EXP_ID, ("", ""))
if better and inside_band:
    interp = ("the improvement is INSIDE the 2-sigma band, so under the Step 7.0 multi-seed gate it "
              "CANNOT be promoted on one seed. Champion is unchanged. A same-code second seed "
              "(seed 43) of this arm is required before any promotion; the pair also contributes a "
              "noise sample at the 1.088 base.")
elif better:
    interp = "Outside the 2-sigma band and strictly better: promotable."
elif inside_band:
    interp = ("inside the 2-sigma band, so this is NOT a refutation of the axis and NOT a near-miss; "
              "matrix_lr remains open.")
else:
    interp = "Outside the 2-sigma band and worse: axis direction refuted."
dyn = ""
if loss_curve:
    dyn = (f"- Steps: {loss_curve['final_step']}, tokens: {tokens_M}M, peak VRAM: {peak_vram:.0f} MB, MFU: {mfu:.2f}%\n"
           f"- Final-20% loss drop: {loss_curve['final20_drop']:.6f} = {loss_curve['final20_pct']:.2f}% of the run's loss range (>1% => still undertrained).\n"
           f"- Loss at ~80% ({loss_curve['step_at_80pct']}): {loss_curve['loss_at_80pct']:.6f} -> final {loss_curve['final_loss']:.6f}")

result_md = f"""---
exp_id: {EXP_ID}
axis: {axis}
direction: {direction}
value: {value}
current_value: {current_value}
val_bpb: {our_metric}
champion_at_measure: {cur} ({exp_champ})
delta_ours_minus_champ: {delta:+.6f}
outcome: {outcome}
team: gradient-quality
agent: {AGENT_NAME}
timestamp: {NOW}
---

# {EXP_ID}

## Experiment

{blurb}

**Pre-registered confound.** {confound}

## Result

- val_bpb = **{our_metric}**
- Champion at measure: {cur} ({exp_champ}, champion.md v{champ_version})
- delta (ours - champion) = **{delta:+.6f}**; 2-sigma band = +/-{band2:.6f} (sigma {sigma})
- Outcome: **{outcome}** — {interp}

## Training Dynamics

{dyn}

## Reproduction

```bash
CUDA_VISIBLE_DEVICES=1 HF_HOME=/root/autodl-tmp/cache/huggingface HF_HUB_OFFLINE=1 python train.py
```
Stamped: `agents/{AGENT_NAME}/workspace/repo/train_{EXP_ID}.py`

## Provenance

- Agent: {AGENT_NAME} (GPU 1), team gradient-quality
- Timestamp: {NOW}
- Proposal: 552e2db3-5221-498b-a61e-83f155016948 (ar_20261024_analyst1)
"""
print("=" * 80); print(result_md)
if DRY:
    print("[DRY RUN] no writes"); sys.exit(0)

r = requests.put(f"{API}/workspaces/{MAIN}/files/results/{EXP_ID}.md", headers=H, json={"content": result_md})
print("[RESULT FILE]", r.status_code)

q_raw = requests.get(f"{API}/workspaces/{TEAM_WS}/files/queue.md", headers=H).json()
q_fm = pf(q_raw)
claim_removed = q_fm.get("claims", {}).pop(AGENT_NAME, None) is not None
pending = q_fm.get("pending", []) or []; completed = q_fm.get("completed", []) or []
remaining = []
for it in pending:
    if it.get("id") == EXP_ID:
        it = dict(it); it.update(completed_at=NOW, completed_by=AGENT_NAME, outcome=outcome,
                                 val_score=our_metric, delta=delta); completed.append(it)
    else:
        remaining.append(it)
q_fm["pending"] = remaining; q_fm["completed"] = completed
if claim_removed or len(remaining) != len(pending):
    new = f"---\n{yaml.safe_dump(q_fm, sort_keys=False)}---{body_of(q_raw)}"
    r = requests.put(f"{API}/workspaces/{TEAM_WS}/files/queue.md",
                     headers={**H, "If-Match": str(q_raw.get("version", 0))}, json={"content": new})
    print("[QUEUE]", r.status_code)

if outcome == "DISCARD":
    de_raw = requests.get(f"{API}/workspaces/{TEAM_WS}/files/dead_ends.md", headers=H).json()
    entry = (f"\n- exp_id: {EXP_ID}\n  axis: {axis}\n  direction: {direction}\n  value: {value}\n"
             f"  status: {'NOISE-CONTAMINATED — axis remains open' if inside_band else 'DISCARD'}\n"
             f"  delta: {delta:+.6f}\n  family: exp_gq\n  date: {datetime.now(timezone.utc).date()}\n"
             f"  reason: MATRIX_LR {value} vs 0.04 on the 956-step champion; "
             f"{'inside' if inside_band else 'outside'} the 2-sigma band. Confounded with changed "
             f"lr*wd decay. {'Not a refutation; axis open.' if inside_band else ''}\n")
    r = requests.put(f"{API}/workspaces/{TEAM_WS}/files/dead_ends.md",
                     headers={**H, "If-Match": str(de_raw.get("version", 0))},
                     json={"content": de_raw.get("content", "") + entry})
    print("[DEAD_END]", r.status_code)

if outcome == "KEEP":
    stamped = rep / f"train_{EXP_ID}.py"
    tmp = Path(f"{FOCUS_ROOT}/champion/train.py.tmp")
    shutil.copy(stamped, tmp); tmp.replace(f"{FOCUS_ROOT}/champion/train.py")
    with open(f"{FOCUS_ROOT}/champion/SOURCE", "a") as f:
        f.write(f"{EXP_ID} {our_metric:.6f} {AGENT_NAME} {NOW} (MATRIX_LR 0.04->{value})\n")
    champ_content = f"""---
metric_name: val_bpb
metric_value: {our_metric}
val_bpb: {our_metric}
seed_values: [{our_metric}]
direction: minimize
experiment_id: {EXP_ID}
agent: {AGENT_NAME}
timestamp: {NOW}
status: established
---
# Champion: {EXP_ID}

## Experiment Description
MATRIX_LR 0.04 -> {value} on exp_tput_batch_2e17. Single variable.

## Result
- val_bpb = {our_metric} (delta vs {exp_champ} = {delta:+.6f}, outside 2 sigma {band2:.6f})
- Steps {steps}, tokens {tokens_M}M, peak VRAM {peak_vram:.0f} MB

## Reproduction
`CUDA_VISIBLE_DEVICES=1 HF_HOME=/root/autodl-tmp/cache/huggingface HF_HUB_OFFLINE=1 python train.py`
Stamped: agents/{AGENT_NAME}/workspace/repo/train_{EXP_ID}.py
"""
    r = requests.put(f"{API}/workspaces/{MAIN}/files/champion.md",
                     headers={**H, "If-Match": str(champ_version)}, json={"content": champ_content})
    print("[CHAMPION PUT]", r.status_code)

roster = pf(requests.get(f"{API}/workspaces/{MAIN}/files/teams/roster.md", headers=H).json())
members = roster["teams"]["gradient-quality"]["members"]
r = requests.post(f"{API}/posts", headers=H, json={
    "workshop": WORKSHOP,
    "title": f"[RESULT] {EXP_ID}: {metric_name}={our_metric} ({outcome})",
    "content": (f"## Experiment\n{sentinel['description']}\n\n## Result\n{metric_name}: {our_metric}\n"
                f"Delta (ours - champion): {delta:+.6f}\n2-sigma band: +/-{band2:.6f}\nOutcome: {outcome}\n"
                f"Champion at measure: {cur} ({exp_champ})\n\n## Team\ngradient-quality\n\n"
                f"## Training Dynamics\n{dyn}\n\n{interp}\n"),
    "notify_agents": members,
    "tags": ["team:gradient-quality", "type:result", f"outcome:{outcome}"]})
post_id = (r.json().get("post", {}) or {}).get("id") if r.ok else None
print("[POST]", r.status_code, post_id)
sentinel.update({"status": "posted", "posted_to_workshop": bool(r.ok), "result_post_id": post_id,
                 "val_score": our_metric, "outcome": outcome, "delta": delta, "posted_at": NOW})
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
print("[SENTINEL] posted =", bool(r.ok))
