import json, requests, yaml, shutil
from datetime import datetime, timezone
from pathlib import Path

FOCUS_ROOT='/root/autodl-tmp/ar_20261024'; AGENT_NAME='ar_20261024_gpu10'
creds=json.load(open(f'{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json'))
HEADERS={'Authorization':f"Bearer {creds['api_key']}",'Content-Type':'application/json','X-Agent-Name':AGENT_NAME}
API='http://localhost:3000/api/v1'; MAIN=open(f'{FOCUS_ROOT}/WORKSPACE_ID').read().strip()
WORKSHOP=open(f'{FOCUS_ROOT}/WORKSHOP_NAME').read().strip()
CAP='d7c6f814-aab0-4029-a887-04345d274f9b'
def pf(resp):
    c=resp.get('content',''); p=c.split('---')
    return yaml.safe_load(p[1]) if len(p)>=3 else {}

OUR=1.097234; CURRENT=1.088286; DELTA=OUR-CURRENT; NSIG=DELTA/0.00266
ws=Path(f'{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace'); rep=ws/'repo'

# Step 4: stamped agent-local train copy
shutil.copy(rep/'train.py', rep/'train_exp_cap_ar80_w640.py')
print('stamped', rep/'train_exp_cap_ar80_w640.py')

# Step 8: [RESULT] post
content = f"""## Experiment
exp_cap_ar80_w640 — ASPECT_RATIO 64 -> 80 on champion `exp_tput_batch_2e17` (width 512 -> 640,
n_head 4 -> 5, DEPTH 8, MLP_EXPANSION 2, TOTAL_BATCH_SIZE 2**17, DEVICE_BATCH_SIZE 64 held).
Far-probe upper arm of the 3-point AR bracket. Clean single-variable width probe: dbs=64 fit
(peak VRAM 24.7/32.7 GB), no batch/config fallback was needed.

## Result
val_bpb: **{OUR}**
Delta: **{DELTA:+.6f}** (worse)
Outcome: **DISCARD** ({NSIG:.2f} sigma, sigma 0.00266, 2-sigma 0.00532 -> outside the band)
Race condition: False (champion.md v13 unchanged before/after)
Steps 682 vs 956 (-28.7%) | tokens 89.4M vs 125.3M | tok/s 292.6K vs 411.3K | params 57.72M vs 41.94M (+37.5%) | FLOPs/tok 2.674e8 vs 1.887e8 (+41.7%)

## Why this is decisive, not just a null
1. **The step-cost confound is bounded and small at this base.** Measured saturated step channel
   (exp_tput_batch_2e16: +94% steps -> -0.002711) prices -28.7% steps at only **+0.0009**. Under that
   (only locally measured) model the capacity effect is **+0.0080 — capacity up HURTS**. The
   MLP-derived prior (0.12 bpb/ln) predicts +0.0404 from step loss alone — 4.5x more than the whole
   measured regression, so that prior is refuted as a step predictor at 956 steps.
2. **The width bracket is now complete at the current base:** 384 -> 1.088598 (+0.12 sigma),
   512 -> 1.088286 (champion), 640 -> 1.097234 (+3.36 sigma). Both directions worse. Fine AR points
   are worthless; close the axis.
3. **It retires the capacity hypothesis on the parametrisation axis.** The earlier AR64->48 KEEP
   (-0.037 at a 433-step base) is fully explained as a step-count artifact: the same lever at 956 steps
   is worth +0.0003. Width was never a capacity lever in this regime — it was a FLOPs-per-token lever,
   and that channel is exhausted.
4. **FLOPs model validated for matrix axes:** predicted 57.67M params / 2.674e8 FLOPs / 290.2K tok-s /
   675 steps; measured 57.72M / 2.674e8 / 292.6K / 682 (+0.01%, ~0, +0.8%, +1.0%).

## Queue consequences
- `aspect_ratio` direction=increase: MEASURED at the far probe. CLOSED. Do not refile AR 72/88/etc.
- `exp_cap_depth12_w512` (+41% params, -31% steps): same capacity-up bet with a larger step cost.
  Recommend DEMOTE / do not run — the prior is now negative.
- `exp_cap_ve_density_2` (-18% params, 0 FLOPs, step-neutral) is the only remaining capacity item that
  isolates capacity from steps; prior from AR48 says it will be flat.
- Recommend reallocating to tokens-per-step quality. WEIGHT_DECAY has never been varied (0.2, and Muon
  decay is lr*wd*p so it is also an LR knob).

## Training dynamics
Final-20% loss drop 0.0896 = 1.51% of range (largest observed; champion calibration 0.0630) — the wider
model was still descending, yet val_bpb got worse: generalisation cost, not a dynamics anomaly.
No early plateau. Secondary confound: `dmodel_lr_scale` (AdamW groups only) is 1.0954 at width 640 vs
1.2247 at 512, so AdamW LRs were 10.6% lower — cannot manufacture a capacity gain.

## Team
capacity

Result file: results/exp_cap_ar80_w640.md
"""
r=requests.post(f'{API}/posts',headers=HEADERS,json={
    'workshop':WORKSHOP,
    'title':f'[RESULT] exp_cap_ar80_w640: val_bpb={OUR} (DISCARD — capacity-UP fails at 3.36 sigma; width bracket CLOSED)',
    'content':content,
    'tags':['team:capacity','type:result','outcome:DISCARD','axis:aspect_ratio'],
})
post_id=r.json().get('id') if r.ok else None
print('POST',r.status_code,post_id)

# dead_ends entry
de_raw=requests.get(f'{API}/workspaces/{CAP}/files/dead_ends.md',headers=HEADERS).json()
entry=(
 "\n- exp_id: exp_cap_ar80_w640\n"
 "  axis: aspect_ratio\n"
 "  direction: increase\n"
 "  value: 80\n"
 "  delta: +0.008948 (worse; 3.36 sigma vs sigma 0.00266)\n"
 "  family: exp_cap\n"
 f"  date: {datetime.now(timezone.utc).date()}\n"
 "  reason: width 512->640 (+37.5% params, +41.7% FLOPs/token, 682 steps vs 956). Bracket closed:\n"
 "    384 +0.000312 / 512 champion / 640 +0.008948. Capacity-UP pays nothing at 956 steps; the earlier\n"
 "    AR64->48 KEEP was a step-count artifact. Do not refile fine AR points or depth12-class scale-ups.\n"
)
r3=requests.put(f'{API}/workspaces/{CAP}/files/dead_ends.md',headers={**HEADERS,'If-Match':str(de_raw.get('version',0))},
                json={'content':de_raw.get('content','')+entry})
print('dead_ends PUT',r3.status_code)

# result_latest.json -> complete + posted data
rl_path=ws/'result_latest.json'
rl=json.loads(rl_path.read_text())
rl.update({'val_score':OUR,'delta':round(DELTA,6),'outcome':'DISCARD','status':'complete',
           'posted_to_workshop':True,'result_post_id':post_id,
           'train_path':str(rep/'train_exp_cap_ar80_w640.py'),
           'posted_at':datetime.now(timezone.utc).isoformat(),
           'champion_before':CURRENT,'champion_after':CURRENT})
rl_path.write_text(json.dumps(rl,indent=2,default=str))
print('sentinel ->', {k:rl.get(k) for k in ('status','posted_to_workshop','result_post_id','val_score','outcome')})
