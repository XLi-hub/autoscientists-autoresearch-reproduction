from api import *
import json, os
from datetime import datetime, timezone
from pathlib import Path

WS = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace")
REP = WS / "repo"
exp_id = "exp_gq_weight_decay_lo"
item = {
    "id": exp_id, "axis": "weight_decay", "direction": "decrease", "value": 0.1,
    "current_value": 0.2, "priority": "high", "bold_bet": True,
    "diff": "WEIGHT_DECAY = 0.1 (was 0.2), train.py:444, single token",
    "proposal_post": "55aa397c-2b77-4c20-90e5-e9b285ad3491",
    "proposed_by": "ar_20261024_analyst2",
    "diff_applied": True,
    "noise_gate": "second seed if |delta|<0.006",
}
pid = int((WS / "train.pid").read_text().strip())
sentinel = {
    "status": "running", "posted_to_workshop": False,
    "exp_id": exp_id, "agent": AGENT_NAME, "item": item, "queue_claimed": True,
    "direction": "minimize", "val_score": None,
    "submission_path": str(REP / f"submission_{exp_id}.csv"),
    "train_path": str(REP / f"train_{exp_id}.py"),
    "stdout_path": str(WS / f"train_{exp_id}.stdout"),
    "stderr_path": str(WS / f"train_{exp_id}.stderr"),
    "pid": pid, "monitor_id": None,
    "description": "WEIGHT_DECAY 0.2 -> 0.1 at fixed MATRIX_LR 0.04 (train.py:444). Isolates the decay channel in muon_step_fused (sign-masked, lr*wd*p); de-confounder for the flat MATRIX_LR bracket.",
    "launched_at": datetime.now(timezone.utc).isoformat(),
}
(WS / "result_latest.json").write_text(json.dumps(sentinel, indent=2, default=str))
print("sentinel written, pid", pid)
