import json, yaml, requests, math
from pathlib import Path
from datetime import datetime, timezone

AGENT_NAME = "ar_20261024_gpu9"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
GQ = "005cb9ec-6fce-4bba-9340-21c08ab914c5"
NOW = datetime.now(timezone.utc).isoformat()

OUR = 1.089445; CHAMP = 1.088286; LO42 = 1.086983
delta = OUR - CHAMP            # +0.001159 (worse)
arm_mean = (LO42 + OUR)/2
arm_delta = arm_mean - CHAMP   # vs champion
seed_pair = abs(LO42 - OUR)

result_md = f"""---
exp_id: exp_gq_matrix_lr_lo_seed43
axis: matrix_lr
direction: decrease
value: 0.02 (seed 43)
current_value: 0.04
val_bpb: {OUR}
champion_at_measure: {CHAMP} (exp_tput_batch_2e17)
delta_ours_minus_champ: {delta:+.6f}
outcome: DISCARD
team: gradient-quality (claimed by capacity agent)
agent: {AGENT_NAME}
confirmation_of: exp_gq_matrix_lr_lo
timestamp: {NOW}
---

# exp_gq_matrix_lr_lo_seed43

## Experiment

Step 7.0 **second seed** of `exp_gq_matrix_lr_lo`. `champion/train.py` verbatim except three lines:
`MATRIX_LR = 0.02` (was 0.04) and `torch.manual_seed(43)` / `torch.cuda.manual_seed(43)` (were 42).
Nothing else. Diff verified: 3 changed lines. Run on **GPU 1** — the same device gpu7 used for the
seed-42 arm, so this pair differs by **seed only**.

## Result

- val_bpb = **{OUR}** (seed 43)
- Champion at measure: {CHAMP}; delta = **{delta:+.6f}**
- Gate: sigma = 0.002503 (5-pair pooled, updated this run), 2-sigma = 0.005007. |delta| = 0.001159
  is **0.46 sigma** — nowhere near promotion. **Champion unchanged.**
- Outcome: **DISCARD** (does not beat champion). This is a *confirmation failure*, not a refutation
  of a large effect.

## The verdict on MATRIX_LR = 0.02

| sample | seed | GPU | val_bpb | delta vs champion |
|---|---|---|---|---|
| champion (MATRIX_LR 0.04) | 42 | 1 | 1.088286 | — |
| lo arm, original | 42 | 1 | 1.086983 | -0.001303 |
| **lo arm, this run** | **43** | **1** | **{OUR}** | **{delta:+.6f}** |

- Two-seed mean of the lo arm = **{arm_mean:.6f}**, delta vs champion = **{arm_delta:+.6f}**.
  MATRIX_LR 0.02 is **FLAT** — the arm's apparent -0.0013 was a lucky seed-42 draw.
- The two lo-arm samples differ from each other by **{seed_pair:.6f}**. That is a *seed-only,
  same-GPU, same-code* pair — the cleanest noise sample in the run — and it is **1.9x larger than
  the effect the arm appeared to show**. The arm was never resolvable at this noise level.
- Bracket status at 2x scale: hi (0.08) = +0.003688, lo (0.02, 2-seed mean) = {arm_delta:+.6f}.
  Both inside the 2-sigma band, opposite signs -> per the pre-registered decision rule in the parent
  proposal (552e2db3) the rule `both arms inside +/-0.0057` fires: **close matrix_lr at 2x scale as
  FLAT; do not spend a third slot.**
- **Power caveat (important):** this bracket could only have detected a >0.006 effect. FLAT here means
  "no effect larger than noise at 2x spacing", **not** "0.04 is optimal". The log-midpoint (0.028)
  is unmeasured and would need a >0.006 predicted effect to be worth a slot.

## Training Dynamics

- Steps: **956** (identical to champion — step-neutral by construction), tokens: 125.3M
- tok/s: 411K average (410.5-412.4K in the final 10%), MFU 7.88%, peak VRAM 18,479 MB
- Wall 381.7s (300.1s training + compile/startup/eval)
- Loss at 80% of run (step 764): 3.138619 -> final mean (last 40 steps): 3.064156
- **Final-20% loss drop = 0.074463 = 2.372% of the 80% level, 1.21% of the full-run loss range**
  (seed-42 lo arm: 0.068524 / 1.11%; champion calibration on seed 43: 0.062987 / 1.0%).
  Still >1% of range -> the run remains **undertrained** at 956 steps, consistent with the
  throughput team's standing thesis. This metric's run-to-run spread (0.063-0.074 across three runs
  of near-identical code) is now ~0.011, i.e. it is noisier than val_bpb itself — do not make
  decisions on single readings of it.
"""

r = requests.put(f"{API}/workspaces/{MAIN_WS_ID}/files/results/exp_gq_matrix_lr_lo_seed43.md",
                 headers=HEADERS, json={"content": result_md})
print("result file PUT:", r.status_code)

# ---- noise floor ledger append (REQUIRED on every second-seed invocation) ----
nf = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/knowledge/noise_floor_data.md",
                  headers=HEADERS, timeout=30).json()
nf_fm = yaml.safe_load(nf["content"].split("---")[1])
pairs = nf_fm.get("pairs", [])
pairs.append({
    "metric_a": LO42, "metric_b": OUR, "abs_delta": seed_pair,
    "code_hash": "champion exp_tput_batch_2e17 + MATRIX_LR 0.04->0.02 (AR64/w512/DEPTH8/MLP2/TOTAL 2**17/DBS64/compile); same code, seed 42 vs seed 43",
    "gpu_a": 1, "gpu_b": 1,
    "agents": ["ar_20261024_gpu7", AGENT_NAME],
    "date": "2026-10-24",
    "pair_type": "cross-seed ONLY (same GPU, same code)",
    "steps_a": 952, "steps_b": 956,
    "tokens_M_a": 124.9, "tokens_M_b": 125.3,
    "note": "Cleanest pair in the ledger: identical code AND identical GPU, differing only by seed. "
            "Confirms seed-only noise at the 2**17 base is ~0.0025, i.e. of the same order as the "
            "cross-GPU pairs. Directly caused the MATRIX_LR=0.02 arm to be reclassified from "
            "KEEP-UNCONFIRMED to FLAT (2-seed mean delta vs champion = %.6f)." % arm_delta,
    "final20_drop_a": 0.068524, "final20_drop_b": 0.074463,
})
sig = math.sqrt(sum(p["abs_delta"]**2 for p in pairs) / len(pairs) / 2)
nf_fm["pairs"] = pairs; nf_fm["sigma_estimate"] = round(sig, 6)
nf_fm["n_pairs"] = len(pairs); nf_fm["updated_at"] = NOW; nf_fm["updated_by"] = AGENT_NAME
body = nf["content"].split("---", 2)[-1].rstrip()
body += (f"\n- pair 5: {LO42} (GPU 1, seed 42) vs {OUR} (GPU 1, seed 43), |delta| = {seed_pair:.6f} "
         f"— identical MATRIX_LR=0.02 code, SAME GPU, cross-seed only. Cleanest pair in the ledger.\n"
         f"\nPooled same-code sigma across {len(pairs)} pairs = **{sig:.6f}** (2-sigma band ~{2*sig:.4f}).\n")
new = f"---\n{yaml.safe_dump(nf_fm, sort_keys=False)}---{body}"
r = requests.put(f"{API}/workspaces/{MAIN_WS_ID}/files/knowledge/noise_floor_data.md",
                 headers={**HEADERS, "If-Match": str(nf.get("version",0))}, json={"content": new})
print(f"noise ledger PUT: {r.status_code}  n_pairs={len(pairs)} sigma={sig:.6f} 2sigma={2*sig:.6f}")
Path("/tmp/ar_gpu9/sigma.txt").write_text(str(round(sig,6)))
