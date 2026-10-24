"""Parse the seed-43 calibration training log: final metrics + final-20% loss-drop."""
import json
import re
import sys
from pathlib import Path

FOCUS_ROOT = Path("/root/autodl-tmp/ar_20261024")
WS = FOCUS_ROOT / "agents" / "ar_20261024_gpu8" / "workspace"
EXP_ID = "exp_cal_champion_seed43"
log_path = WS / f"train_{EXP_ID}.stdout"

text = log_path.read_text(errors="ignore")

# ---- final summary block ----
def grab(key):
    m = re.search(rf"^{re.escape(key)}:\s*([0-9.eE+-]+)\s*$", text, re.MULTILINE)
    return float(m.group(1)) if m else None

summary = {k: grab(k) for k in (
    "val_bpb", "training_seconds", "total_seconds", "peak_vram_mb",
    "mfu_percent", "total_tokens_M", "num_steps", "num_params_M", "depth")}

# ---- progress lines (written with \r) ----
# step 00042 (4.4%) | loss: 3.141592 | lrm: 1.00 | dt: 300ms | tok/sec: 411,300 | mfu: 12.1% | epoch: 1 | remaining: 260s
pat = re.compile(
    r"step\s+(\d+)\s+\(([\d.]+)%\)\s*\|\s*loss:\s*([0-9.]+)\s*\|\s*lrm:\s*([0-9.]+)\s*\|"
    r"\s*dt:\s*([0-9.]+)ms\s*\|\s*tok/sec:\s*([\d,]+)\s*\|\s*mfu:\s*([\d.]+)%")
rows = []
for m in pat.finditer(text.replace("\r", "\n")):
    rows.append({"step": int(m.group(1)), "pct": float(m.group(2)), "loss": float(m.group(3)),
                 "lrm": float(m.group(4)), "dt_ms": float(m.group(5)),
                 "tok_per_sec": int(m.group(6).replace(",", "")), "mfu": float(m.group(7))})

result = {"exp_id": EXP_ID, "log": str(log_path), "summary": summary,
          "n_logged_steps": len(rows),
          "first_step": rows[0] if rows else None,
          "last_step": rows[-1] if rows else None}

if rows:
    N = rows[-1]["step"]
    losses = [r["loss"] for r in rows]
    steps = [r["step"] for r in rows]
    # primary definition: smoothed loss at ~80% of the completed steps vs the final smoothed loss
    idx80 = next((i for i, s in enumerate(steps) if s >= 0.80 * N), len(steps) - 1)
    loss80 = losses[idx80]
    loss_final = losses[-1]
    # window means (robust): [80%,90%) vs [90%,100%]
    w1 = [r["loss"] for r in rows if 0.80 * N <= r["step"] < 0.90 * N]
    w2 = [r["loss"] for r in rows if 0.90 * N <= r["step"] <= N]
    mean_w1 = sum(w1) / len(w1) if w1 else None
    mean_w2 = sum(w2) / len(w2) if w2 else None
    # absolute loss range across the run (for the ">1% of total range" undertrain test)
    loss_range = max(losses) - min(losses)
    tok = [r["tok_per_sec"] for r in rows if r["step"] > 10]
    result["dynamics"] = {
        "definition_primary": "loss_smooth(step>=0.80*N) - loss_smooth(final step)",
        "step_at_80pct_index": idx80,
        "step_at_80pct": steps[idx80],
        "loss_at_80pct": loss80,
        "loss_final": loss_final,
        "final20_drop": loss80 - loss_final,
        "final20_drop_rel_pct": 100.0 * (loss80 - loss_final) / loss80 if loss80 else None,
        "mean_loss_80_90": mean_w1,
        "mean_loss_90_100": mean_w2,
        "final10_of_20_drop": (mean_w1 - mean_w2) if (mean_w1 is not None and mean_w2 is not None) else None,
        "loss_range_abs": loss_range,
        "final20_drop_pct_of_range": 100.0 * (loss80 - loss_final) / loss_range if loss_range else None,
        "tok_per_sec_steady_mean": (sum(tok) / len(tok)) if tok else None,
        "tok_per_sec_last": rows[-1]["tok_per_sec"],
        "pct_done_at_last": rows[-1]["pct"],
        "N_steps_last_logged": N,
    }

# ---- champion baseline for comparison ----
champ_md = (FOCUS_ROOT / "champion" / "train.py")
result["champion_metric"] = 1.088286
result["delta_vs_champion"] = (summary["val_bpb"] - 1.088286) if summary.get("val_bpb") is not None else None

(WS / "analysis.json").write_text(json.dumps(result, indent=2, default=str))
print(json.dumps(result, indent=2, default=str))
