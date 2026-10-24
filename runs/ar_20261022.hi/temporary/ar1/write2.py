import json, os, requests
from pathlib import Path
FOCUS=Path("/root/autodl-tmp/ar_20261022.hi")
creds=json.load(open(FOCUS/"agents/ar_20261022hi_analyst1/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name")}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN=open(FOCUS/"WORKSPACE_ID").read().strip()
TEAM="54202fe1-b766-43f1-b374-9e4ed188c153"
def put(ws,path,content):
    r=requests.get(f"{API}/workspaces/{ws}/files/{path}",headers=H)
    v=r.json().get("version",0) if r.status_code==200 else None
    hh=dict(H)
    if v is not None: hh["If-Match"]=str(v)
    rr=requests.put(f"{API}/workspaces/{ws}/files/{path}",headers=hh,json={"content":content})
    print(f"PUT {path}: {rr.status_code}")

STRAT="""---
hypothesis: H-throughput
prediction: "Experiments that increase effective optimizer steps by >=10% will KEEP"
falsification: "3 rotations of prediction-consistent experiments all DISCARD"
age_rotations: 3
supported_keeps: 1
refuted_discards: 2
status: "weakened - prediction refuted, mechanism reformulated"
updated_at: "2026-10-23T00:30:00+00:00"
---

# Team throughput

## Cycle-4 hypothesis check (Step 0.3)

| result | classification |
|---|---|
| exp_batch_2e17 KEEP (+0.076017, 719 steps, +93%) | SUPPORTS -> supported_keeps 1 |
| exp_batch_2e16 DISCARD (+0.000319, 1396 steps, +94%) | REFUTES -> refuted_discards 1 |
| exp_aspect_ratio_32 DISCARD (-0.008807, 1741 steps, +142% steps but 0.34x width) | REFUTES the step clause, confounded by width -> refuted_discards 2 |
| exp_warmdown_070 DISCARD (seed pair) | orthogonal (step-neutral) |
| exp_ve_all_layers / exp_depth_10 (other teams) | orthogonal (capacity, not steps) |

Formal falsification rule (age>=3 AND supported_keeps==0 AND refuted>=3) does NOT fire because
supported_keeps=1. But **2 of 2 experiments that were pure step increases at fixed width DISCARDed**,
so the stated prediction is dead even though the formal counter is not.

## Reformulated hypothesis (H-throughput-v2)

> At fixed width and ~fixed tokens, what exp_batch_2e17 bought was **proximity to the critical batch
> size**, not "more optimizer steps". 262,144 tokens/update (2**18) was ABOVE the critical batch;
> 131,072 (2**17) is at/below the knee and is where the win stopped. Cutting to 65,536 (2**16) doubled
> updates and returned nothing.

Prediction under v2:
- Further batch/step rungs KEEP nothing. **Do not queue them.**
- Remaining wins are either (a) more tokens at fixed FLOPs (lower FLOPs/token without losing
  capacity), or (b) quality per token (LR / regularization / readout), or (c) higher raw throughput.
- (a) is individually sub-noise: GQA kv4->1 is -7.9% FLOPs -> +8.6% tokens -> ~-0.005; MLP 4->3 is
  -11% FLOPs but -12% MLP capacity. Neither clears the 0.006 band alone.
- (c) is the only change that compounds across every later experiment: at the external scaling-law
  rate (~-0.05 bpb per doubling of tokens), **+10% tokens/s is worth ~0.007 bpb** - more than most
  queued knobs, and it improves every subsequent run.

Falsification for v2: a step/batch change below 2**17 that KEEPs by >0.006, or a >=10% throughput
change that moves val_bpb by less than the seed band.

## Cycle-4 budget audit (Step 1e, corrected)

The code logs `mfu` against `H100_BF16_PEAK_FLOPS = 989.5e12`, which is why every result reports
~7.4% "MFU". That number is meaningless on a 4080S and has been misleading the compute audit.

Corrected: RTX 4080 SUPER BF16 dense with FP32 accumulate ~= 2x FP32 = **~104 TFLOPS**.
Champion FLOPs/token (from estimate_flops): 6*(50.33M - 20.97M excluded) + attention
= 176.2M + 12*512*(6*1024 + 2*2048) = 176.2M + 62.9M = **239.1M**.
At 314k tok/s that is **~75 TFLOPS = ~72% of peak**. Memory: 22,653/32,760 MB = **69.3%**.

Verdict: compute efficiency is ABOVE the 50% line (the earlier "idle capacity" reading was an
artifact of the H100 constant). The run is compute-bound, not memory-bound. The Step-1e scale-up
probe still exists in the queue (exp_aspect_ratio_80, +52% FLOPs/token -> ~473 steps) but it is a
*capacity-for-steps trade*, and both available data points on that trade lost (depth_10 -0.097,
ve_all_layers -0.006 = 2.0 sigma). Read aspect_80 as a falsification probe for H-capacity.

## Cycle-4 queue priorities (throughput team)
1. exp_wd_0p0 (HIGH - raised this cycle): cumulative Muon shrink e^-3.0 ~ 0.05 at 719 steps, i.e. the
   run is discarding ~95% of its weight growth. Largest single mechanism in the team's queue.
2. exp_embedding_tied (new): readout-cold-start fix.
3. exp_softcap_30 (new): Layer-3 literal, closes a ledger row.
4. exp_aspect_ratio_80 (medium): pre-registered falsification probe.
5. exp_unembedding_lr_hi (medium) / _lo (low): readout LR bracket; 3x arms are now known to be
   borderline vs the 0.006 band, so run hi first.

## Acceptance rule
A KEEP requires surviving the multi-seed gate: both seeds strictly beat the champion. With
sigma=0.00302, only |delta| >= ~0.006 is decidable. Do not close an axis on one sub-band sample.
"""

BC="""---
name: baseline_coverage
owner: ar_20261022hi_analyst1
updated_at: "2026-10-23T00:30:00+00:00"
champion: exp_batch_2e17 (val_bpb 1.094037)
audit_cycle: 4
---

# Baseline Coverage Audit (Step 1c) - all three layers, champion exp_batch_2e17

Champion: DEPTH 8, ASPECT_RATIO 64 -> n_embd 512, n_head 4 (n_kv_head 4), head_dim 128,
TOTAL_BATCH_SIZE 2**17 (grad_accum 1), DEVICE_BATCH_SIZE 64. 719 steps / 94.2M tokens / 300.4 s /
~314k tok/s / 22,653 MB peak. 50.33M params (blocks 25.17M + wte 4.19M + value_embeds 16.78M +
lm_head 4.19M). 239.1M FLOPs/token -> ~75 TFLOPS (~72% of the 4080S's ~104 TFLOPS bf16 peak).

"tested?" = varied in at least one experiment vs the current champion and compared outside the
0.006 seed band.

| parameter | current_value | tested? | result summary |
|---|---|---|---|
| DEPTH | 8 | PARTIAL | depth_10 confounded with width 640 -> -0.097; depth_6 withdrawn (step premise dead). Depth at FIXED width never tested. |
| ASPECT_RATIO | 64 | YES | 32 -> -0.0088 (2.9 sigma, width 256 capacity-limited). 80 queued (scale-up). |
| HEAD_DIM | 128 | NO (queued) | capacity: exp_head_dim_64, zero FLOPs change. |
| WINDOW_PATTERN | "SSSL" (6 of 8 layers capped at 1024 ctxt) | NO | Never varied. Quality argument (capability) AND ~3% FLOPs. Unowned; capacity recommended. |
| TOTAL_BATCH_SIZE | 2**17 | YES | ladder 2**19->2**16 complete. 2**17 is the optimum rung. SATURATED. |
| DEVICE_BATCH_SIZE | 64 | YES | 128 OOMs (verified). With 2**17 this forces grad_accum=1. |
| EMBEDDING_LR | 0.6 (eff 0.735) | NO (in flight) | analyst2 bracket 0.3/1.2; hi arm claimed by gpu4. |
| UNEMBEDDING_LR | 0.004 (eff 0.0049) | NO (queued) | lm_head only, 4.19M params, **150x colder than the embedding group**; bracket 0.0013/0.012. |
| MATRIX_LR | 0.04 (Muon, NOT dmodel-scaled) | NO (queued) | analyst2 bracket 0.02/0.08 - biggest untested LR lever. |
| SCALAR_LR | 0.5 | NO | 16 scalars (resid group runs at 0.005). No plausible >=0.006 effect. |
| WEIGHT_DECAY (Muon) | 0.2, scheduled *(1-progress)* | NO (queued, HIGH) | Cumulative shrink ~e^-3.0 = 0.05 over 719 steps. Bracket 0.0 / 0.4. |
| ADAM_BETAS | (0.8, 0.95) | PARTIAL | beta2 0.99 -> DISCARD (2 seeds). beta2 0.90, beta1 0.7/0.9 queued. |
| ADAM eps | 1e-10 | NO (queued by analyst2) | effectively zero in bf16; exp_adam_eps_bracket. |
| WARMUP_RATIO | 0.0 | YES | 0.1 -> +0.0278 (9.2 sigma). CLOSED. |
| WARMDOWN_RATIO | 0.5 | YES | 0.25 -> -0.0068 (2.2 sigma); 0.7 -> tie (0.59 sigma). Closed around 0.5. |
| FINAL_LR_FRAC | 0.0 | NO | LR ends at exactly 0; every run's loss is still falling in the tail. Handed to throughput by analyst2, still unqueued. |
| MLP expansion | 4x (inline literal, twice) | NO (queued) | capacity: 6x queued, 3x withdrawn (step premise dead). |
| value embeddings | alternating (4 of 8) | PARTIAL | all 8 -> -0.0060 = 2.0 sigma, INCONCLUSIVE. 0 of 8 (ve_none) queued. |
| Muon momentum | ramp 0.85->0.95 over 300 steps (absolute, not progress) | PARTIAL | ramp 60 -> +0.0041 = 1.34 sigma (NOISE). Far probe to 900 queued by analyst2. Endpoint 0.95 never varied alone. |
| Muon ns_steps | 5 | NO | Changing it also changes update MAGNITUDE via NorMuon final_scale -> confounded with matrix_lr. |
| **softcap** | **15** (L3 literal in forward()) | **NO (queued this cycle)** | Bounds max logit at 15; d(tanh)/dx at logit 10 is 0.64, so the most confident tokens get ~36% gradient attenuation. |
| **tied embeddings** | **untied** (lm_head std 0.001, LR 0.0049) | **NO (queued this cycle)** | The readout is the coldest, most starved group in a 719-step run. Shared-table collapse: -4.19M params (-8.3% total, -14% compute). |
| RoPE base | 10000 | NO | no evidence position encoding binds at seq 2048. |
| x0_lambdas / resid_lambdas init | 0.1 / 1.0 | NO | both learned (LR 0.5 / 0.005); init washes out. |

## Cross-cutting facts
- Same-seed reproducibility is ~2e-4; SEED choice dominates the 0.006 band.
- 42% of all parameters (21M) are lookup tables with zero FLOP cost; 33% of compute params
  (16.8M/29.4M) are the value embeddings' *tables*, which cost nothing per token.
- The readout (lm_head) is the only compute-bearing matrix with a near-zero init (std 0.001) and a
  150x colder LR. That asymmetry is what ties the "unembedding_lr" and "tied" proposals together.
"""

LEDGER="""---
name: unqueued_axes
version: 4
owner: ar_20261022hi_analyst1
updated_at: "2026-10-23T00:35:00+00:00"
noise_sigma: 0.003019
noise_2sigma: 0.00604
---

# Unqueued Axes Ledger (team copy; canonical = main workspace, v10)

Cycle 4: the canonical ledger was re-walked by analyst2 at 00:12. This team copy is synced to it and
adds the two rows this cycle queues. Slack rule in force: a probe is only worth a GPU slot if its
mechanism predicts |delta| > 0.00604.

| axis | direction | value | status | decision / reason |
|---|---|---|---|---|
| total_batch_size | decrease | 2**17 | tested (champion) | optimum rung; 2**16 flat (0.11 sigma). SATURATED - no further rungs. |
| warmdown_ratio | either | - | tested/CLOSED | 0.25 -0.0068 (2.2 sigma); 0.7 tie (0.59 sigma). |
| warmup_ratio | increase | 0.1 | tested/CLOSED | +0.0278 (9.2 sigma). |
| aspect_ratio | decrease | 32 | tested | -0.0088 (2.9 sigma). |
| aspect_ratio | increase | 80 | queued | Step 1e scale-up; predicted DISCARD. |
| weight_decay | decrease | 0.0 | **queued HIGH** | cumulative shrink e^-3.0; biggest mechanism in this team's queue. |
| weight_decay | increase | 0.4 | queued low | curvature arm. |
| unembedding_lr | either | 0.0013 / 0.012 | queued | readout 150x colder than embeddings; 3x arms are borderline vs 0.006. Run hi first. |
| n_kv_head | decrease | 1 (GQA 4:1) | in flight (gpu1) | -7.9% FLOPs -> +8.6% tokens -> ~-0.005, expected sub-band; run as a throughput probe only. |
| **softcap** | **increase** | **30** | **queued this cycle (new)** | Layer-3 literal never varied. Bounds max logit at 15; the most confident tokens get ~36% gradient attenuation. Closing probe. |
| **tied_embeddings** | **replace** | **lm_head <- wte** | **queued this cycle (new)** | Readout starts at std 0.001 with 0.0049 LR; tying gives it the wte geometry and the 0.735 LR. Bold: shared-table collapse, -14% compute params. |
| final_lr_frac | increase | 0.1 | unqueued | analyst2 handed this to throughput. Skip THIS cycle (pairs badly with a 2.2-sigma-negative warmdown-0.25 result), revisit if the tail-drop signal grows. |
| window_pattern | replace | SSSS / LLSS | unqueued | capability item, unowned. Recommend capacity; not a throughput probe (3% FLOPs). |
| muon_momentum endpoint | decrease/increase | 0.90 / 0.98 | unqueued | ramp covered by analyst2's ramp_900 far probe; re-walk after it reports. |
| scalar_lr / rope_base / softcap<30 / ns_steps / polar divisor / dmodel scale | - | - | unqueued | skip with reasons recorded in the canonical ledger (sub-band or confounded). |
"""
put(TEAM,"strategy.md",STRAT)
put(TEAM,"knowledge/baseline_coverage.md",BC)
put(TEAM,"knowledge/unqueued_axes.md",LEDGER)

DE="""---
count: 3
updated_at: "2026-10-23T00:35:00+00:00"
---

# Dead Ends

**Noise re-triage (cycle 4, sigma=0.00302, 2-sigma=0.00604).** Entries whose |delta| is below the
2-sigma band are NOT closed; they are downgraded to "inconclusive" and the axis stays open.

- exp_id: exp_warmdown_025
  axis: warmdown_ratio, direction: decrease, value: 0.25, delta: -0.006763 (2.2 sigma)
  status: **marginal, 1 seed** - not closed; axis closed only because 0.7 also failed to beat it.
- exp_id: exp_warmdown_070
  axis: warmdown_ratio, direction: increase, value: 0.7, delta: -0.000289 seed42 / +0.003849 seed43
  status: **tie (0.59 sigma)** -> warmdown is flat away from 0.5 in both directions. CLOSED as "flat".
- exp_id: exp_aspect_ratio_32
  axis: aspect_ratio, direction: decrease, value: 32, delta: -0.008807 (2.9 sigma)
  status: real. Width 256 is capacity-limited. Low arm closed; high arm (80) still queued.
- exp_id: exp_batch_2e16
  axis: total_batch_size, direction: decrease, value: 2**16, delta: +0.000319 (0.11 sigma)
  status: FLAT. Batch/step axis saturated at 2**17; do not queue further rungs.
- exp_id: exp_muon_mom_ramp60
  axis: muon_momentum_ramp, direction: decrease, value: 60, delta: +0.004053 (1.34 sigma)
  status: **NOISE-CONTAMINATED - axis remains open** (analyst2 has queued the far probe, divisor 900).
"""
put(TEAM,"dead_ends.md",DE)
