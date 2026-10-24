"""Synchronous training driver for exp_cap_head_dim_64.

Blocks on subprocess.run until training exits, capturing stdout/stderr to
agent-local files and maintaining result_latest.json (HEARTBEAT Part 0 Check C).
"""
import json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu6"
EXP_ID = "exp_cap_head_dim_64"

ws = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace")
rep = ws / "repo"
out = ws / f"train_{EXP_ID}.stdout"
err = ws / f"train_{EXP_ID}.stderr"

item = {
    "id": EXP_ID,
    "axis": "head_dim",
    "direction": "decrease",
    "value": 64,
    "current_value": 128,
    "diff": "HEAD_DIM = 64 (was 128); width 512 -> n_head 4->8, head_dim 128->64. Zero param/FLOP change, step-neutral structural probe.",
    "proposed_by": "ar_20261024_analyst3",
    "proposal_post": "5049d7ae-1890-4c73-a5d7-b16968accdc0",
    "base": "exp_tput_batch_2e17",
    "diff_applied": True,
}
description = ("HEAD_DIM 128 -> 64 at DEPTH 8 / ASPECT_RATIO 64: model_dim stays 512, "
               "n_head 4 -> 8, head_dim 128 -> 64. Attention FLOPs and params unchanged "
               "(only +512 ve_gate scalars). Step-neutral representational-structure probe "
               "on champion exp_tput_batch_2e17 (val_bpb 1.088286).")

sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": EXP_ID, "agent": AGENT_NAME, "item": item, "queue_claimed": True,
    "direction": "minimize", "val_score": None,
    "submission_path": None,
    "train_path": str(rep / f"train_{EXP_ID}.py"),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None, "description": description,
    "diff_applied": True,
    "launched_at": datetime.now(timezone.utc).isoformat(),
}
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))

env = {**os.environ,
       "CUDA_VISIBLE_DEVICES": "1",
       "HF_HOME": "/root/autodl-tmp/cache/huggingface",
       "HF_HUB_OFFLINE": "1",
       "TORCH_HOME": "/root/autodl-tmp/cache/torch",
       "UV_CACHE_DIR": f"{FOCUS_ROOT}/.cache/uv"}

t0 = time.time()
try:
    result = subprocess.run(
        ["python", "train.py"],
        cwd=str(rep), capture_output=True, text=True, timeout=1200, env=env,
    )
    rc = result.returncode
    so, se = result.stdout, result.stderr
except subprocess.TimeoutExpired as e:
    rc = -9
    so = (e.stdout or b"").decode(errors="ignore") if isinstance(e.stdout, bytes) else (e.stdout or "")
    se = (e.stderr or b"").decode(errors="ignore") if isinstance(e.stderr, bytes) else (e.stderr or "")
    se += "\n[DRIVER] TIMEOUT after 1200s\n"

out.write_text(so)
err.write_text(se)
sentinel["returncode"] = rc
sentinel["status"] = "complete" if rc == 0 else "failed"
sentinel["wall_seconds"] = round(time.time() - t0, 1)
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
print(f"[DRIVER] done rc={rc} wall={sentinel['wall_seconds']}s stdout={len(so)}B stderr={len(se)}B")
sys.exit(0 if rc == 0 else 1)
