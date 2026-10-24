import json, requests, yaml, re
from datetime import datetime, timezone
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_analyst3"
creds=json.load(open(Path(FOCUS_ROOT)/"agents"/AGENT_NAME/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; TEAM="3a33313e-18ff-4e17-9c47-66b54cfe576d"
NOW=datetime.now(timezone.utc).isoformat()

def get(path):
    return requests.get(f"{API}/workspaces/{TEAM}/files/{path}",headers=HEADERS,timeout=20).json()
def put(path, version, content, label):
    r=requests.put(f"{API}/workspaces/{TEAM}/files/{path}",headers={**HEADERS,"If-Match":str(version)},
                   json={"content":content},timeout=30)
    print(label, r.status_code, r.json().get("version") if r.status_code==200 else r.text[:200])

# ---------------- strategy.md ----------------
s=get("strategy.md"); sc=s.get("content",""); sv=s.get("version")
sc2=sc.replace('age_rotations: 3','age_rotations: 4').replace(
  'last_audited: "2026-10-22T14:22:28.792046+00:00"', f'last_audited: "{NOW}"')
add = """

---

# Cycle 4 audit (analyst3, 2026-10-23) — H-capacity survives, but the search space is thin

## Hypothesis scorecard (Step 0.3)
Results since the cycle-3 audit, classified against the prediction "structural changes KEEP more than tuning":

| result | axis | delta | z | H-capacity verdict |
|---|---|---|---|---|
| exp_muon_beta2_hi | muon beta2 | +0.00057 | 0.19 | ORTHOGONAL (tuning) |
| exp_wd_0p0 | weight decay | +0.00084 | 0.28 | ORTHOGONAL (tuning) |
| exp_embedding_lr_hi | embedding LR | +0.00274 | 0.91 | ORTHOGONAL (tuning) |
| exp_adam_beta2_hi (2 seeds) | adam beta2 | +0.0024 mean | ~0.8 | ORTHOGONAL (tuning) |
| exp_gqa_kv1 | n_kv_head 4->1 | +0.00858 | 2.8 | ORTHOGONAL (FLOPs cut, not a capacity add) |

**No capacity-axis experiment ran this cycle.** age_rotations 3 -> **4**, supported_keeps **0**,
refuted_discards **2**. Not falsified (needs 3 refutations); but see the refutation trigger below.

## The frame that now governs this team: DATA-limited, not capacity-limited
Champion is 50.3M params trained on 94.2M tokens = **1.87 tokens/param** (Chinchilla optimum ~20).
Parameter split (vocab is 8192, NOT 32768 - this corrects every older FLOP estimate in the notes):
transformer matrices 25.2M (50%), **value embeddings 16.8M (33%)**, wte 4.19M, lm_head 4.19M.
Per-token FLOPs ~239M: MLP ~42%, attention ~26%, embeddings/unembedding the rest.
Consequences:
1. Adding params does not add data; at 1.87 tok/param, extra capacity has to repay in per-token
   quality immediately, and it has failed twice at zero step cost (ve_all -0.0060, depth_10 -0.0215).
2. Any change that buys FLOPs back for steps is worthless above the ~719-step knee (2e16 flat), and
   has failed twice anyway (gqa -0.0086, aspect_32 -0.0088).
3. What is left is **zero-param, zero-FLOP structural controls** whose effect must clear 2-sigma =
   0.00604 to be resolvable on one seed. There are only three such axes in this code: head granularity
   (HEAD_DIM), the MLP nonlinearity, and the value-embedding layer policy (already bracketed 0/4/8).

## Queue revision this cycle
- **exp_activation_silu AMENDED in place**: diff is now `F.relu(x).square()` -> `F.silu(x).square()`
  (squaring PRESERVED). The two reviews on ff2578ae (analyst1, analyst2) were right: the old diff
  changed the rectifier AND the square. Review flag discharged (their objection is resolved).
- **exp_head_dim_256 ADDED** (high): n_head 4 -> 2 at fixed n_embd 512; 0 params / 0 FLOPs / 0 steps.
  Together with the already-queued exp_head_dim_64 (n_head 8) this is a complete 3-point bracket with
  the champion (n_head 4) as the implicit midpoint.
- **exp_mlp_expansion_6** stays LOW as the Step 1e fallback, with the cost recomputed correctly:
  +50% MLP params = +21% FLOPs/token -> ~594 steps (-22%) -> ~0.022 val_bpb of step penalty.
  It needs a +0.022/step quality gain to break even; no zero-step capacity probe has managed 0.006.
- Pending order = expected information value: ve_none, head_dim_64, activation_silu, head_dim_256, mlp_6.

## Refutation trigger for NEXT cycle
The prediction names depth/width/**heads** explicitly. exp_head_dim_64 and exp_head_dim_256 now test the
heads arm directly at zero step cost. **If both DISCARD (2 seeds each), that is refutation #3 ->
post [HYPOTHESIS-FALSIFIED] with both results and let the monitor re-form the team.** A KEEP on either
is `supported_keeps: 1` and re-brackets head granularity instead.

## Step 1e compute-budget audit (unconditional) — budget IS binding, no new scale-up mandated
- peak_vram 22,653 / 32,768 MB = 69.1% allocated. The 70% default is nominally triggered, but the only
  direction that raises per-step compute is DEVICE_BATCH_SIZE 128, which is verified-OOM. Memory is
  therefore one discrete step from the wall, not headroom.
- Corrected compute efficiency: logged mfu 7.47% is against the H100 constant; x9.5 gives ~71% of the
  4080S dense-bf16 peak (analyst1 ~72%, analyst2 ~73%) -> well above the 50% threshold.
- Verdict: not compute-idle, not memory-idle. exp_mlp_expansion_6 remains the queued scale-up fallback.

## Step 1d team-structure audit (unconditional) — no structure post required
All teams falsified? No. Dormant >=5 cycles? No (capacity last ran 12:33, ~2 rotations). 3+ discussion
threads on an unowned axis? No discussion threads exist. Two teams on the same mechanism? No (throughput
owns readout/regularization, gradient-quality owns optimizer moments/LRs). Open [STUCK] / [DIMENSION-*]?
None (checked all 57 workshop posts). No [DIMENSION-*] post this cycle.

## Step 0.2 stagnation checks — no [DISCUSSION-TRIGGER] this cycle
rotations_since_keep ~1-2 (<3; last KEEP exp_batch_2e17 at 12:01Z, 7 results since). Axis-mining: the
last 7 DISCARDs span 7 distinct axes (>3), no paired probes pending but the diversity condition fails
too. No [HYPOTHESIS-FALSIFIED] since any reform. No active trigger exists.
"""
put("strategy.md", sv, sc2.rstrip()+add, "strategy.md")

# ---------------- knowledge/noise_floor.md ----------------
nf = """---
name: noise-floor
updated_at: "%s"
n_pairs: 2
sigma: 0.003019
band_2sigma: 0.00604
locked: false
source: main knowledge/noise_floor_data.md (analyst2, 2 independent same-code seed pairs)
---

# Noise Floor (MEASURED - supersedes the old 0.003 placeholder)

The old "conservative 0.003 band" was a 2-sigma stand-in implying sigma=0.0015. The first two real
same-code seed pairs measure **sigma = 0.003019**, so the 2-sigma decision band is **0.00604** - twice
what every cycle-1..3 proposal was valued against.

| pair | code | seed 42 | seed 43 | |delta| |
|---|---|---|---|---|---|
| exp_adam_beta2_hi | beta2 0.99 variant | 1.093839 | 1.098235 | 0.004396 |
| exp_warmdown_070 | warmdown 0.7 variant | 1.093748 | 1.097886 | 0.004138 |

Pooled: sigma_hat = sqrt((0.004138^2 + 0.004396^2)/4) = 0.003019 -> 2-sigma 0.00604, 3-sigma 0.00906.
Not locked (lock at n>=5 pairs; later pairs update sigma as a pooled average and do not reclassify
existing DISCARDs).

## Rules in force for capacity
1. A single-sample |delta| < 0.006 is INCONCLUSIVE. Do not close an axis on it; do not fine-bracket it
   (Step 1a far/opposite rule instead).
2. Zero-step-cost structural probes are expected to land near this band. Any proposal whose honest
   expected range straddles +-0.006 MUST be run with a second seed (43) before it is interpreted.
3. Promotion still requires the multi-seed gate: both seeds must beat the champion.
""" % NOW
put("knowledge/noise_floor.md", get("knowledge/noise_floor.md").get("version"), nf, "noise_floor.md")

# ---------------- dead_ends.md ----------------
de=get("dead_ends.md"); dec=de.get("content",""); dev=de.get("version")
dec2=re.sub(r'updated_at: ".*?"', f'updated_at: "{NOW}"', dec, count=1)
dec2=dec2.rstrip()+"""

## Cycle 4 noise-contamination re-triage (analyst3, measured sigma 0.003019)
Both entries re-checked against the MEASURED floor (not the old 0.003 placeholder):
- exp_depth_10: |delta| 0.021505 = **7.1 sigma** -> real, entry stands unchanged.
- exp_ve_all_layers: |delta| 0.006029 = **2.0 sigma** -> AT the boundary. Entry stays, but it is
  marked BOUNDARY: it is neither proof that capacity hurts nor a closable signal. exp_ve_none (0 of 8)
  is the arm that resolves it.

## Family counts (Step 2)
exp_depth: 1 DISCARD / 0 KEEP. exp_ve: 1 DISCARD / 0 KEEP. **No family has 3+ DISCARDs, so no new
dead-end family this cycle.** Two-DISCARD downgrade rule also not reached for any family.

## FLOP-reduction-buys-steps: 2 DISCARDs, 0 KEEPs -> LOW PRIORITY (not yet a dead end)
- exp_gqa_kv1 (n_kv_head 4->1, -31% params, +9% steps): +0.00858 (2.8 sigma).
- exp_aspect_ratio_32 (width 512->256, 2.4x steps): -0.00881 (2.9 sigma).
Both traded per-token quality for steps and lost; steps are worth ~0 above the ~719 knee. Any new
FLOP-cut justified by "+steps" is pre-falsified. A third such DISCARD closes the family.
"""
put("dead_ends.md", dev, dec2, "dead_ends.md")

# ---------------- knowledge/axis_priors.md ----------------
ap = """---
name: axis-priors
updated_at: "%s"
source: logs/experiments.jsonl (16 records: baseline + 15 experiments)
audited_by: ar_20261022hi_analyst3
---

# Empirical Axis Priors - cycle 4

Sign convention: mean_abs_delta is |val_bpb change|. Resolvability gate = 2-sigma = 0.00604.

| axis | direction | n | mean_|delta| | status |
|---|---|---|---|---|
| total_batch_size | decrease | 3 | 0.0340 | SATURATED: 2**19->18 +0.0256 KEEP, 2**18->17 +0.0760 KEEP, 2**17->16 +0.0003 FLAT |
| warmup_ratio | increase | 1 | 0.0278 | tested, DISCARD - closed for increase |
| depth | increase | 1 | 0.0215 | n=1, confounded with width 640 and -41%% steps |
| n_kv_head | decrease | 1 | 0.00858 | n=1 (2.8 sigma) - K/V sharing costs per-token quality |
| aspect_ratio | decrease | 1 | 0.00881 | n=1 (2.9 sigma) - width 256 capacity-limited |
| warmdown_ratio | decrease | 1 | 0.0068 | n=1, borderline (2.2 sigma) |
| value_embedding_layers | increase | 1 | 0.0060 | n=1 AT 2-sigma boundary - axis stays open; 0-arm queued |
| muon_momentum_ramp | decrease | 1 | 0.0041 | NOISE (1.34 sigma) - axis open, far probe queued (other team) |
| embedding_lr | increase | 1 | 0.00274 | n=1 in-band |
| adam_betas (beta2) | increase | 1 | 0.0024 | 2 seeds, tie (0.8 sigma) |
| warmdown_ratio | increase | 1 | 0.00178 | 2 seeds, tie (0.59 sigma) - axis closed around 0.5 |
| weight_decay | decrease | 1 | 0.00084 | n=1 in-band - axis OPEN |
| muon_beta2 | increase | 1 | 0.00057 | n=1 in-band - axis OPEN |
| device_batch_size | decrease | 1 | n/a | hardware prerequisite (128 OOMs), not a metric probe |
| activation_fn | replace | 0 | - | COLD - queued (amended to silu^2, keeps the square) |
| head_dim | decrease | 0 | - | COLD - queued (64 -> n_head 8) |
| head_dim | increase | 0 | - | COLD - queued (256 -> n_head 2) |
| value_embedding_layers | decrease | 0 | - | COLD - queued (0 of 8) |
| mlp_expansion | increase | 0 | - | COLD but step-costly (-22%% steps): low, Step 1e fallback only |
| window_pattern | replace | 0 | - | COLD; reviewed and SKIPPED (sub-band expected, ~0.003 step cost) |

## The step slope (unchanged, and it is what prices every proposal)
373 -> 719 steps: +0.0760. Fitted slope 0.1159 val_bpb per ln(step).
719 -> 1396 steps: +0.0003. **Knee at ~719.** Above it, steps are worth zero; below it, a -%d%% step
move costs ~0.1159*ln(1+x). This is why every FLOP-costly structural probe is priced, not just "tried".

## How to use this table
High mean|delta| axes are already TESTED (batch, depth, n_kv_head, aspect) or closed. Every remaining
axis is COLD, and every COLD axis is expected to straddle 2-sigma. Therefore: (a) prefer zero-step-cost
axes, (b) insist on 2 seeds for anything in-band, (c) do not fine-bracket a cold axis - use the
64/128/256-style bracket instead.
""" % (NOW, 22)
put("knowledge/axis_priors.md", get("knowledge/axis_priors.md").get("version"), ap, "axis_priors.md")
