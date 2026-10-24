import json, os, shutil, subprocess, sys, filecmp
from datetime import datetime, timezone
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu7"
EXP_ID = "exp_gq_matrix_lr_hi"
ws = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace")
rep = ws / "repo"

# Step 4 guard: verify the diff actually landed
diff_applied = not filecmp.cmp(str(rep / "train.py"), f"{FOCUS_ROOT}/champion/train.py", shallow=False)
print("[STEP4] diff_applied =", diff_applied)
if not diff_applied:
    print("[STEP4] FAILED — train.py identical to champion, not launching training")
    sys.exit(2)

# Stamp train script before training
stamped = rep / f"train_{EXP_ID}.py"
shutil.copy(rep / "train.py", stamped)
print("[ISOLATION] stamped →", stamped)

item = {
    "id": EXP_ID, "priority": "high", "bold_bet": True,
    "diff": "MATRIX_LR = 0.08        # was 0.04",
    "proposed_by": "ar_20261024_analyst1",
    "proposal_post": "552e2db3-5221-498b-a61e-83f155016948",
    "axis": "matrix_lr", "direction": "increase", "value": 0.08, "current_value": 0.04,
    "bracket": "matrix_lr_3pt_high", "discussion_pending": False,
    "expected_delta": "-0.010 to +0.050",
    "noise_gate": "second seed if |delta|<0.006; hold the verdict until exp_cal_champion_seed43 returns",
    "diff_applied": diff_applied,
}
description = ("MATRIX_LR 0.04 -> 0.08 (Muon LR for all 8 blocks' matrix weights, 40.0% of params / "
               "80.0% of 6N FLOP-relevant count; n=0 cold axis). Champions base: exp_tput_batch_2e17 "
               "(val_bpb 1.088286, AR64/width512, DEPTH 8, MLP_EXPANSION 2, TOTAL_BATCH_SIZE 2**17, "
               "DEVICE_BATCH_SIZE 64, compile max-autotune-no-cudagraphs). Confound: lr*wd coupling "
               "doubles effective decay 0.8%->1.6%/step.")

out, err = ws / f"train_{EXP_ID}.stdout", ws / f"train_{EXP_ID}.stderr"
sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": EXP_ID, "agent": AGENT_NAME, "item": item, "queue_claimed": True,
    "direction": "increase", "val_score": None,
    "submission_path": str(rep / f"submission_{EXP_ID}.csv"),
    "train_path": str(stamped),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None, "description": description,
    "launched_at": datetime.now(timezone.utc).isoformat(),
    "diff_applied": diff_applied,
}
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))

env = {**os.environ,
       "CUDA_VISIBLE_DEVICES": "1",
       "HF_HOME": "/root/autodl-tmp/cache/huggingface",
       "HF_HUB_OFFLINE": "1",
       "TORCH_HOME": f"{FOCUS_ROOT}/.cache/torch"}
print("[TRAIN] launching python train.py at", datetime.now(timezone.utc).isoformat(), flush=True)
t0 = datetime.now(timezone.utc)
with open(out, "w") as fo, open(err, "w") as fe:
    proc = subprocess.run([sys.executable, "train.py"], cwd=str(rep), stdout=fo,
                          stderr=fe, timeout=1200, env=env)
elapsed = (datetime.now(timezone.utc) - t0).total_seconds()
print(f"[TRAIN] returncode={proc.returncode} wall={elapsed:.1f}s", flush=True)

sentinel["status"] = "complete" if proc.returncode == 0 else "failed"
sentinel["returncode"] = proc.returncode
sentinel["wall_seconds"] = elapsed
sentinel["finished_at"] = datetime.now(timezone.utc).isoformat()
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))

# quick metric echo
import re
log = out.read_text(errors="ignore")
m = re.findall(r"val_bpb:\s+([0-9.]+)", log)
s = re.findall(r"num_steps:\s+(\d+)", log)
print("[PARSE] val_bpb =", m, "num_steps =", s)
print("[PARSE] tail:", log[-600:])
