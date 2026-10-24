import json, os, subprocess, sys, re
from pathlib import Path
from datetime import datetime, timezone

FOCUS = "/root/autodl-tmp/ar_20261024"
AGENT = "ar_20261024_gpu4"
GPU = "1"
exp_id = sys.argv[1]
item = json.loads(Path(sys.argv[2]).read_text())

ws = Path(f"{FOCUS}/agents/{AGENT}/workspace")
rep = ws / "repo"
out, err = ws / f"train_{exp_id}.stdout", ws / f"train_{exp_id}.stderr"

sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": exp_id, "agent": AGENT, "item": item, "queue_claimed": True,
    "direction": "minimize", "val_score": None,
    "submission_path": None,
    "train_path": str(rep / f"train_{exp_id}.py"),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None,
    "description": item.get("diff", exp_id),
    "diff_applied": True,
    "launched_at": datetime.now(timezone.utc).isoformat(),
}
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))

env = {**os.environ,
       "CUDA_VISIBLE_DEVICES": GPU,
       "HF_HOME": "/root/autodl-tmp/cache/huggingface",
       "HF_HUB_OFFLINE": "1",
       "TORCH_HOME": f"{FOCUS}/.cache/torch",
       "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"}
print(f"[runner] launching {exp_id} on GPU {GPU} ...", flush=True)
result = subprocess.run(["python", "train.py"], cwd=str(rep), capture_output=True,
                        text=True, timeout=1500, env=env)
out.write_text(result.stdout)
err.write_text(result.stderr)
m = re.search(r"val_bpb:\s+([0-9.]+)", result.stdout)
val = float(m.group(1)) if m else None
sentinel["status"] = "complete" if (result.returncode == 0 and val is not None) else "failed"
sentinel["returncode"] = result.returncode
sentinel["val_score"] = val
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
print(f"[runner] returncode={result.returncode} val_bpb={val}", flush=True)
print(result.stdout[-2500:], flush=True)
if result.returncode != 0:
    print("STDERR_TAIL:", result.stderr[-3000:], flush=True)
