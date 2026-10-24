#!/usr/bin/env python3
"""Synchronous training runner for one experiment. Writes a resumable sentinel."""
import json, os, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

FOCUS = Path("/root/autodl-tmp/ar_20261022.hi")
AGENT = "ar_20261022hi_gpu4"
EXP_ID = sys.argv[1]
GPU_ID = sys.argv[2] if len(sys.argv) > 2 else "1"
DESCRIPTION = sys.argv[3] if len(sys.argv) > 3 else EXP_ID
ITEM_PATH = Path(sys.argv[4]) if len(sys.argv) > 4 else None

ws = FOCUS / "agents" / AGENT / "workspace"
rep = ws / "repo"
item = json.loads(ITEM_PATH.read_text()) if ITEM_PATH and ITEM_PATH.exists() else {"id": EXP_ID}
out = ws / f"train_{EXP_ID}.stdout"
err = ws / f"train_{EXP_ID}.stderr"
rl = ws / "result_latest.json"

sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": EXP_ID, "agent": AGENT, "item": item, "queue_claimed": True,
    "direction": "minimize", "val_score": None,
    "submission_path": str(rep / f"submission_{EXP_ID}.csv"),
    "train_path": str(rep / f"train_{EXP_ID}.py"),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None, "description": DESCRIPTION,
    "launched_at": datetime.now(timezone.utc).isoformat(),
}
rl.write_text(json.dumps(sentinel, indent=2, default=str))

env = {**os.environ,
       "CUDA_VISIBLE_DEVICES": str(GPU_ID),
       "UV_CACHE_DIR": f"{FOCUS}/.cache/uv",
       "HF_HOME": f"{FOCUS}/.cache/huggingface",
       "TORCH_HOME": f"{FOCUS}/.cache/torch"}

# The shared uv cache lock is contended by other agents in this run; the
# pre-provisioned env already pins torch==2.9.1+cu128 and all deps, so run
# train.py directly with it instead of materialising a fresh venv via uv.
PYTHON = os.environ.get("TRAIN_PYTHON", "/root/autodl-tmp/envs/ar/bin/python3")
with open(out, "w") as of, open(err, "w") as ef:
    result = subprocess.run([PYTHON, "train.py"],
                            cwd=str(rep), stdout=of, stderr=ef, text=True,
                            timeout=1800, env=env)

stdout = out.read_text(errors="ignore")
sentinel["status"] = "complete" if result.returncode == 0 else "failed"
sentinel["returncode"] = result.returncode
sentinel["completed_at"] = datetime.now(timezone.utc).isoformat()

m = re.search(r"val_bpb:\s*([0-9.]+)", stdout)
if m:
    sentinel["val_score"] = float(m.group(1))
# metrics block
mt = re.search(r"^\s*val_bpb\s+([0-9.]+)", stdout, re.MULTILINE)
if sentinel["val_score"] is None and mt:
    sentinel["val_score"] = float(mt.group(1))
steps = re.search(r"num_steps:\s*(\d+)", stdout)
toks = re.search(r"total_tokens:\s*([0-9,]+)", stdout)
if steps:
    sentinel["num_steps"] = int(steps.group(1))
if toks:
    sentinel["total_tokens"] = toks.group(1)
rl.write_text(json.dumps(sentinel, indent=2, default=str))
print(json.dumps({k: sentinel.get(k) for k in ("status", "returncode", "val_score", "num_steps")}, indent=1))
