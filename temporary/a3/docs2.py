import json, requests
from datetime import datetime, timezone
FR="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FR}/agents/ar_20261022hi_analyst3/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds["agent_name"]}
API="http://localhost:3000/api/v1"; TEAM="3a33313e-18ff-4e17-9c47-66b54cfe576d"
NOW=datetime.now(timezone.utc).isoformat()
def put(path,content):
    r=requests.get(f"{API}/workspaces/{TEAM}/files/{path}",headers=H).json()
    rr=requests.put(f"{API}/workspaces/{TEAM}/files/{path}",headers={**H,"If-Match":str(r.get("version",0))},json={"content":content})
    print(path,"->",rr.status_code)

strategy = f"""---
hypothesis: H-capacity
prediction: Structural changes (depth/width/heads) will KEEP more than tuning
falsification: 3 rotations of prediction-consistent experiments all DISCARD
age_rotations: 3
supported_keeps: 0
refuted_discards: 2
last_audited: "{NOW}"
regime: step-saturated
---

# Team capacity

**Hypothesis (H-capacity):** The model's parametric capacity or representational structure limits the metric

**Prediction:** Structural changes (depth/width/heads) will KEEP more than tuning

**Falsification:** 3 rotations of prediction-consistent experiments all DISCARD

Proposals this team queues must be evaluable against the prediction.
Any axis is in-scope as long as the change is one the hypothesis predicts will KEEP.

## REGIME CHANGE (cycle 3, analyst3) — read before proposing anything

exp_batch_2e16 (2**17 -> 2**16, 1396 steps, 91.5M tokens) returned **val_bpb 1.094356, delta +0.00032 — FLAT**.
The step ladder therefore saturates at ~719 optimizer steps:
- 373 -> 719 steps: +0.0760 (KEEP)
- 719 -> 1396 steps: +0.0003 (FLAT)

**Consequences for every future capacity proposal:**
1. Any probe that buys steps by removing capacity is now worthless. A step target below ~700 is the only
   place steps still pay, and losing capacity to get there is a straight loss.
2. Any probe that COSTS steps is now nearly free in step terms (719 -> 705 is still above the knee) but buys
   no step benefit — value it purely on per-step quality.
3. Therefore **only step-neutral, per-step-quality probes can KEEP**. In practice: hold n_embd, n_layer,
   TOTAL_BATCH_SIZE and DEVICE_BATCH_SIZE fixed; vary one representational choice.

## Cycle 1 audit (analyst3)
- No capacity experiments ran in cycle 1; champion moved only via the throughput team.
- Baseline audit: depth is a SCALE axis (DEPTH 6/8/10 -> n_embd 384/512/640); dmodel_lr_scale
  = (n_embd/768)**-0.5 applies to AdamW only, so width probes confound capacity with the AdamW/Muon LR ratio.

## Cycle 2 audit (analyst3)
- Classification for H-capacity: none applied (all three new results were throughput/optimizer axes);
  age_rotations incremented, no refutations recorded.
- Proposed the MLP-expansion bracket, HEAD_DIM 64, and carried depth_6 / ve_all_layers.

## Cycle 3 audit (analyst3, this cycle) — hypothesis scorecard
Results since the last audit, classified against the prediction:
| result | axis | delta | H-capacity verdict |
|---|---|---|---|
| exp_depth_10 | depth 8->10 (+71% params) | -0.021505 | **REFUTES** (predicted KEEP) |
| exp_ve_all_layers | value embeds 4->8 (+33% params) | -0.006029 | **REFUTES** (predicted KEEP) |
| exp_aspect_ratio_32 | width 512->256 | -0.008807 | **ORTHOGONAL** (width decrease; not the predicted direction) |
| exp_batch_2e16 | total batch 2**17->2**16 | +0.000319 | orthogonal (throughput axis) |

=> age_rotations 3, supported_keeps 0, refuted_discards 2. **One more refuting structural result falsifies
H-capacity.** Proposers must state in the proposal which outcome would refute the hypothesis; "it might help"
is not enough at 0/3.

Why the two refutations are consistent rather than contradictory: both added capacity in a step-starved or
step-neutral setting and both failed, while exp_aspect_ratio_32 shows the opposite extreme (4x less capacity
at 2.4x steps) also fails. Capacity is at a **local optimum near n_embd=512 / depth 8**; it is neither the
binding constraint nor a free lever.

## Step 1b followup harvest
No `## Followup` / `## Follow-up` section exists in any result file from cycle 1-2
(checked exp_batch_2e17, exp_batch_2e18, exp_depth_10, exp_ve_all_layers, exp_aspect_ratio_32,
exp_muon_mom_ramp60). Nothing to harvest. The actionable recommendation this cycle came instead from
exp_aspect_ratio_32's `## Interpretation` ("more steps at 512 width") — and exp_batch_2e16 then showed
that route is saturated, so it is retired.

## Queue revision this cycle (analyst3)
- **Retired (SUPERSEDED):** exp_depth_6 and exp_mlp_expansion_3 — both existed only to buy steps.
- **Deprioritised:** exp_mlp_expansion_6 (low) — costs ~19% steps, now below the knee; retained only as the
  Step 1e scale-up fallback. Note that every zero-step-cost scale-up has lost (ve_all -0.0060, depth_10 -0.0215).
- **Promoted:** exp_head_dim_64 (high) — zero params, zero FLOPs, zero step change.
- **Added:** exp_activation_silu (high), exp_ve_none (high) — both step-neutral per-step-quality probes.
- **Withdrawn before queueing:** exp_depth_6_w512 — its +28%-steps premise died with exp_batch_2e16.

## Step 1e compute audit
Champion peak VRAM 22653 MB / 32760 MB = 69.1%, real MFU ~71% after correcting the H100 peak constant
(~9.5x understated). The memory threshold is only marginally under 70%, and the actionable headroom is zero:
DEVICE_BATCH_SIZE 128 OOMs on the 32.7 GB cards, and depth_10 at batch 64 (~35 GB) would also OOM.
Scale-up is therefore **not** the largest untouched axis here, and this is now confirmed empirically, not just
asserted: the two scale-up probes run this rotation (depth_10, ve_all_layers) both DISCARDed. The Step 1e
obligation is discharged by keeping exp_mlp_expansion_6 in the queue as the scale-up arm.

## Step 1d team-structure audit
No condition holds: no team is fully falsified (capacity is 0/3, not falsified); no team dormant >=5 cycles
(teams formed this run); no 3+ [DISCUSSION] threads converging on an unowned axis (there are zero
[DISCUSSION] posts); no two teams proposing the same mechanism (throughput = steps/batch, gradient-quality =
LR/betas, capacity = structure); no open [STUCK] thread. No [DIMENSION-*] post required this cycle.
"""

bcoverage = f"""---
name: baseline-coverage
updated_at: "{NOW}"
audited_by: ar_20261022hi_analyst3
champion_version: exp_batch_2e17 (val_bpb 1.094037, DEPTH=8, n_embd=512, ASPECT_RATIO=64, TOTAL_BATCH_SIZE=2**17, DEVICE_BATCH_SIZE=64, 719 steps, 50.3M params)
---

# Baseline Coverage Audit — champion/train.py (cycle 3)

Champion = exp_batch_2e17. "tested?" = Yes only where a result file explicitly varied that constant.
DERIVED = computed from other constants, not independently settable.

| parameter | current_value | tested? | result summary |
|---|---|---|---|
| DEPTH | 8 | **Yes** | 8->10 (with width 512->640, batch 32): DISCARD -0.0215, 221 steps. Confounded; depth-only never tested. |
| ASPECT_RATIO | 64 | **Yes** | 64->32 (n_embd 512->256): DISCARD -0.0088 at 1741 steps. Width reduction not repaid by steps. |
| HEAD_DIM | 128 | No | exp_head_dim_64 queued (high; 128->64 => n_head 8 at same n_embd, zero params/FLOPs). |
| n_layer / n_head / n_embd / n_kv_head | DERIVED (8 / 4 / 512 / 4) | **Yes** (n_kv_head) | exp_gqa_kv1 queued in throughput (n_kv_head 4->1, -7.9% FLOPs). n_kv_head == n_head today (full MHA). |
| WINDOW_PATTERN | "SSSL" | No | Last layer forced long. Attention is ~5-8% of FLOPs/token, so pattern changes are near the 0.003 band. |
| TOTAL_BATCH_SIZE | 2**17 = 131072 | **Yes** | 2**19->2**18 KEEP +0.0256; 2**18->2**17 KEEP +0.0760; 2**17->2**16 **FLAT +0.00032 (1396 steps)**. SATURATED. |
| DEVICE_BATCH_SIZE | 64 | **Yes** | 128 OOMs on 32.7 GB; 32 is the 2**16 pairing. |
| grad_accum | DERIVED = 1 | **Yes** | follows TOTAL_BATCH_SIZE / (DEVICE_BATCH_SIZE*MAX_SEQ_LEN). |
| EMBEDDING_LR | 0.6 | No | AdamW for wte + value_embeds (42% of params, one shared LR). x1.2247 via dmodel_lr_scale. Owner: gradient-quality bracket. |
| UNEMBEDDING_LR | 0.004 | No | AdamW lm_head only (4.19M), wd=0. |
| MATRIX_LR | 0.04 | No | Muon; NOT scaled by dmodel_lr_scale. Bracket queued (gradient-quality). |
| SCALAR_LR | 0.5 | No | resid group gets 0.005 (lr*0.01), x0 group 0.5, betas (0.96,0.95). |
| WEIGHT_DECAY | 0.2 | No | **Muon groups only** (AdamW groups hardcoded 0.0). Scheduled WD*(1-progress) => average 0.10. |
| ADAM_BETAS | (0.8, 0.95) | No | all AdamW groups; x0 overrides (0.96,0.95). Bracket queued (gradient-quality). |
| WARMUP_RATIO | 0.0 | **Yes** | 0.1 -> DISCARD 1.223462 (+0.0278). |
| WARMDOWN_RATIO | 0.5 | **Yes** | 0.25 -> DISCARD 1.176817. 0.7 still queued (throughput). |
| FINAL_LR_FRAC | 0.0 | No | cooldown ends at exactly 0 LR. Skipped: warmdown_025 evidence says the decay tail is load-bearing. |
| dmodel_lr_scale | (n_embd/768)**-0.5 (DERIVED) | No | 1.2247 at 512. AdamW only (Muon unscaled) — confounds every width probe. |
| Muon momentum | 0.95 after ramp | No | ramp 0.85->0.95 over min(step/300,1). |
| Muon momentum ramp length | 300 steps (inline) | **Yes** | 60 -> DISCARD 1.174107 (+0.0041, 1.35x band). Near-miss; axis open. |
| Muon ns_steps | 5 | No | polar-express iterations; ~0.3% of per-step work (recomputed from matrix shapes). |
| Muon beta2 (NorMuon) | 0.95 | No | second-momentum buffer. Bracket queued (gradient-quality). |
| **MLP activation** | **ReLU-squared** (`F.relu(x).square()`) | No | **NEW ROW — was missing from cycles 1-2 because it is a symbolic literal, not a number.** exp_activation_silu queued (high). |
| MLP hidden multiplier | 4 (inline `4 * config.n_embd`) | No | exp_mlp_expansion_6 retained low (scale-up fallback); mlp_3 SUPERSEDED. |
| value-embedding layer policy | alternating has_ve (4 of 8) | **Yes** | all 8 -> DISCARD -0.0060 at 0 step cost. exp_ve_none queued (far/opposite arm, 0 of 8). |
| ve_gate_channels | 32 (inline) | No | gate reads first 32 of 512 channels. |
| resid_lambdas init | 1.0 | No | per-layer residual scale, learned (8 params). |
| x0_lambdas init | 0.1 (inline fill_) | No | per-layer x0 scale, learned (8 params). |
| wte init std | 1.0 | No | normal init. |
| lm_head init std | 0.001 | No | normal init. |
| block init scale s | 3**0.5 * n_embd**-0.5 (DERIVED) | No | uniform(-s,s) for q/k/v/fc; c_proj zero-init. |
| rotary base | 10000 (inline) | No | _precompute_rotary_embeddings default arg. |
| rotary_seq_len | sequence_len * 10 (DERIVED) | No | 20480 positions precomputed. |
| logit softcap | 15 (inline, forward) | No | softcap*tanh(logits/softcap). |
| time-budget warmup | `if step > 10 and ...` | No | ~10 steps of free compute outside the budget accounting. |
| weight decay schedule | WD*(1-progress), LR-multiplied | No | Decay is scaled by LR, so it vanishes in the warmdown tail. |

**Untested high-leverage remainder:** activation (queued), HEAD_DIM (queued), ve_gate_channels, resid/x0 inits,
rotary base, softcap. Of these only activation and HEAD_DIM are step-neutral, which is now a hard requirement.
"""

priors = f"""---
name: axis-priors
updated_at: "{NOW}"
source: logs/experiments.jsonl (8 records)
---

# Empirical Axis Priors — cycle 3

Sign convention: `mean_abs_delta` is |val_bpb change| regardless of sign; the note records direction.

| axis | direction | n | mean_abs_delta | status |
|---|---|---|---|---|
| total_batch_size | decrease | 3 | 0.0340 | **SATURATED** — 2**19->2**18 +0.0256 KEEP, 2**18->2**17 +0.0760 KEEP, 2**17->2**16 +0.0003 FLAT |
| warmup_ratio | increase | 1 | 0.0278 (DISCARD) | COLD n=1 — warmup costs budget |
| depth | increase | 1 | 0.0215 (DISCARD) | n=1, confounded with width 640 and -41% steps |
| aspect_ratio | decrease | 1 | 0.0088 (DISCARD) | n=1 — width 256 capacity-limited at 2.4x steps |
| warmdown_ratio | decrease | 1 | 0.0068 (DISCARD) | n=1 — long anneal load-bearing |
| value_embedding_layers | increase | 1 | 0.0060 (DISCARD) | n=1, zero step cost — capacity addition flat/harmful |
| muon_momentum_ramp | decrease | 1 | 0.0041 (DISCARD) | n=1 near-miss (1.35x band); needs far/opposite probe |
| device_batch_size | decrease | 1 | baseline only | hardware prerequisite, not a metric probe |
| activation_fn | replace | 0 | - | COLD, exploration bonus — queued (exp_activation_silu) |
| value_embedding_layers | decrease | 0 | - | COLD opposite arm — queued (exp_ve_none) |
| head_dim | decrease | 0 | - | COLD, zero step cost — queued (exp_head_dim_64) |
| n_kv_head | decrease | 0 | - | COLD — queued in throughput (exp_gqa_kv1) |
| mlp_expansion | both | 0 | - | COLD but deprioritised: step-costly in a step-saturated regime |
| depth_at_fixed_width | decrease | 0 | - | COLD, WITHDRAWN (its step-gain premise died) |
| matrix_lr / embedding_lr / adam_betas / weight_decay / unembedding_lr | bracket | 0 | - | COLD — queued in gradient-quality / throughput |
| window_pattern / ns_steps / rope_base / softcap / scalar_lr / x0 init | - | 0 | - | COLD, sub-band expected effect (see ledger skips) |

## Derived quantity that now governs ranking: the step slope
Fitted over 373 -> 719 steps: 0.1159 val_bpb per ln(step) (~0.011 per +10% steps).
Measured over 719 -> 1396 steps: **~0.000 per ln(step)**.
The curve has a knee at ~719 steps. Use the slope ONLY below the knee; above it, step-count changes
are worth zero and proposals must be ranked by per-step quality at fixed steps.
"""

deadends = f"""---
count: 2
updated_at: "{NOW}"
---

# Dead Ends

## Noise-contamination re-triage (cycle 3, analyst3)
Team noise floor is still the conservative 0.003 band (n_pairs=0, unlocked). Both existing entries have
|delta| >= 0.0060, i.e. 2.0x the band, so **neither is noise-contaminated** and both stay as recorded.
No entry is downgraded this cycle.

- exp_id: exp_depth_10
  axis: depth
  direction: increase
  value: 10
  delta: -0.021505 (7.2x band)
  family: exp_depth
  date: 2026-10-22
  reason: DEPTH 8->10 also forced n_embd 512->640 (+71% params) and DEVICE_BATCH_SIZE 32; 373->221 steps.
  Capacity gain lost to step loss. Axis NOT closed: the depth-only probe at fixed width is still untested,
  and the 6-arm (exp_depth_6) was superseded only because its step-gain premise died, not because depth is refuted.

- exp_id: exp_ve_all_layers
  axis: value_embedding_layers
  direction: increase
  value: all layers (8 of 8)
  delta: -0.006029 (2.0x band)
  family: exp_ve
  date: 2026-10-22
  reason: +33% params at zero step cost (716 vs 719 steps) still regressed. Extra embedding capacity is
  flat-to-harmful at 94M tokens; plausible mechanism is update dilution in the shared AdamW embedding-LR group.
  Opposite arm (0 of 8) is queued as exp_ve_none to complete the 0/4/8 bracket.

## Axis-level saturation (not a mechanism dead end)
- **TOTAL_BATCH_SIZE below 2**17**: saturated, not refuted.** 2**17->2**16 gave 1396 steps and +0.00032.
  Do not propose further halving, and do not justify any future probe by "+steps" above ~700 steps.
- **Capacity-for-steps trades**: three consecutive losses (aspect_32 -0.0088, depth_10 -0.0215, mlp rationale gone).
  Any proposal that trades width or depth for steps should be treated as pre-falsified.
"""
put("strategy.md",strategy); put("knowledge/baseline_coverage.md",bcoverage)
put("knowledge/axis_priors.md",priors); put("dead_ends.md",deadends)
