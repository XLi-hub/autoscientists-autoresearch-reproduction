import json, os, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

AGENT_NAME = "ar_20261024_gpu9"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
EXP = "exp_gq_matrix_lr_lo_seed43"
ws = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace")
rep = ws / "repo"
out, err = ws / f"train_{EXP}.stdout", ws / f"train_{EXP}.stderr"

item = json.loads(Path("/tmp/ar_gpu9/item.json").read_text())
sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": EXP, "agent": AGENT_NAME, "item": item, "queue_claimed": True,
    "direction": "minimize", "val_score": None,
    "submission_path": str(rep / f"submission_{EXP}.csv"),
    "train_path": str(rep / f"train_{EXP}.py"),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None,
    "description": item["diff"],
    "diff_applied": True,
    "launched_at": datetime.now(timezone.utc).isoformat(),
}
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
print("sentinel written, launching...", flush=True)

env = {**os.environ,
       "CUDA_VISIBLE_DEVICES": "1",
       "HF_HOME": "/root/autodl-tmp/cache/huggingface",
       "HF_HUB_OFFLINE": "1",
       "TORCH_HOME": "/root/autodl-tmp/cache/torch"}
t0 = datetime.now(timezone.utc)
with open(out, "w") as fo, open(err, "w") as fe:
    rc = subprocess.run([sys.executable, "train.py"], cwd=str(rep), stdout=fo, stderr=fe, env=env,
                        timeout=1500).returncode
t1 = datetime.now(timezone.utc)
sentinel["status"] = "complete" if rc == 0 else "failed"
sentinel["returncode"] = rc
sentinel["wall_seconds"] = (t1-t0).total_seconds()
sentinel["finished_at"] = t1.isoformat()
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
print(f"TRAINING DONE rc={rc} wall={sentinel['wall_seconds']:.1f}s")
