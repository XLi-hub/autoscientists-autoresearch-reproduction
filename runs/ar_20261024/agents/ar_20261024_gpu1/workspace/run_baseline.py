import json, os, subprocess, sys, re
from pathlib import Path
from datetime import datetime, timezone

FOCUS = "/root/autodl-tmp/ar_20261024"
AGENT = "ar_20261024_gpu1"
ws = Path(f"{FOCUS}/agents/{AGENT}/workspace")
rep = ws / "repo"
exp_id = "baseline_shared_hw"
out, err = ws / f"train_{exp_id}.stdout", ws / f"train_{exp_id}.stderr"

item = {"id": exp_id, "axis": "seed", "direction": "none", "value": 0,
        "diff": "Shared baseline: pristine upstream train.py with DEVICE_BATCH_SIZE 128->64 (128 OOMs on 32GB; TOTAL_BATCH_SIZE 2**19 unchanged, grad_accum 2->4)",
        "infrastructure_probe": True, "diff_applied": True,
        "hardware_adaptation": "DEVICE_BATCH_SIZE 128->64 only"}

sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": exp_id, "agent": AGENT, "item": item, "queue_claimed": False,
    "direction": "minimize", "val_score": None,
    "submission_path": None,
    "train_path": str(rep / f"train_{exp_id}.py"),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None,
    "description": item["diff"],
    "launched_at": datetime.now(timezone.utc).isoformat(),
}
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))

env = {**os.environ,
       "CUDA_VISIBLE_DEVICES": "0",
       "HF_HOME": "/root/autodl-tmp/cache/huggingface",
       "HF_HUB_OFFLINE": "1",
       "TORCH_HOME": f"{FOCUS}/.cache/torch",
       "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"}
print("[runner] launching training...", flush=True)
result = subprocess.run(["python", "train.py"], cwd=str(rep), capture_output=True,
                        text=True, timeout=1100, env=env)
out.write_text(result.stdout)
err.write_text(result.stderr)
print(f"[runner] returncode={result.returncode}", flush=True)
m = re.search(r"val_bpb:\s+([0-9.]+)", result.stdout)
val = float(m.group(1)) if m else None
sentinel["status"] = "complete" if result.returncode == 0 else "failed"
sentinel["returncode"] = result.returncode
sentinel["val_score"] = val
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
print(f"[runner] val_bpb={val}", flush=True)
print(result.stdout[-3000:], flush=True)
print("STDERR_TAIL:", result.stderr[-1500:], flush=True)
