import json, requests
from pathlib import Path
from datetime import datetime, timezone
AGENT_NAME="ar_20261022hi_gpu4"; FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"
AGENT_DIR=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}"); NOW=datetime.now(timezone.utc).isoformat()
creds=json.load(open(AGENT_DIR/"credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
sc=AGENT_DIR/"memory"/".session_count"; n=int(sc.read_text().strip()) if sc.exists() else 0

agent_content=f"""---
name: {AGENT_NAME}
role: gpu
team: gradient-quality
last_seen: "{NOW}"
session_count: {n+1}
last_branch: "normal"
last_experiment: "exp_muon_beta2_hi"
last_outcome: "DISCARD"
---

# {AGENT_NAME}

Gpu agent. Team: gradient-quality.

## Current Focus
Fixed-time (300 s) nanoGPT val_bpb optimization. Team hypothesis H-gradient-quality:
changes that reduce gradient noise or improve update direction will KEEP.

## Notes for Next Session
- Champion v5 is exp_batch_2e17: TOTAL_BATCH_SIZE=2**17, 719 steps, val_bpb=1.094037.
- This cycle ran two step-neutral probes, both ties:
  exp_embedding_lr_hi (1.096777, +0.00274 = 0.91 sigma) and
  exp_muon_beta2_hi (1.094608, +0.00057 = 0.19 sigma).
- **Measured seed sigma is 0.00302 (analyst2, 16:01 UTC), so the keep-bar is 2-sigma = 0.006.**
  Anything smaller is a tie, not evidence. The old 0.003 "band" was 1 sigma.
- EMA-horizon family is now inert on BOTH optimizers (Adam beta2 0.99: 0.07 sigma;
  NorMuon beta2 0.99: 0.19 sigma). Stop tuning beta2 variants.
- Run training with the pre-provisioned interpreter, not `uv run`:
  `CUDA_VISIBLE_DEVICES=1 /root/autodl-tmp/envs/ar/bin/python3 train.py`
  with HF_HOME={FOCUS_ROOT}/.cache/huggingface and HF_HUB_OFFLINE=1.
- A full run is ~356 s wall clock (300 s train + eval), peak VRAM 22,653 MB at DEVICE_BATCH_SIZE=64.
- Remaining high-priority queue items: adm_eps bracket, muon_ramp_900, adam_beta1 bracket.
  Structural/init changes (tied readout, softcap) look higher-upside than finer EMA tuning.
"""
(AGENT_DIR/"AGENT.md").write_text(agent_content); sc.write_text(str(n+1))

mem=AGENT_DIR/"memory"/"feedback_noise_floor_and_inert_axes.md"
mem.write_text("""---
name: noise_floor_and_inert_axes
description: Measured seed sigma 0.00302 -> 0.006 keep-bar; EMA-horizon axes are inert at 719 steps
type: feedback
---

# Noise floor and inert axes (2026-10-22, cycle 4)

- **Measured per-seed sigma = 0.00302** from two same-code seed pairs
  (exp_warmdown_070: 1.093748/1.097886; exp_adam_beta2_hi: 1.093839/1.098235).
  The old hardcoded 0.003 "conservative band" was therefore 1 sigma, not 2.
  Practical keep-bar: **|delta| > 0.006**.
- **EMA-horizon knobs are inert on both optimizers at 719 steps:**
  AdamW beta2 0.95->0.99 = +0.0002 (0.07 sigma); NorMuon beta2 0.95->0.99 = +0.0006 (0.19 sigma).
  Do not spend slots on finer beta2 brackets.
- **EMBEDDING_LR 0.6->1.2** (effective 0.735->1.47 on 42% of params) = +0.0027 (0.91 sigma),
  and behind champion train loss at every checkpoint (+0.032 @20% narrowing to +0.010 @99%).
  The fast AdamW group is not LR-starved; it is at/past its optimum.
- Only large lever observed in this run remains the batch/step change (2**18->2**17, -0.076).
""")
mi=AGENT_DIR/"memory"/"MEMORY.md"
mi.write_text("""# Memory Index

- [Infra run recipe](infra_run_recipe.md) — use the pre-provisioned python, batch 64, flash-attn cache
- [Noise floor and inert axes](feedback_noise_floor_and_inert_axes.md) — sigma 0.00302 -> keep-bar 0.006; beta2/embedding-LR are ties
""")
r=requests.put(f"{API}/workspaces/{MAIN}/files/agents/{AGENT_NAME}.md",headers=H,json={"content":agent_content})
print("agent.md mirror:",r.status_code,"session_count ->",n+1)
