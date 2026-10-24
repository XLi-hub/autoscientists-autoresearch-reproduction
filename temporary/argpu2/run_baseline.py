import json, os, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu2"
ws = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace")
rep = ws / "repo"
exp_id = "baseline_shared"

item = {
    "id": exp_id, "axis": "seed", "direction": "none", "value": 0,
    "diff": "Run champion train.py unchanged (shared baseline)",
    "infrastructure_probe": True,
}

out, err = ws / f"train_{exp_id}.stdout", ws / f"train_{exp_id}.stderr"
sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": exp_id, "agent": AGENT_NAME, "item": item, "queue_claimed": False,
    "direction": "minimize", "val_score": None,
    "train_path": str(rep / f"train_{exp_id}.py"),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None,
    "description": "Shared baseline: pristine champion/train.py, unchanged",
    "launched_at": datetime.now(timezone.utc).isoformat(),
}
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))

env = {**os.environ,
       "CUDA_VISIBLE_DEVICES": "1",
       "HF_HOME": "/root/autodl-tmp/cache/huggingface",
       "HF_HUB_OFFLINE": "1",
       "TORCH_HOME": "/root/autodl-tmp/ar_20261024/.cache/torch",
       "UV_CACHE_DIR": "/root/autodl-tmp/ar_20261024/.cache/uv",
       "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"}
print("[RUN] launching baseline training...", flush=True)
t0 = datetime.now(timezone.utc)
try:
    result = subprocess.run([sys.executable, "train.py"], cwd=str(rep),
                            capture_output=True, text=True, timeout=1200, env=env)
    rc = result.returncode
    out.write_text(result.stdout or "")
    err.write_text(result.stderr or "")
except subprocess.TimeoutExpired as e:
    rc = -1
    out.write_text((e.stdout or "") if isinstance(e.stdout, str) else "")
    err.write_text(((e.stderr or "") if isinstance(e.stderr, str) else "") + "\nTIMEOUT 1200s")
    print("[RUN] TIMEOUT", flush=True)

t1 = datetime.now(timezone.utc)
log = out.read_text(errors="ignore")
m = re.search(r"val_bpb:\s+([0-9.]+)", log)
val = float(m.group(1)) if m else None
print(f"[RUN] returncode={rc} val_bpb={val} elapsed={(t1-t0).total_seconds():.0f}s", flush=True)
print("---- tail stdout ----")
print("\n".join(log.strip().splitlines()[-25:]))
print("---- tail stderr ----")
print("\n".join(err.read_text(errors="ignore").strip().splitlines()[-15:]))

sentinel["status"] = "complete" if rc == 0 else "failed"
sentinel["returncode"] = rc
sentinel["val_score"] = val
sentinel["finished_at"] = t1.isoformat()
sentinel["elapsed_sec"] = (t1-t0).total_seconds()
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
