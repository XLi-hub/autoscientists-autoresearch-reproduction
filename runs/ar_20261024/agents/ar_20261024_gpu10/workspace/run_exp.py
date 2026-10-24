"""Blocking runner for one experiment (HEARTBEAT ROLE-GPU Pattern B).

Launches train.py as a subprocess in the repo dir, captures stdout/stderr,
and maintains the result_latest.json sentinel. Blocks until training exits.
"""
import json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu10"
EXP_ID = sys.argv[1]
GPU_ID = sys.argv[2] if len(sys.argv) > 2 else "0"

ws = Path(FOCUS_ROOT) / "agents" / AGENT_NAME / "workspace"
rep = ws / "repo"
out = ws / f"train_{EXP_ID}.stdout"
err = ws / f"train_{EXP_ID}.stderr"
sent_path = ws / "result_latest.json"

item = json.loads((ws / "item.json").read_text())

sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": EXP_ID, "agent": AGENT_NAME, "item": item, "queue_claimed": True,
    "direction": "minimize", "val_score": None,
    "submission_path": None,
    "train_path": str(rep / f"train_{EXP_ID}.py"),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None,
    "description": item.get("diff", ""),
    "diff_applied": True,
    "team": "capacity",
    "launched_at": datetime.now(timezone.utc).isoformat(),
}
sent_path.write_text(json.dumps(sentinel, indent=2, default=str))

env = {**os.environ,
       "CUDA_VISIBLE_DEVICES": str(GPU_ID),
       "HF_HOME": "/root/autodl-tmp/cache/huggingface",
       "HF_HUB_OFFLINE": "1",
       "TORCH_HOME": "/root/autodl-tmp/cache/torch",
       "UV_CACHE_DIR": "/root/autodl-tmp/.cache/uv"}

t0 = datetime.now(timezone.utc)
try:
    result = subprocess.run([sys.executable, "train.py"], cwd=str(rep),
                            capture_output=True, text=True, timeout=2400, env=env)
    out.write_text(result.stdout)
    err.write_text(result.stderr)
    rc = result.returncode
except subprocess.TimeoutExpired as e:
    out.write_text(e.stdout or "")
    err.write_text((e.stderr or "") + "\nTIMEOUT after 2400s")
    rc = -9

sentinel["status"] = "complete" if rc == 0 else "failed"
sentinel["returncode"] = rc
sentinel["finished_at"] = datetime.now(timezone.utc).isoformat()
sentinel["wall_seconds"] = (datetime.now(timezone.utc) - t0).total_seconds()
sent_path.write_text(json.dumps(sentinel, indent=2, default=str))
print(f"DONE exp={EXP_ID} rc={rc} wall={sentinel['wall_seconds']:.1f}s")
print(f"stdout={out} stderr={err}")
