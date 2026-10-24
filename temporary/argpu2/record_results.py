import json, requests, yaml
from datetime import datetime, timezone
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu2"
TEAM_WS_ID = "005cb9ec-6fce-4bba-9340-21c08ab914c5"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
NOW = datetime.now(timezone.utc).isoformat()
def pf(resp):
    c=resp.get("content",""); p=c.split("---")
    return yaml.safe_load(p[1]) if len(p)>=3 else {}

# ---------- 1. queue: release claim + move to completed ----------
q = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=H).json()
fm = pf(q); pending = fm.get("pending") or []; completed = fm.get("completed") or []
removed_claim = fm.get("claims", {}).pop(AGENT_NAME, None) is not None
remaining=[]; moved=False
for it in pending:
    if it.get("id") == "exp_gq_muon_mom_098":
        it = dict(it); it.update({
            "completed_at": datetime.now(timezone.utc).isoformat(), "completed_by": AGENT_NAME,
            "outcome": "DISCARD", "val_score": 1.192527,
            "val_score_seed43": 1.188308, "champion_at_completion": 1.158107,
            "note": "run on old base (TOTAL_BATCH 2**19); paired seed-42 effect +0.00018 (below noise); confounded by base change"})
        completed.append(it); moved=True
    else: remaining.append(it)
fm["pending"]=remaining; fm["completed"]=completed
body = q.get("content","").split("---",2)[-1]
new = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}"
assert yaml.safe_load(new.split("---")[1]) == fm
r = requests.put(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md",
                 headers={**H, "If-Match": str(q.get("version",0))}, json={"content": new})
print("queue PUT", r.status_code, "claim_removed", removed_claim, "moved", moved)

# ---------- 2. results/exp_gq_muon_mom_098.md ----------
md = f"""# exp_gq_muon_mom_098 — Muon momentum ramp target 0.95 -> 0.98

- metric: **val_bpb = 1.192527** (seed 42) / **1.188308** (seed 43, confirmation)
- outcome: **DISCARD** vs current champion (1.158107)
- agent: {AGENT_NAME} (GPU 1), team: gradient-quality
- timestamp: {NOW}
- axis: muon_momentum | direction: increase | value: 0.98 (current 0.95)
- base on which tested: champion at run time = TOTAL_BATCH_SIZE 2**19, MLP_EXPANSION 4, DEVICE_BATCH_SIZE 64

## Change
```python
def get_muon_momentum(step):
    frac = min(step / 300, 1)
    return (1 - frac) * 0.85 + frac * 0.98   # was 0.95
```

## Result and interpretation
| run | seed | val_bpb | steps |
|---|---|---|---|
| baseline_shared (no change) | 42 | 1.192708 | 196 |
| this experiment | 42 | 1.192527 | 196 |
| this experiment | 43 | 1.188308 | 196 |

- Paired seed-42 treatment effect: **+0.000181** (improvement), which is 16x smaller than the
  team's measured same-code noise (|delta| ~ 0.0042 between seeds 42/43 on THIS code).
- The seed-43 draw is 0.0042 better than the seed-42 draw of the identical code. That is a seed
  effect, not a momentum effect. It is the same magnitude as gpu1's GPU-to-GPU repeat delta (0.0030).
- **Verdict: no measurable effect.** Do not promote.
- Important caveat: on this base only ~196 optimizer steps fit in 300 s, so `frac = step/300`
  reaches only 0.65 and terminal momentum reached 0.9349 instead of 0.98. On the CURRENT
  champion base (TOTAL_BATCH 2**18 -> ~374-410 steps) the ramp saturates at step 300, so the
  full 0.98 is actually reached. A retest on the new base would test a strictly different
  regime than this run did; this result does not refute it there.

## Training Dynamics
- 196 optimizer steps in 301.1s, 102.8M tokens, ~322K tok/s, MFU 7.83%, peak VRAM 22.8GB.
- Loss 9.01 -> 3.358; final-20% drop 0.122 (2.2% of range) — still decreasing, undertrained signal.
- No early plateau.
"""
print("result md PUT", requests.put(f"{API}/workspaces/{MAIN}/files/results/exp_gq_muon_mom_098.md",
      headers=H, json={"content": md}).status_code)

# ---------- 3. results/exp_baseline_seed43.md (noise probe) ----------
probe = f"""# exp_baseline_seed43 — same-code seed repeat of exp_tput_batch_2e18 (noise probe)

- metric: **val_bpb = 1.164542** (seed 43)
- agent: {AGENT_NAME} (GPU 1), self-designed infrastructure probe (noise-floor calibration)
- timestamp: {NOW}
- code: exactly champion/train.py at launch time = exp_tput_batch_2e18
  (TOTAL_BATCH_SIZE 2**18, DEVICE_BATCH_SIZE 64, MLP_EXPANSION 4, seed 42 changed to 43 only)

## Why this run exists
After `exp_gq_muon_mom_098` produced seeds {1.192527, 1.188308} on identical code, the seed
swing (0.0042) was far larger than the treatment delta (0.00018). A paired control was needed
to separate seed noise from treatment effect.

## Result
| code | seed 42 | seed 43 | |delta| |
|---|---|---|---|
| exp_tput_batch_2e18 (champion at launch, 2**18) | 1.169258 (gpu1, GPU 0) | **1.164542** (this run, GPU 1) | **0.004716** |
| momentum 0.98 on 2**19 base | 1.192527 | 1.188308 | 0.004219 |
| pristine baseline (identical code AND seed, GPU0 vs GPU1) | 1.192708 / 1.195744 | — | 0.003036 |

Three independent repeat measurements cluster at **|delta| ~ 0.003-0.005**.
Pooled same-code sigma across the 3 pairs: **sigma ~= 0.00287** (2-sigma band ~0.0057).

## Implication for the promotion gate
Any experiment with |delta| < ~0.006 must be treated as unconfirmed on a single seed.
gpu1's KEEPs (deltas 0.023 and 0.011) clear this band comfortably.

## Dynamics
- 379 optimizer steps in 300.6s, 99.4M tokens, ~320K tok/s, MFU 7.77%, peak VRAM 22.8GB.
- Loss 9.01 -> 3.267; still decreasing.
"""
print("probe md PUT", requests.put(f"{API}/workspaces/{MAIN}/files/results/exp_baseline_seed43.md",
      headers=H, json={"content": probe}).status_code)
