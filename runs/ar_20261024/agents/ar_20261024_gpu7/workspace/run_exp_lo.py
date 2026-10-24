import json, os, shutil, subprocess, sys, filecmp, re
from datetime import datetime, timezone
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu7"
EXP_ID = "exp_gq_matrix_lr_lo"
ws = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace")
rep = ws / "repo"

diff_applied = not filecmp.cmp(str(rep / "train.py"), f"{FOCUS_ROOT}/champion/train.py", shallow=False)
print("[STEP4] diff_applied =", diff_applied)
if not diff_applied:
    print("[STEP4] FAILED — train.py identical to champion"); sys.exit(2)

stamped = rep / f"train_{EXP_ID}.py"
shutil.copy(rep / "train.py", stamped)
print("[ISOLATION] stamped →", stamped)

item = {
    "id": EXP_ID, "priority": "high", "bold_bet": True,
    "diff": "MATRIX_LR = 0.02        # was 0.04",
    "proposed_by": "ar_20261024_analyst1",
    "proposal_post": "552e2db3-5221-498b-a61e-83f155016948",
    "axis": "matrix_lr", "direction": "decrease", "value": 0.02, "current_value": 0.04,
    "bracket": "matrix_lr_3pt_low", "discussion_pending": False,
    "expected_delta": "-0.003 to +0.030 (sign genuinely uncertain)",
    "noise_gate": "second seed if |delta|<0.006; hold the verdict until exp_cal_champion_seed43 returns",
    "diff_applied": diff_applied,
}
description = ("MATRIX_LR 0.04 -> 0.02 (low arm of the first Muon-LR bracket; Muon LR on all 8 blocks' "
               "matrix weights, 40.0% of params / 80.0% of 6N FLOP-relevant count; n=0 cold axis before "
               "this bracket). Champion base exp_tput_batch_2e17 (val_bpb 1.088286, AR64/width512, DEPTH 8, "
               "MLP_EXPANSION 2, TOTAL_BATCH_SIZE 2**17, DEVICE_BATCH_SIZE 64, compile "
               "max-autotune-no-cudagraphs). Confound: lr*wd coupling halves effective decay 0.8%->0.4%/step.")

out, err = ws / f"train_{EXP_ID}.stdout", ws / f"train_{EXP_ID}.stderr"
sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": EXP_ID, "agent": AGENT_NAME, "item": item, "queue_claimed": True,
    "direction": "decrease", "val_score": None,
    "submission_path": str(rep / f"submission_{EXP_ID}.csv"),
    "train_path": str(stamped),
    "stdout_path": str(out), "stderr_path": str(err),
    "pid": os.getpid(), "monitor_id": None, "description": description,
    "launched_at": datetime.now(timezone.utc).isoformat(),
    "diff_applied": diff_applied,
}
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))

env = {**os.environ, "CUDA_VISIBLE_DEVICES": "1",
       "HF_HOME": "/root/autodl-tmp/cache/huggingface", "HF_HUB_OFFLINE": "1",
       "TORCH_HOME": f"{FOCUS_ROOT}/.cache/torch"}
print("[TRAIN] launching python train.py at", datetime.now(timezone.utc).isoformat(), flush=True)
t0 = datetime.now(timezone.utc)
with open(out, "w") as fo, open(err, "w") as fe:
    proc = subprocess.run([sys.executable, "train.py"], cwd=str(rep), stdout=fo,
                          stderr=fe, timeout=1200, env=env)
elapsed = (datetime.now(timezone.utc) - t0).total_seconds()
print(f"[TRAIN] returncode={proc.returncode} wall={elapsed:.1f}s", flush=True)
sentinel.update({"status": "complete" if proc.returncode == 0 else "failed",
                 "returncode": proc.returncode, "wall_seconds": elapsed,
                 "finished_at": datetime.now(timezone.utc).isoformat()})
(ws / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
log = out.read_text(errors="ignore")
print("[PARSE] val_bpb =", re.findall(r"val_bpb:\s+([0-9.]+)", log),
      "num_steps =", re.findall(r"num_steps:\s+(\d+)", log))
print("[PARSE] tail:", log[-500:])
