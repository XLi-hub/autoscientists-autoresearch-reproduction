"""Launch exp_cal_champion_seed43 training on GPU 0, synchronously, writing sentinel state."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FOCUS_ROOT = Path("/root/autodl-tmp/ar_20261024")
AGENT_NAME = "ar_20261024_gpu8"
WS = FOCUS_ROOT / "agents" / AGENT_NAME / "workspace"
REP = WS / "repo"
EXP_ID = "exp_cal_champion_seed43"
GPU_ID = 0

claim = json.loads((WS / "claim_record.json").read_text())
item = claim["item"]
description = (
    "NOISE CALIBRATION (non-promotable). champion/train.py verbatim (exp_tput_batch_2e17, "
    "val_bpb 1.088286, 956 steps, AR64/width512, DEPTH 8, MLP_EXPANSION 2, TOTAL_BATCH_SIZE 2**17, "
    "DEVICE_BATCH_SIZE 64, compile max-autotune-no-cudagraphs); ONLY train.py:459-460 seed 42 -> 43. "
    "Champion ran on GPU 1; this run on GPU 0 (same model RTX 4080 SUPER 32GB)."
)

out = WS / f"train_{EXP_ID}.stdout"
err = WS / f"train_{EXP_ID}.stderr"

sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": EXP_ID, "agent": AGENT_NAME, "item": item, "queue_claimed": True,
    "team": claim["team"], "team_ws_id": claim["team_ws_id"],
    "direction": "minimize", "val_score": None,
    "calibration": True, "promotable": False,
    "train_path": str(REP / f"train_{EXP_ID}.py"),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None, "description": description,
    "launched_at": datetime.now(timezone.utc).isoformat(),
    "gpu_device": GPU_ID, "champion_gpu_device": 1,
}
(WS / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))

env = {**os.environ,
       "CUDA_VISIBLE_DEVICES": str(GPU_ID),
       "HF_HOME": "/root/autodl-tmp/cache/huggingface",
       "HF_HUB_OFFLINE": "1",
       "PYTHONUNBUFFERED": "1"}
print(f"[launch] {EXP_ID} on CUDA_VISIBLE_DEVICES={GPU_ID}, cwd={REP}", flush=True)
with out.open("w") as fo, err.open("w") as fe:
    proc = subprocess.run([sys.executable, "train.py"], cwd=str(REP), stdout=fo, stderr=fe,
                          text=True, timeout=1800, env=env)
    rc = proc.returncode

sentinel["status"] = "complete" if rc == 0 else "failed"
sentinel["returncode"] = rc
sentinel["finished_at"] = datetime.now(timezone.utc).isoformat()
(WS / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
print(f"[done] returncode={rc} stdout={out} ({out.stat().st_size} bytes) stderr={err} ({err.stat().st_size} bytes)")
