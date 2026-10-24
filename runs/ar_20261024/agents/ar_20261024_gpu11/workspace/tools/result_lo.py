from api import *
import json, yaml
from datetime import datetime, timezone
from pathlib import Path

TEAM_WS = "005cb9ec-6fce-4bba-9340-21c08ab914c5"
EXP = "exp_gq_weight_decay_lo"
now = datetime.now(timezone.utc).isoformat()
CHAMPION = 1.088286
SIGMA_OLD, SIGMA_NEW = 0.002503, 0.002614
seed42, seed43 = 1.085846, 1.090242
mean2 = (seed42 + seed43) / 2
delta_mean = mean2 - CHAMPION
abs_pair = abs(seed42 - seed43)

md = f"""---
exp_id: {EXP}
agent: {AGENT_NAME}
team: gradient-quality
axis: weight_decay
direction: decrease
value: 0.1
current_value: 0.2
outcome: DISCARD
val_bpb_seed42: {seed42}
val_bpb_seed43: {seed43}
val_bpb_two_seed_mean: {mean2:.6f}
delta_vs_champion_two_seed_mean: {delta_mean:+.6f}
champion_at_measure_time: {CHAMPION}
sigma_at_measure_time: {SIGMA_OLD}
promoted: false
timestamp: {now}
---

# {EXP} — WEIGHT_DECAY 0.2 -> 0.1

## Experiment
Single token change at `train.py:444`: `WEIGHT_DECAY = 0.2` -> `0.1`. Everything else champion
(`exp_tput_batch_2e17`: AR64/w512/DEPTH8/MLP_EXPANSION=2/TOTAL_BATCH_SIZE 2**17/DBS64/compile
max-autotune-no-cudagraphs, MATRIX_LR 0.04, ADAM_BETAS (0.8,0.95)). Diff verified as exactly one
changed line (`diff -u` vs `champion/train.py`).

Scope: `WEIGHT_DECAY` reaches only the Muon 2D-matrix param groups (`train.py:261`); all five AdamW
groups pass `weight_decay=0.0` (lines 251-255). The decay in `muon_step_fused` is sign-masked and
first-order — `mask = (g*p) >= 0; p.sub_(lr*g + lr*wd*p*mask)` (lines 352-353) — at progress 0 it is
`0.04*0.2 = 0.8%/step`, falling linearly to 0.

## Result — two seeds, because seed 42 alone would have been a lucky-draw KEEP

| run | seed | GPU | val_bpb | delta vs champion | steps | tokens (M) |
|---|---|---|---|---|---|---|
| champion (`exp_tput_batch_2e17`) | 42 | 1 | {CHAMPION} | — | 956 | 125.3 |
| **{EXP}** | 42 | 1 | **{seed42}** | **-0.002440** | 955 | 125.2 |
| **{EXP}** (Step 7.0 second seed) | 43 | 1 | **{seed43}** | **+0.001956** | 952 | 124.8 |
| **two-seed mean** | — | 1 | **{mean2:.6f}** | **{delta_mean:+.6f}** | — | — |

**Outcome: DISCARD — the arm is FLAT.** The seed-42 draw (-0.002440, 0.98 sigma) sat just inside the
2-sigma band, so Step 7.0 fired and forced a second seed. That seed came back +0.001956 on the other
side of champion. The two-seed mean is {delta_mean:+.6f} = **0.09 sigma** — the arm has no measurable
effect at 2x spacing.

Same-GPU, same-code, seed-only spread = **{abs_pair:.6f}** — the largest such pair on record (previous
high 0.002462). Seed noise is 1.8x the effect seed 42 appeared to show. This is the second gq arm in a
row (after MATRIX_LR=0.02, pair 5 = 0.002462) to produce a cross-champion opposite-sign seed pair.

## Training Dynamics
| | seed 42 | seed 43 |
|---|---|---|
| num_steps | 955 | 952 |
| tokens_M | 125.2 | 124.8 |
| training_seconds | 300.2 | 300.1 |
| total_seconds (incl. compile+eval) | 379.9 | 379.7 |
| mean tok/s | 411,256 | ~410,000 |
| peak_VRAM_mB | 18479.4 | 18479.4 |
| loss @ 80% of run | 3.129242 | 3.138905 |
| final smoothed loss | 3.051484 | 3.058693 |
| final-20% loss drop | {0.077758:.6f} | {0.080212:.6f} |

- Throughput is unchanged vs champion (411.3K tok/s, 956 steps) — a weight-decay constant is free.
- Still **undertrained**: loss drops 0.078-0.080 in the final 20% (~1.3% of the full-run loss range).
- **New code-level signal, not noise:** both WD=0.1 seeds show a final-20% drop of 0.078-0.080, vs
  0.063 for the champion calibration run (`exp_cal_champion_seed43`). The two seeds agree with each
  other (spread 0.0025) far more tightly than they differ from the champion (0.015-0.017), so lower
  shrink really does let the model keep descending later in the run. It simply does not convert into
  val_bpb at this budget — the extra late descent is within the eval noise.

## Verdict and what it means for the axis
`weight_decay` lo arm (0.1) = **FLAT at 2x**. The bracket's lo point is now measured; the hi arm (0.4)
is still queued and is the only remaining point on this axis. Two live readings, both cheap to
distinguish:
- If hi (0.4) is also inside +/-0.0052, the axis closes at 2x scale as FLAT, like MATRIX_LR.
- If hi is clearly worse (> +0.0052), the pair of arms implies a minimum near 0.2 within +/-0.005 —
  still no promoted change, but a real curvature statement.

This also weakly de-confounds the closed MATRIX_LR bracket: MATRIX_LR 0.04->0.02 halved `lr` and
`lr*wd` together and was flat; the decay half of that change is now independently flat at 2x, so the
flat MATRIX_LR result is not hiding an opposed decay effect.

## Reproduction
```
cp champion/train.py .
sed -i 's/^WEIGHT_DECAY = 0.2/WEIGHT_DECAY = 0.1/' train.py
CUDA_VISIBLE_DEVICES=1 HF_HOME=/root/autodl-tmp/cache/huggingface HF_HUB_OFFLINE=1 python train.py
```
Expected: val_bpb in [{seed43}, {seed42}] (mean {mean2:.6f}).
"""
r = requests.put(f"{API}/workspaces/{MAIN_WS_ID}/files/results/{EXP}.md",
                 headers=HEADERS, json={"content": md})
print("result file PUT:", r.status_code)

# ---------- release claim + move pending -> completed ----------
q_raw = get_file(TEAM_WS, "queue.md")
q_fm = parse_frontmatter(q_raw)
removed = q_fm.get("claims", {}).pop(AGENT_NAME, None) is not None
pending = q_fm.get("pending") or []
completed = q_fm.get("completed") or []
remaining = []
for it in pending:
    if it.get("id") == EXP:
        it = dict(it)
        it["completed_at"] = now; it["completed_by"] = AGENT_NAME
        it["outcome"] = "DISCARD"; it["val_score"] = round(mean2, 6)
        it["seed_values"] = [seed42, seed43]
        it["result_note"] = "2-seed FLAT (delta_mean -0.000242, 0.09 sigma)"
        completed.append(it)
    else:
        remaining.append(it)
q_fm["pending"] = remaining; q_fm["completed"] = completed
qb = q_raw.get("content", "").split("---", 2)[-1]
qn = f"---\n{yaml.safe_dump(q_fm, sort_keys=False)}---{qb}"
assert yaml.safe_load(qn.split("---")[1]) == q_fm
r = requests.put(f"{API}/workspaces/{TEAM_WS}/files/queue.md",
                 headers={**HEADERS, "If-Match": str(q_raw.get("version", 0))},
                 json={"content": qn})
print("queue release+complete:", r.status_code, "| claim removed:", removed)

# ---------- dead ends entry ----------
de_raw = get_file(TEAM_WS, "dead_ends.md")
entry = (f"\n- exp_id: {EXP}\n"
         f"  axis: weight_decay\n  direction: decrease\n  value: 0.1\n"
         f"  delta: {delta_mean:+.6f} (two-seed mean; seeds {seed42}/{seed43})\n"
         f"  family: exp_gq\n  date: 2026-10-24\n"
         f"  status: FLAT at 2x, lo arm only — hi arm (0.4) still queued; do NOT re-run WEIGHT_DECAY=0.1\n"
         f"  reason: Single-token WD 0.2->0.1. Seed 42 gave -0.00244 (0.98 sigma, looked like a KEEP), "
         f"seed 43 gave +0.001956. Same-GPU seed-only spread 0.0044, the largest on record. "
         f"Throughput unchanged; final-20% loss drop rises to 0.078-0.080 vs 0.063 champion but does not reach val_bpb.\n")
r = requests.put(f"{API}/workspaces/{TEAM_WS}/files/dead_ends.md",
                 headers={**HEADERS, "If-Match": str(de_raw.get("version", 0))},
                 json={"content": de_raw.get("content", "# Dead Ends\n\n") + entry})
print("dead_ends PUT:", r.status_code)

# ---------- POST [RESULT] ----------
r = requests.post(f"{API}/posts", headers=HEADERS, json={
    "workshop": WORKSHOP,
    "title": f"[RESULT] {EXP}: val_bpb={mean2:.6f} 2-seed mean (DISCARD — seed 42's -0.00244 was a lucky draw; seed 43 returned +0.001956; FLAT)",
    "content": f"""## Experiment
WEIGHT_DECAY 0.2 -> **0.1**, single token at `train.py:444`, MATRIX_LR pinned at 0.04. Muon 2D matrices only
(AdamW groups all pass `weight_decay=0.0`); decay is sign-masked and first-order (0.8%/step -> 0.4%/step at progress 0).

## Result — TWO SEEDS

| run | seed | GPU | val_bpb | delta vs champion |
|---|---|---|---|---|
| champion `exp_tput_batch_2e17` | 42 | 1 | 1.088286 | — |
| **{EXP}** | 42 | 1 | **{seed42}** | **-0.002440** (0.98 sigma) |
| **{EXP}** second seed | 43 | 1 | **{seed43}** | **+0.001956** |
| two-seed mean | — | 1 | {mean2:.6f} | **{delta_mean:+.6f}** |

Outcome: **DISCARD — FLAT.** Step 7.0 correctly forced the second seed: seed 42 alone would have been
promoted as a KEEP at 0.98 sigma, and it was simply a lucky draw. Seed-only spread on this code is
**{abs_pair:.6f}**, the largest same-GPU pair on record (previous high 0.002462 from MATRIX_LR=0.02 —
which this repeats almost exactly). **This is the second gq arm in a row where one seed beat champion
and the other lost to it.**

**sigma updated:** the pooled ledger is now n=6 pairs, sigma **0.002614** (2-sigma 0.005228), up from
0.002503. Appended as pair 6 to `knowledge/noise_floor_data.md`. Practical consequence: the effective
promotion bar for single-seed results is drifting *up* to ~0.006, and two of the last three gq
candidate KEEPs died at exactly this bar.

## Training Dynamics (throughput neutral, as expected)
955 / 952 steps, 125.2 / 124.8M tokens, 411K tok/s, 18479 MB peak VRAM — identical to champion.
Still undertrained: final-20% loss drop **{0.077758:.6f} / {0.080212:.6f}** vs **0.063** for the
champion calibration. The two seeds agree with each other (spread 0.0025) far better than they
differ from champion (0.015+), so lower shrink genuinely lets the model descend later in the run —
it just does not reach val_bpb inside a 300 s budget.

## What is left on this axis
Only the hi arm (WEIGHT_DECAY 0.4) remains. If it too lands inside +/-0.0052, close `weight_decay`
at 2x as FLAT like MATRIX_LR. If it is clearly worse, the two arms bracket a minimum near 0.2 with
no promotable change. Either way the axis costs at most one more slot.

Side benefit: MATRIX_LR 0.04->0.02 halved `lr` *and* `lr*wd` together and came back flat. The decay
half of that is now independently flat, so the closed MATRIX_LR bracket is not hiding an opposed
decay effect.

## Team
gradient-quality. Result file: `results/{EXP}.md`. Champion unchanged (no champion.md PUT, no
champion/SOURCE write).""",
    "tags": ["team:gradient-quality", "type:result", "outcome:DISCARD", "axis:weight_decay"],
})
print("RESULT post:", r.status_code, r.json().get("id") if r.ok else r.text[:300])

# ---------- sentinel ----------
WS = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace")
rl = WS / "result_latest.json"
prior = json.loads(rl.read_text())
prior.update({"status": "posted", "posted_to_workshop": True, "val_score": round(mean2, 6),
              "seed_values": [seed42, seed43], "outcome": "DISCARD",
              "result_post_id": r.json().get("id") if r.ok else None,
              "posted_at": now, "delta_vs_champion": round(delta_mean, 6)})
rl.write_text(json.dumps(prior, indent=2, default=str))
print("sentinel marked posted")
