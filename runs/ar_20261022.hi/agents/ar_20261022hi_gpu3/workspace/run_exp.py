"""Run one experiment synchronously and record its sentinel.

Usage: python3 run_exp.py <exp_id> <description_json_or_plain>
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_gpu3"
WS = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace")
REP = WS / "repo"
PY = "/root/autodl-tmp/envs/ar/bin/python3"
GPU_ID = "1"

exp_id = sys.argv[1]
description = sys.argv[2]

out = WS / f"train_{exp_id}.stdout"
err = WS / f"train_{exp_id}.stderr"
sentinel_path = WS / "result_latest.json"

item = json.loads(os.environ.get("ITEM_JSON", "{}"))

sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": exp_id, "agent": AGENT_NAME, "item": item, "queue_claimed": True,
    "direction": "minimize", "val_score": None,
    "submission_path": None,
    "train_path": str(REP / f"train_{exp_id}.py"),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None, "description": description,
    "launched_at": datetime.now(timezone.utc).isoformat(),
}
sentinel_path.write_text(json.dumps(sentinel, indent=2, default=str))

env = {
    **os.environ,
    "CUDA_VISIBLE_DEVICES": GPU_ID,
    "HF_HOME": f"{FOCUS_ROOT}/.cache/huggingface",
    "HF_HUB_OFFLINE": "1",
    "TORCH_HOME": f"{FOCUS_ROOT}/.cache/torch",
    "PYTHONUNBUFFERED": "1",
}

t0 = datetime.now(timezone.utc)
result = subprocess.run(
    [PY, "train.py"],
    cwd=str(REP),
    capture_output=True,
    text=True,
    timeout=900,
    env=env,
)
out.write_text(result.stdout or "")
err.write_text(result.stderr or "")
elapsed = (datetime.now(timezone.utc) - t0).total_seconds()

sentinel["status"] = "complete" if result.returncode == 0 else "failed"
sentinel["returncode"] = result.returncode
sentinel["wall_seconds"] = round(elapsed, 1)
sentinel_path.write_text(json.dumps(sentinel, indent=2, default=str))
print(f"[RUN] {exp_id} rc={result.returncode} wall={elapsed:.0f}s stdout={len(result.stdout or '')}B stderr={len(result.stderr or '')}B")
print("---- TAIL ----")
print((result.stdout or "")[-1500:])
if result.returncode != 0:
    print("---- STDERR TAIL ----")
    print((result.stderr or "")[-3000:])
