import json, os, subprocess
from pathlib import Path
from datetime import datetime, timezone

AGENT_NAME = "ar_20261022hi_gpu5"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
ws  = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace")
rep = ws / "repo"
c = json.load(open("/tmp/claim_state.json")); EXP_ID = c["exp_id"]; item = c["item"]
out, err = ws / f"train_{EXP_ID}.stdout", ws / f"train_{EXP_ID}.stderr"
description = ("MLP activation ReLU^2 -> SiLU^2 (square preserved; single-property swap). "
               "Zero params, zero FLOPs, step-neutral per-step representational probe on champion exp_batch_2e17.")

sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": EXP_ID, "agent": AGENT_NAME, "item": item, "queue_claimed": True,
    "direction": "minimize", "val_score": None, "submission_path": None,
    "train_path": str(rep / f"train_{EXP_ID}.py"),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None, "description": description,
    "diff_applied": True,
    "launched_at": datetime.now(timezone.utc).isoformat(),
}
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
print("[SENTINEL] running written", flush=True)

env = {**os.environ, "CUDA_VISIBLE_DEVICES": "0",
       "HF_HOME": f"{FOCUS_ROOT}/.cache/huggingface", "HF_HUB_OFFLINE": "1",
       "TORCH_HOME": f"{FOCUS_ROOT}/.cache/torch"}
t0 = datetime.now(timezone.utc)
result = subprocess.run(["/root/autodl-tmp/envs/ar/bin/python3", "train.py"],
                        cwd=str(rep), capture_output=True, text=True, timeout=1200, env=env)
out.write_text(result.stdout or ""); err.write_text(result.stderr or "")
sentinel["status"] = "complete" if result.returncode == 0 else "failed"
sentinel["returncode"] = result.returncode
sentinel["finished_at"] = datetime.now(timezone.utc).isoformat()
sentinel["wall_sec"] = (datetime.now(timezone.utc)-t0).total_seconds()
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
print(f"[TRAIN] returncode={result.returncode} wall={sentinel['wall_sec']:.0f}s")
print("=== STDOUT TAIL ===")
print("\n".join((result.stdout or "").splitlines()[-22:]))
print("=== STDERR TAIL ===")
print("\n".join((result.stderr or "").splitlines()[-12:]))
