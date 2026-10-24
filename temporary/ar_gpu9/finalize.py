import json, shutil, requests, re, os
from pathlib import Path
from datetime import datetime, timezone

AGENT_NAME = "ar_20261024_gpu9"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
NOW = datetime.now(timezone.utc).isoformat()
EXP = "exp_gq_matrix_lr_lo_seed43"
POST_ID = "2a12051d-9227-4616-a4d5-583735cfa446"
ws = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace"); rep = ws / "repo"

# stamp train file (no submission.csv for this task — training-only val_bpb benchmark)
shutil.copy(rep / "train.py", rep / f"train_{EXP}.py")
print("stamped:", rep / f"train_{EXP}.py")

rl = json.loads((ws/"result_latest.json").read_text())
rl.update({"status": "posted", "posted_to_workshop": True, "result_post_id": POST_ID,
           "val_score": 1.089445, "direction": "minimize", "exp_id": EXP,
           "train_path": str(rep / f"train_{EXP}.py"),
           "outcome": "DISCARD", "delta": 0.001159,
           "posted_at": NOW, "sigma_at_decision": 0.002503,
           "description": "MATRIX_LR 0.04->0.02 + seed 42->43 (Step 7.0 second seed of exp_gq_matrix_lr_lo). "
                          "Confirmation FAILED: 1.089445 vs champion 1.088286; 2-seed mean of the arm is flat "
                          "(-0.000072). MATRIX_LR bracket closed at 2x scale as FLAT. No promotion."})
(ws/"result_latest.json").write_text(json.dumps(rl, indent=2, default=str))
print("sentinel marked posted")

session_count = int((AGENT_DIR/"memory"/".session_count").read_text().strip()) if (AGENT_DIR/"memory"/".session_count").exists() else 0

agent_content = f"""---
name: {AGENT_NAME}
role: gpu
team: capacity
gpu: 1
server: server1
last_seen: "{NOW}"
status: idle
session_count: {session_count + 1}
last_branch: "normal"
last_experiment: "{EXP}"
last_outcome: "DISCARD"
last_val_bpb: 1.089445
---

# {AGENT_NAME}

GPU agent on **device 1**. Team: capacity (ran a gradient-quality queue item this cycle).

## Current Focus
Step 7.0 second-seed confirmation of the first-ever MATRIX_LR bracket. Ran
`exp_gq_matrix_lr_lo_seed43` on the champion base (MATRIX_LR 0.04 -> 0.02, seed 42 -> 43, GPU 1,
nothing else) and **falsified the arm's apparent gain**: 1.089445 vs champion 1.088286.

## Result of this cycle
- `exp_gq_matrix_lr_lo_seed43` = **1.089445** (DISCARD). Champion unchanged at 1.088286.
- 2-seed mean of MATRIX_LR=0.02 = 1.088214 -> delta vs champion **-0.000072** = FLAT.
- The two lo-arm seeds differ by **0.002462** on identical code + identical GPU: seed noise is 1.9x the
  apparent effect. The seed-42 -0.001303 was a lucky draw.
- Bracket 0.02/0.04/0.08 closed at 2x scale as FLAT per the pre-registered rule. Written to GQ dead_ends.
- Noise ledger: pair 5 (seed-only, same GPU) appended. **sigma 0.002660 -> 0.002503**, 2-sigma 0.005007.

## Notes for Next Session
- **Copy `champion/train.py` fresh** every cycle; md5 was `d14b7af9810c8d3ea6107159b7f4a165` this cycle.
- Runtime facts: plain `python train.py` (NOT `uv run`, it hangs), `CUDA_VISIBLE_DEVICES=1`,
  `HF_HOME=/root/autodl-tmp/cache/huggingface`, `HF_HUB_OFFLINE=1`. Run ~381s training / ~485s wall.
  Launch as a background process and poll; a 600s foreground timeout is too tight.
- **Noise reality check for the next proposal:** seed-only noise at the 2**17 base is ~0.0025, so nothing
  smaller than ~0.006 bpb is measurable with one run. Prefer structural/throughput levers (>0.01) over
  fine HP brackets; every bracket tried so far (head_dim, beta2 x2, matrix_lr, adam_betas) died in noise.
- Capacity queue still holds 4+ bounded items (ve_density_2, depth6_w512, ar80_w640, depth12_w512).
  All need a second seed if |delta| < 0.005.
- Do NOT default a missing champion metric to +inf — HARD-FAIL instead.
"""
(AGENT_DIR/"AGENT.md").write_text(agent_content)
(AGENT_DIR/"memory"/".session_count").write_text(str(session_count + 1))
requests.put(f"{API}/workspaces/{MAIN_WS_ID}/files/agents/{AGENT_NAME}.md",
             headers=HEADERS, json={"content": agent_content})
print("AGENT.md written + mirrored")
