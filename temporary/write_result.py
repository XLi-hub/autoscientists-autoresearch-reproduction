import json, requests, yaml
from datetime import datetime, timezone

FOCUS_ROOT='/root/autodl-tmp/ar_20261024'; AGENT_NAME='ar_20261024_gpu10'
creds=json.load(open(f'{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json'))
HEADERS={'Authorization':f"Bearer {creds['api_key']}",'Content-Type':'application/json','X-Agent-Name':AGENT_NAME}
API='http://localhost:3000/api/v1'; MAIN=open(f'{FOCUS_ROOT}/WORKSPACE_ID').read().strip()
CAP='d7c6f814-aab0-4029-a887-04345d274f9b'

def pf(resp):
    c=resp.get('content',''); p=c.split('---')
    return yaml.safe_load(p[1]) if len(p)>=3 else {}

OUR=1.097234
champ_raw=requests.get(f'{API}/workspaces/{MAIN}/files/champion.md',headers=HEADERS).json()
champ=pf(champ_raw)
metric_name=champ['metric_name']; direction=champ.get('direction','minimize')
assert metric_name=='val_bpb'
current_best=float(champ['metric_value'])   # HARD-FAIL design: no default
delta=OUR-current_best                       # minimize: positive = worse
sigma=0.00266; MARGIN=2.0
nsigma=abs(delta)/sigma
outcome='KEEP' if delta<0 else 'DISCARD'
print(f'champion {current_best} ours {OUR} delta {delta:+.6f} nsigma {nsigma:.2f} -> {outcome}')

result_md = f"""---
exp_id: exp_cap_ar80_w640
agent: {AGENT_NAME}
team: capacity
axis: aspect_ratio
direction: increase
value: 80
current_value: 64
base: exp_tput_batch_2e17
metric_name: val_bpb
metric_value: {OUR}
delta: {delta:+.6f}
delta_sigma: {nsigma:.2f}
outcome: {outcome}
timestamp: {datetime.now(timezone.utc).isoformat()}
---

# exp_cap_ar80_w640: ASPECT_RATIO 64 -> 80 (width 512 -> 640, n_head 4 -> 5) — DISCARD

## Experiment
One change vs champion `exp_tput_batch_2e17` (val_bpb 1.088286), line 433 of train.py:

```python
ASPECT_RATIO = 80   # was 64 -> model_dim 640, n_head 5, DEPTH 8 held
```

Everything else held: MLP_EXPANSION 2, HEAD_DIM 128, TOTAL_BATCH_SIZE 2**17, DEVICE_BATCH_SIZE 64
(grad_accum 1), WINDOW_PATTERN SSSL, compile max-autotune-no-cudagraphs, seed 42.
This is the far-probe upper arm of the 3-point AR bracket; the lower arm (AR48 on this base,
`exp_cap_ar48_b2e17`) measured +0.000312.

## Result
- **val_bpb = {OUR}** vs champion {current_best} -> **delta {delta:+.6f} (worse)**
- |delta| = **{nsigma:.2f} sigma** (sigma {sigma}, 2-sigma 0.00532) -> **outside the noise band: a real regression.**
  No second seed required (the Step 7.0 gate only triggers for a promotable KEEP; this is not one).
- Outcome: **{outcome}**. Champion unchanged at {current_best}.
- Params **57.72M vs 41.94M (+37.5%)** — predicted 57.67M, measured 57,672,336 (+0.01%).
- FLOPs/token **2.6739e8 vs 1.8874e8 (+41.7%)** — prediction exact.
- Steps **682 vs 956 (-28.7%)** | tokens 89.4M vs 125.3M | tok/s 292.6K vs 411.3K (-28.9%)
- peak_vram 24,669 MB (75.3% of 32,760 MB) — **dbs=64 fit; no fallback needed, so this arm is a clean
  single-variable width probe with no batch-size confound.**
- training_seconds 300.2 | total_seconds 563.9 (max-autotune re-benchmarked the 640x5 head shapes:
  +83s startup/eval vs the champion's 381.8s) | mfu 7.93%

## Prediction check (the FLOPs model holds for matrix-dominated axes)
| quantity | predicted before running | measured | error |
|---|---|---|---|
| params | 57.67M | 57.72M | +0.01% |
| FLOPs/token | 2.674e8 | 2.674e8 | ~0 |
| tok/s | 290.2K (188.7/267.4 x 411.3K) | 292.6K | +0.8% |
| steps | 675 | 682 | +1.0% |
analyst2's independent rebase predicted ~650 (range 620-680). The analytic FLOPs ratio is an excellent
step predictor for width changes — unlike attention-layout changes, where `estimate_flops()` failed
(exp_cap_window_ssll: predicted -5.6% steps, measured -0.9%). Width is matrix-dominated; the
distinction is now empirically established on this GPU.

## Confound decomposition (capacity vs step loss)
The change necessarily couples capacity up with steps down. Two competing priors for the step term:

| step-cost model | implied step cost for -28.7% steps | implied capacity effect |
|---|---|---|
| measured saturated channel on THIS base (exp_tput_batch_2e16: +94% steps -> -0.002711) | **+0.0009** | **+0.0080 (capacity hurts)** |
| MLP-derived prior (0.12 bpb per ln step ratio, analyst3's axis_priors) | +0.0404 | -0.0315 (capacity helps) |

The measured total is +0.0089 — **4.5x smaller than the MLP-derived prior predicts from step loss
alone**. That refutes the old step-scaling prior at this base and is consistent with the saturated-channel
measurement. Under the saturated model (the only one measured at this operating point) the point
estimate is a capacity *penalty*, not a gain. Either way, there is **no step-cost assumption under
which capacity-up pays a measurable gain large enough to repay the lost steps**: the total effect is a
3.36-sigma regression.

## Width bracket is now closed on the current base
| config | width | params | steps | val_bpb | delta vs 512 |
|---|---|---|---|---|---|
| exp_cap_ar48_b2e17 | 384 | 28.3M | 1348 | 1.088598 | +0.000312 (0.12 sigma) |
| **champion** | **512** | **41.94M** | **956** | **1.088286** | **0** |
| exp_cap_ar80_w640 (this) | 640 | 57.72M | 682 | 1.097234 | +0.008948 (3.36 sigma) |

Both directions away from width 512 are now measured and both are worse. The width axis is a flat-to-worse
plateau around 512, bracket complete, **do not refile fine AR points**.

## Training Dynamics
| progress | step | loss |
|---|---|---|
| 0% | 0 | 9.0110 |
| 18.6% | 136 | 3.8449 |
| 38.9% | 272 | 3.4914 |
| 59.2% | 408 | 3.3307 |
| 79.6% | 545 | 3.1774 |
| 99.9% | 681 | 3.0878 |

1. **Undertrained on train loss, but it does not transfer.** Final-20% drop = 0.0896 = **1.51% of the
   total range** (>1% threshold) — the largest final-20% drop observed so far (champion calibration
   measured 0.0630). The wider model is still descending when the budget expires. Yet val_bpb is worse,
   so this is per-step/per-sample generalisation cost, not a dynamics anomaly. Consistent with gpu3's
   train/val divergence finding at 1348 steps.
2. **No early plateau.** Smooth decline through 80% of the run.
3. **Steps 682 (-28.7% vs champion) — flagged.** Above the 10% threshold that makes a fixed-time
   benchmark uphill; that is the whole reason this is a capacity/step-coupled probe.

## Secondary confound (small, and it points the same way)
`setup_optimizer` applies `dmodel_lr_scale = (model_dim/768)**-0.5` to the AdamW groups only
(lm_head, token embeddings, value embeddings) — it is NOT applied to `matrix_lr`. At width 640 that
multiplier is 1.0954; at width 512 it is 1.2247. So this run's AdamW LRs were **10.6% lower** than the
champion's. This does not change the verdict (a lower LR on the embedding groups cannot manufacture a
capacity gain) but it means the arm is very slightly "width change + AdamW LR down". If a future width
probe ever KEEPs, re-test with the LR scale pinned.

## Interpretation (capacity hypothesis lens)
The stated capacity hypothesis was: *"parametric capacity or representational structure limits val_bpb
at this compute."* Adding 39% parameters at fixed depth, with the step channel already saturated, bought
nothing — it cost 3.4 sigma. Together with AR48 at this base (+0.31 sigma for -33% params), the width
direction of that hypothesis is **not supported at the 956-step operating point**.

The historical AR64->48 KEEP (-0.037 at a 433-step base) is now fully explained as a step-count artifact:
the same lever at a 956-step base is worth +0.0003. Width was never a capacity lever in this regime.

## Consequences for the queue
- `aspect_ratio` increase: MEASURED at the far probe (80). Close the direction.
- The 3-point bracket (48/64/80) is complete at the current base. No more AR points.
- `exp_cap_depth12_w512` (+41% params, -31% steps) carries the same capacity-up bet that just failed by
  3.4 sigma at a larger step cost. Recommend **demote to low / do not run** rather than spend a slot.
- `exp_cap_ve_density_2` (-18% params, 0 FLOPs, step-neutral) is now the only capacity item that
  isolates capacity from step count in the *down* direction. With width flat and head_dim harmful, the
  remaining capacity question is representational, not parametric — if it runs, it should be read as
  "does removing parameters cost anything at all" (prediction, from AR48 at this base: nothing).
- Reallocate GPU time to tokens-per-step quality (optimizer/LR/regularization — WEIGHT_DECAY has never
  been varied) rather than more capacity.
"""

r=requests.put(f'{API}/workspaces/{MAIN}/files/results/exp_cap_ar80_w640.md',headers=HEADERS,json={'content':result_md})
print('result file PUT',r.status_code)

# --- Step 6: release claim AND move pending -> completed in one read-modify-PUT
q_raw=requests.get(f'{API}/workspaces/{CAP}/files/queue.md',headers=HEADERS).json()
q=pf(q_raw)
claim_removed=q.get('claims',{}).pop(AGENT_NAME,None) is not None
pending=q.get('pending',[]) or []; completed=q.get('completed',[]) or []
remaining=[]
for it in pending:
    if it.get('id')=='exp_cap_ar80_w640':
        it=dict(it); it['completed_at']=datetime.now(timezone.utc).isoformat()
        it['completed_by']=AGENT_NAME; it['outcome']=outcome
        it['val_score']=OUR; it['delta_vs_champion']=round(delta,6)
        it['discussion_pending']=False
        completed.append(it)
    else: remaining.append(it)
q['pending']=remaining; q['completed']=completed
body=q_raw.get('content','').split('---',2)[-1]
newc=f'---\n{yaml.safe_dump(q,sort_keys=False)}---{body}'
assert yaml.safe_load(newc.split('---')[1])==q
r2=requests.put(f'{API}/workspaces/{CAP}/files/queue.md',headers={**HEADERS,'If-Match':str(q_raw.get('version',0))},json={'content':newc})
print('queue PUT',r2.status_code,'claim_removed',claim_removed)
