"""Run one training experiment for ar_20261022hi_gpu1 (blocking subprocess runner).

Usage: python3 run_exp.py <exp_id> <description> [--seed N]
Writes sentinel to workspace/result_latest.json before launch and after finish.
"""
import json, os, re, shutil, subprocess, sys, time
from pathlib import Path
from datetime import datetime, timezone

AGENT_NAME = "ar_20261022hi_gpu1"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
WS = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace")
REP = WS / "repo"

exp_id = sys.argv[1]
description = sys.argv[2] if len(sys.argv) > 2 else exp_id

out = WS / f"train_{exp_id}.stdout"
err = WS / f"train_{exp_id}.stderr"

item = json.loads(os.environ.get("ITEM_JSON", "{}") or "{}")

sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": exp_id, "agent": AGENT_NAME, "item": item,
    "diff_applied": bool(item.get("diff_applied", True)),
    "direction": "minimize", "val_score": None,
    "submission_path": str(REP / f"submission_{exp_id}.csv"),
    "train_path": str(REP / f"train_{exp_id}.py"),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None,
    "description": description,
    "launched_at": datetime.now(timezone.utc).isoformat(),
}
(WS / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
print(f"[RUN] {exp_id} starting at {sentinel['launched_at']}", flush=True)

env = {**os.environ,
       "CUDA_VISIBLE_DEVICES": "0",
       "UV_CACHE_DIR": f"{FOCUS_ROOT}/.cache/uv",
       "HF_HOME": f"{FOCUS_ROOT}/.cache/huggingface",
       "HF_HUB_ENDPOINT": "https://hf-mirror.com",
       "HF_ENDPOINT": "https://hf-mirror.com",
       "TORCH_HOME": f"{FOCUS_ROOT}/.cache/torch"}

PYTHON = "/root/autodl-tmp/envs/ar/bin/python3"  # pre-provisioned env (torch 2.9.1+cu128, kernels, etc.)
t0 = time.time()
result = subprocess.run([PYTHON, "train.py"], cwd=str(REP),
                        capture_output=True, text=True, timeout=1800, env=env)
elapsed = time.time() - t0
out.write_text(result.stdout)
err.write_text(result.stderr)
print(f"[RUN] exit={result.returncode} elapsed={elapsed:.0f}s", flush=True)

val = None
m = re.search(r"val_bpb:\s*([0-9.]+)", result.stdout)
if m:
    val = float(m.group(1))
num_steps = None
m2 = re.search(r"num_steps:\s*(\d+)", result.stdout)
if m2:
    num_steps = int(m2.group(1))

sentinel.update({
    "status": "complete" if result.returncode == 0 else "failed",
    "returncode": result.returncode,
    "val_score": val,
    "num_steps": num_steps,
    "elapsed_sec": round(elapsed, 1),
    "completed_at": datetime.now(timezone.utc).isoformat(),
})
(WS / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
print(f"[RUN] val_bpb={val} num_steps={num_steps}", flush=True)
print("[RUN] --- stdout tail ---")
print("\n".join(result.stdout.splitlines()[-25:]), flush=True)
print("[RUN] --- stderr tail ---")
print("\n".join(result.stderr.splitlines()[-15:]), flush=True)
