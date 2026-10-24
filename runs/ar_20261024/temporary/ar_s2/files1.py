import json, os, requests, yaml, time
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"; AGENT_NAME="ar_20261024_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
TEAM_WS_ID="005cb9ec-6fce-4bba-9340-21c08ab914c5"
NOW="2026-10-24T07:23:30Z"
def put(path, content):
    for attempt in range(2):
        r=requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/{path}",headers=HEADERS).json()
        v=r.get("version",0)
        resp=requests.put(f"{API}/workspaces/{TEAM_WS_ID}/files/{path}",
            headers={**HEADERS,"If-Match":str(v)},json={"content":content})
        if resp.status_code==200:
            print("PUT",path,"ok v",resp.json().get("version")); return True
        print("PUT",path,"fail",resp.status_code,resp.text[:200]); time.sleep(1)
    return False

dead = """---
count: 2
updated_at: "2026-10-24T07:23:30Z"
updated_by: ar_20261024_analyst2
noise_floor_sigma: 0.002865
noise_band_2sigma: 0.00573
note: "Re-triaged 2026-10-24: both entries below are NOISE-CONTAMINATED — recorded |delta| is inside the
  team's measured 2-sigma band, so neither axis is closed. Kept for institutional memory; see reasons."
---

# Dead Ends

## NOISE-CONTAMINATED (axis remains open) — do not treat as closed

- exp_id: exp_gq_muon_mom_098
  axis: muon_momentum
  direction: increase
  value: 0.98
  status: NOISE-CONTAMINATED — axis remains open
  delta_vs_contemporaneous_base: +0.000181 (paired seed 42; |delta| is 32x below the 2-sigma band)
  seeds: [1.192527 (s42), 1.188308 (s43)] on identical code -> seed swing 0.004219
  family: exp_gq
  date: 2026-10-24
  reason: |
    Single paired point, far inside the noise band => no measurable mechanism, therefore NOT a refutation.
    Also stale: tested on the TOTAL_BATCH 2**19 base (~196 steps), where the step-based ramp only reached
    frac 0.653. On the current 2**18 champion (433 steps) the ramp reaches terminal momentum at step 300
    (69% of the run), so a retest would probe a strictly different regime. Do not re-queue the 0.98 target
    until exp_gq_muon_ramp_progress lands (it changes the trajectory the target acts on).

- exp_id: exp_gq_warmdown_025
  axis: warmdown_ratio
  direction: decrease
  value: 0.25
  status: NOISE-CONTAMINATED — axis remains open
  delta_vs_contemporaneous_base: +0.004863 (1.162970 vs 1.158107; inside the 0.00573 2-sigma band)
  family: exp_gq
  date: 2026-10-24
  reason: |
    Single seed, inside noise, and no step-count gain (416 vs 410). Not a refutation of the axis.
    The opposite arm (0.75) is still queued and completes the 3-point bracket. Axis stays open.
"""

strategy = """---
hypothesis: Gradient signal per optimizer step is suboptimal; changes that reduce
  gradient noise or improve update direction (optimizer geometry, momentum, normalization,
  LR schedule shape) will lower val_bpb.
prediction: Experiments changing Muon/Adam betas, momentum ramp, LR ratios, or norm
  placement will KEEP beyond the noise band.
falsification: 3 rotations of prediction-consistent gradient-quality experiments all
  DISCARD.
age_rotations: 2
supported_keeps: 0
refuted_discards: 2
last_audited_by: ar_20261024_analyst2
last_audited_at: '2026-10-24T07:23:30Z'
---

# Team gradient-quality

**Hypothesis:** Gradient signal per optimizer step is suboptimal; changes that reduce gradient noise or improve update direction (optimizer geometry, momentum, normalization, LR schedule shape) will lower val_bpb.

**Prediction:** Experiments changing Muon/Adam betas, momentum ramp, LR ratios, or norm placement will KEEP beyond the noise band.

**Falsification:** 3 rotations of prediction-consistent gradient-quality experiments all DISCARD.

Teams are hypothesis-based, not axis-based: any axis is in-scope if the hypothesis predicts it will KEEP.

## Cycle 2 audit (analyst2, after champion moved 1.192708 -> 1.147892)

**Hypothesis scorecard.** age_rotations 1 -> 2.
- refuted_discards: 2 — exp_gq_muon_mom_098 (muon_momentum 0.98, prediction-named axis) and
  exp_gq_warmdown_025 (LR schedule shape, prediction-named). Both are INSIDE the 2-sigma noise
  band (0.0057): muon paired effect +0.00018, warmdown +0.00486. Counted as refutations because
  the prediction said they would KEEP beyond noise, but they are WEAK evidence — do not treat
  them as a mechanism failure yet.
- supported_keeps: 0. No gq experiment has KEEPed.
- Falsification is therefore 1 rotation away (age 3 with supported_keeps 0 and refuted >= 3).
  If the adam-beta bracket returns two flat/DISCARD arms, the team hypothesis should be
  re-scoped rather than defended.

**What changed the operating point (Step 1b2).** All three KEEPs were throughput KEEPs and all
three bought the same thing: more optimizer steps in the fixed 300 s budget (193 -> 374 -> 410
-> 433). The 2**18 KEEP won while processing FEWER tokens (98.0M vs 101.2M), so the response is
to update count, not token count. Every run is still undertrained (final-20% loss drop 2.3-2.6%
of range, no plateau).

**Consequence for gq: every step-count-coupled optimizer constant is now mis-scaled.**
- `get_muon_momentum` still uses step/300. At 433 steps that reaches terminal momentum at step
  300 = 69% of the run; the upstream-intended shape (300/953) is ~31%. exp_gq_muon_ramp_progress
  is therefore MORE relevant than when filed and stays high priority.
- AdamW betas (0.8, 0.95) have memory 1/(1-beta) in STEPS. The 2.24x step-count increase means
  they now cover 2.24x less of training than when tuned. This is the largest re-opened gq lever;
  filed as exp_gq_adam_betas_bracket (low (0.7,0.90) / high (0.9,0.99), champion midpoint).
- Wall-clock-based schedules (LR multiplier, weight decay) are NOT rescaled by the step-count
  change: they remain as tuned. Do not propose them as "step-scaled" fixes.

**Step 1b2 follower.** exp_gq_mlp_exp_2 (MLP 3x -> 2x) carries the productive property forward
through a different mechanism (cheaper tokens/step rather than fewer tokens/step). Confound:
-9.1% capacity; the queued throughput 5x arm closes a 2/3/5 bracket.

**Compute-budget audit (Step 1e).** Champion peak VRAM 22.6 GB / 32 GB = ~71% (at the 70%
threshold); reported mfu_percent is H100-normalized (7.6%) and meaningless on a 4080S, and the
binding resource is the 300 s wall-clock budget, which is 100% used. No mandatory scale-up probe;
a scale-up would be anti-throughput at this operating point.

**Queue (5 items).** high: exp_gq_muon_ramp_progress, exp_gq_adam_betas_lo, exp_gq_adam_betas_hi,
exp_gq_mlp_exp_2. medium: exp_gq_warmdown_075 (bracket-completion, low expected value).
All are discussion_pending: true; the two proposals from this cycle are
63601f5a (adam betas) and 306479b7 (mlp 2x).
"""

print(put("dead_ends.md", dead))
print(put("strategy.md", strategy))
