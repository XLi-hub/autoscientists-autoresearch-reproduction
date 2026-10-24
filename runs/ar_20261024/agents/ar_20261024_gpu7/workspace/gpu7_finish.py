import json, os, re, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
import requests, yaml

DRY = os.environ.get("DRY_RUN", "1") == "1"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu7"
EXP_ID = "exp_gq_matrix_lr_hi"
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


def pf(resp):
    parts = resp.get("content", "").split("---")
    return yaml.safe_load(parts[1]) if len(parts) >= 3 else {}


def body_of(resp):
    return resp.get("content", "").split("---", 2)[-1]


sentinel = json.loads((ws / "result_latest.json").read_text())
log = Path(sentinel["stdout_path"]).read_text(errors="ignore")

m = re.search(r"val_bpb:\s+([0-9.]+)", log)
if not m:
    print("HARD FAIL: no val_bpb in stdout"); sys.exit(1)
our_metric = float(m.group(1))


def grab(name, cast=float):
    mm = re.search(rf"{name}:\s+([0-9.]+)", log)
    return cast(mm.group(1)) if mm else None


steps = grab("num_steps", int)
tokens_M = grab("total_tokens_M")
train_s = grab("training_seconds")
total_s = grab("total_seconds")
peak_vram = grab("peak_vram_mb")
mfu = grab("mfu_percent")
params_M = grab("num_params_M")

# ---- training dynamics from step lines ----
pts = [(int(a), float(b)) for a, b in re.findall(
    r"step (\d+) \(\s*[\d.]+%\) \| loss: ([0-9.]+)", log)]
loss_curve = None
if len(pts) > 10:
    losses = [p[1] for p in pts]
    rng = max(losses) - min(losses)
    final_step, final_loss = pts[-1]
    tgt = int(0.8 * final_step)
    near = min(pts, key=lambda p: abs(p[0] - tgt))
    drop20 = near[1] - final_loss
    pct = 100 * drop20 / rng if rng else 0.0
    loss_curve = dict(n_points=len(pts), final_step=final_step, final_loss=final_loss,
                      loss_at_80pct=near[1], step_at_80pct=near[0], range=rng,
                      final20_drop=drop20, final20_pct_of_range=pct)
    print("[DYNAMICS]", json.dumps(loss_curve, indent=2))

# ---- champion (HARD FAIL if metric missing) ----
champ_raw = requests.get(f"{API}/workspaces/{MAIN}/files/champion.md", headers=H).json()
champ = pf(champ_raw)
metric_name = champ.get("metric_name")
dirn = champ.get("direction", "minimize")
cur = champ.get(metric_name) if metric_name else None
if cur is None:
    cur = champ.get("metric_value")
if cur is None:
    print("HARD FAIL: champion metric unparseable; refusing to default to inf"); sys.exit(1)
cur = float(cur)
champ_version = champ_raw.get("version", 0)
exp_champ = champ.get("experiment_id")

delta = our_metric - cur           # negative == better (minimize)
improvement = cur - our_metric     # positive == better
print(f"[CMP] ours={our_metric} champ={cur} ({exp_champ}) delta(ours-champ)={delta:+.6f}")

# ---- noise gate ----
nf = requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/noise_floor_data.md", headers=H)
sigma = 0.002865
if nf.status_code == 200:
    fm = pf(nf.json())
    sigma = float(fm.get("sigma_estimate", sigma) or sigma)
band2 = 2 * sigma
print(f"[NOISE] sigma={sigma} 2sigma={band2:.6f}")

if dirn == "minimize":
    better = our_metric < cur
else:
    better = our_metric > cur
inside_band = abs(delta) <= band2

if better and not inside_band:
    outcome = "KEEP"
elif better and inside_band:
    outcome = "KEEP-UNCONFIRMED"   # needs second seed; do not promote
else:
    outcome = "DISCARD"

print(f"[PLAN] outcome={outcome} inside_band={inside_band}")

# ---- result markdown ----
dyn = ""
if loss_curve:
    dyn = (f"- Steps: {loss_curve['final_step']}, tokens: {tokens_M}M, peak VRAM: {peak_vram:.0f} MB, MFU: {mfu:.2f}%\n"
           f"- Final-20% loss drop: {loss_curve['final20_drop']:.6f} = "
           f"{loss_curve['final20_pct_of_range']:.2f}% of the run's loss range "
           f"(>1% => still undertrained).\n"
           f"- Loss at ~80% ({loss_curve['step_at_80pct']}): {loss_curve['loss_at_80pct']:.6f} -> final {loss_curve['final_loss']:.6f}")

result_md = f"""---
exp_id: {EXP_ID}
axis: matrix_lr
direction: increase
value: 0.08
current_value: 0.04
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

MATRIX_LR 0.04 -> 0.08 in `champion/train.py` (single variable). This is the Muon LR for all
eight blocks' matrix weights: 16.78M/41.94M params (40.0%), and 80.0% of the 6N FLOP-relevant
count. First-ever probe of this axis (n=0). Champion base `exp_tput_batch_2e17` (val_bpb
1.088286; ASPECT_RATIO 64 / width 512, DEPTH 8, MLP_EXPANSION 2, TOTAL_BATCH_SIZE 2**17,
DEVICE_BATCH_SIZE 64, compile max-autotune-no-cudagraphs). Proposed by ar_20261024_analyst1
(post 552e2db3), claimed by ar_20261024_gpu7 on GPU 1.

**Pre-registered confound.** `muon_step_fused` applies decay as `lr * wd * p`, so doubling
MATRIX_LR also doubles effective per-step decay from 0.8% to 1.6% at progress 0. This arm is
therefore LR+WD, not LR alone. De-confounder (only if this DISCARDs by >0.01):
MATRIX_LR=0.08 with WEIGHT_DECAY=0.1.

## Result

- val_bpb = **{our_metric}**
- Champion at measure: {cur} ({exp_champ}, champion.md v{champ_version})
- delta (ours - champion) = **{delta:+.6f}**; 2-sigma band = +/-{band2:.6f} (sigma {sigma})
- Outcome: **{outcome}**{' — INSIDE the 2-sigma band, so this is NOT a refutation of the axis and NOT a near-miss; matrix_lr remains open. The lo arm (0.02) is the untested other half of the bracket.' if inside_band else ''}

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

print("=" * 80)
print(result_md)

if DRY:
    print("[DRY RUN] no writes performed")
    sys.exit(0)

# ---- write result file ----
r = requests.put(f"{API}/workspaces/{MAIN}/files/results/{EXP_ID}.md", headers=H,
                 json={"content": result_md})
print("[RESULT FILE]", r.status_code)

# ---- queue: release claim + move pending -> completed ----
q_raw = requests.get(f"{API}/workspaces/{TEAM_WS}/files/queue.md", headers=H).json()
q_fm = pf(q_raw)
claim_removed = q_fm.get("claims", {}).pop(AGENT_NAME, None) is not None
pending = q_fm.get("pending", []) or []
completed = q_fm.get("completed", []) or []
remaining = []
for it in pending:
    if it.get("id") == EXP_ID:
        it = dict(it); it["completed_at"] = NOW; it["completed_by"] = AGENT_NAME
        it["outcome"] = outcome; it["val_score"] = our_metric; it["delta"] = delta
        completed.append(it)
    else:
        remaining.append(it)
q_fm["pending"] = remaining; q_fm["completed"] = completed
if claim_removed or len(remaining) != len(pending):
    new = f"---\n{yaml.safe_dump(q_fm, sort_keys=False)}---{body_of(q_raw)}"
    r = requests.put(f"{API}/workspaces/{TEAM_WS}/files/queue.md",
                     headers={**H, "If-Match": str(q_raw.get("version", 0))},
                     json={"content": new})
    print("[QUEUE]", r.status_code)

# ---- DISCARD -> dead_ends ----
if outcome in ("DISCARD",):
    de_raw = requests.get(f"{API}/workspaces/{TEAM_WS}/files/dead_ends.md", headers=H).json()
    entry = (f"\n- exp_id: {EXP_ID}\n  axis: matrix_lr\n  direction: increase\n  value: 0.08\n"
             f"  status: {'NOISE-CONTAMINATED — axis remains open' if inside_band else 'DISCARD'}\n"
             f"  delta: {delta:+.6f}\n  family: exp_gq\n  date: {datetime.now(timezone.utc).date()}\n"
             f"  reason: MATRIX_LR 0.08 vs 0.04 on the 956-step champion; "
             f"{'inside' if inside_band else 'outside'} the 2-sigma band. "
             f"Confounded with doubled lr*wd decay (0.8%->1.6%/step). "
             f"{'Not a refutation; lo arm (0.02) still the untested half of the bracket.' if inside_band else ''}\n")
    r = requests.put(f"{API}/workspaces/{TEAM_WS}/files/dead_ends.md",
                     headers={**H, "If-Match": str(de_raw.get("version", 0))},
                     json={"content": de_raw.get("content", "") + entry})
    print("[DEAD_END]", r.status_code)

# ---- KEEP -> champion (only if confirmed outside the noise band) ----
if outcome == "KEEP":
    stamped = rep / f"train_{EXP_ID}.py"
    tmp = Path(f"{FOCUS_ROOT}/champion/train.py.tmp")
    shutil.copy(stamped, tmp); tmp.replace(f"{FOCUS_ROOT}/champion/train.py")
    with open(f"{FOCUS_ROOT}/champion/SOURCE", "a") as f:
        f.write(f"{EXP_ID} {our_metric:.6f} {AGENT_NAME} {NOW} (MATRIX_LR 0.04->0.08, Muon LR on 80% of FLOP-relevant params)\n")
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
superseded_note: >
  Supersedes {exp_champ} ({cur}) by {improvement:+.6f} (outside the 2-sigma {band2:.6f} band).
  MATRIX_LR 0.04 -> 0.08 (Muon LR, 40% of params / 80% of 6N FLOP count). Confound on record:
  this also doubles the coupled lr*wd decay; a future arm can de-confound with WEIGHT_DECAY=0.1.
hardware_adaptation: DEVICE_BATCH_SIZE 64 (32GB), TOTAL_BATCH_SIZE 2**17, MLP_EXPANSION 2, ASPECT_RATIO 64, HEAD_DIM 128, compile max-autotune-no-cudagraphs
---

# Champion: {EXP_ID}

## Experiment Description

MATRIX_LR 0.04 -> 0.08 on exp_tput_batch_2e17. Single variable. Muon LR for all 8 blocks'
matrix weights (16.78M/41.94M params). Pre-registered confound: lr*wd coupling doubles
effective decay 0.8%->1.6%/step at progress 0.

## Result

- val_bpb = {our_metric} (single seed; delta vs {exp_champ} = {delta:+.6f}, outside 2 sigma {band2:.6f})
- Steps {steps}, tokens {tokens_M}M, peak VRAM {peak_vram:.0f} MB

## Complete Hyperparameters

```json
{json.dumps({"ASPECT_RATIO": 64, "HEAD_DIM": 128, "WINDOW_PATTERN": "SSSL", "MLP_EXPANSION": 2,
             "TOTAL_BATCH_SIZE": "2**17", "DEVICE_BATCH_SIZE": 64, "grad_accum": 1,
             "EMBEDDING_LR": 0.6, "UNEMBEDDING_LR": 0.004, "MATRIX_LR": 0.08, "SCALAR_LR": 0.5,
             "WEIGHT_DECAY": 0.2, "ADAM_BETAS": [0.8, 0.95], "WARMUP_RATIO": 0.0,
             "WARMDOWN_RATIO": 0.5, "FINAL_LR_FRAC": 0.0, "DEPTH": 8, "MAX_SEQ_LEN": 2048,
             "TIME_BUDGET": 300, "compile_mode": "max-autotune-no-cudagraphs",
             "num_steps": steps, "tokens_M": tokens_M, "params_M": params_M}, indent=2)}
```

## Reproduction

1. Copy `{FOCUS_ROOT}/champion/train.py`
2. `CUDA_VISIBLE_DEVICES=1 HF_HOME=/root/autodl-tmp/cache/huggingface HF_HUB_OFFLINE=1 python train.py`
3. Expected val_bpb ~ {our_metric}

## Provenance

- Agent: {AGENT_NAME}, team gradient-quality, timestamp {NOW}
- Stamped: agents/{AGENT_NAME}/workspace/repo/train_{EXP_ID}.py
- Proposal: 552e2db3-5221-498b-a61e-83f155016948
"""
    r = requests.put(f"{API}/workspaces/{MAIN}/files/champion.md",
                     headers={**H, "If-Match": str(champ_version)},
                     json={"content": champ_content})
    print("[CHAMPION PUT]", r.status_code)

# ---- post [RESULT] ----
roster = pf(requests.get(f"{API}/workspaces/{MAIN}/files/teams/roster.md", headers=H).json())
members = roster["teams"]["gradient-quality"]["members"]
title = f"[RESULT] {EXP_ID}: {metric_name}={our_metric} ({outcome})"
content = (f"## Experiment\n{sentinel['description']}\n\n## Result\n{metric_name}: {our_metric}\n"
           f"Delta (ours - champion): {delta:+.6f}\n2-sigma band: +/-{band2:.6f}\nOutcome: {outcome}\n"
           f"Champion at measure: {cur} ({exp_champ})\n\n## Team\ngradient-quality\n\n"
           f"## Training Dynamics\n{dyn}\n")
r = requests.post(f"{API}/posts", headers=H, json={
    "workshop": WORKSHOP, "title": title, "content": content,
    "notify_agents": members,
    "tags": ["team:gradient-quality", "type:result", f"outcome:{outcome}"]})
post_id = r.json().get("id") if r.ok else None
print("[POST]", r.status_code, post_id)

# ---- mark posted ----
sentinel.update({"status": "posted", "posted_to_workshop": True, "result_post_id": post_id,
                 "val_score": our_metric, "outcome": outcome, "delta": delta,
                 "posted_at": NOW})
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
print("[SENTINEL] marked posted")
