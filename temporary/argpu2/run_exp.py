import json, os, re, subprocess, sys, filecmp
from datetime import datetime, timezone
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu2"
exp_id = sys.argv[1]
desc = sys.argv[2]
item_json = sys.argv[3] if len(sys.argv) > 3 else "{}"
item = json.loads(item_json)

ws = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace"); rep = ws / "repo"
champ = Path(f"{FOCUS_ROOT}/champion/train.py")
diff_applied = not filecmp.cmp(str(rep / "train.py"), str(champ), shallow=False)
item["diff_applied"] = diff_applied
print(f"[STEP4] diff_applied={diff_applied}")
if not diff_applied:
    print("[STEP4] DIFF NOT APPLIED — aborting training"); sys.exit(3)

out, err = ws / f"train_{exp_id}.stdout", ws / f"train_{exp_id}.stderr"
sentinel = {
    "status": "running", "posted_to_workshop": False, "exp_id": exp_id, "agent": AGENT_NAME,
    "item": item, "queue_claimed": True, "direction": "minimize", "val_score": None,
    "train_path": str(rep / f"train_{exp_id}.py"),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None, "description": desc, "diff_applied": diff_applied,
    "launched_at": datetime.now(timezone.utc).isoformat(),
}
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))

env = {**os.environ, "CUDA_VISIBLE_DEVICES": "1",
       "HF_HOME": "/root/autodl-tmp/cache/huggingface", "HF_HUB_OFFLINE": "1",
       "TORCH_HOME": f"{FOCUS_ROOT}/.cache/torch", "UV_CACHE_DIR": f"{FOCUS_ROOT}/.cache/uv",
       "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"}
t0 = datetime.now(timezone.utc)
print("[RUN] launching", exp_id, flush=True)
try:
    result = subprocess.run([sys.executable, "train.py"], cwd=str(rep), capture_output=True,
                            text=True, timeout=1200, env=env)
    rc = result.returncode
    out.write_text(result.stdout or ""); err.write_text(result.stderr or "")
except subprocess.TimeoutExpired as e:
    rc = -1
    out.write_text((e.stdout or "") if isinstance(e.stdout, str) else "")
    err.write_text(((e.stderr or "") if isinstance(e.stderr, str) else "") + "\nTIMEOUT 1200s")
t1 = datetime.now(timezone.utc)
log = out.read_text(errors="ignore")
m = re.search(r"val_bpb:\s+([0-9.]+)", log)
val = float(m.group(1)) if m else None
print(f"[RUN] returncode={rc} val_bpb={val} elapsed={(t1-t0).total_seconds():.0f}s")
print("\n".join(log.strip().splitlines()[-16:]))
print("---- stderr tail ----")
print("\n".join(err.read_text(errors="ignore").strip().splitlines()[-10:]))
sentinel.update({"status": "complete" if rc == 0 else "failed", "returncode": rc,
                 "val_score": val, "finished_at": t1.isoformat(),
                 "elapsed_sec": (t1-t0).total_seconds()})
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
