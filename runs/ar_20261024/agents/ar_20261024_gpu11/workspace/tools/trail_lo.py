from api import *
import json, math
from datetime import datetime, timezone
from pathlib import Path

TEAM_WS = "005cb9ec-6fce-4bba-9340-21c08ab914c5"
EXP = "exp_gq_weight_decay_lo"
now = datetime.now(timezone.utc).isoformat()
CHAMPION = 1.088286
SIGMA = 0.002503

seed42, seed43 = 1.085846, 1.090242
mean2 = (seed42 + seed43) / 2
delta_mean = mean2 - CHAMPION          # signed, minimize -> negative is better
abs_pair = abs(seed42 - seed43)
final20_42, final20_43 = 0.077758, 0.080212

# ---------- 1. noise ledger: append pair 6 ----------
nf = get_file(MAIN_WS_ID, "knowledge/noise_floor_data.md")
nf_ver = nf.get("version", 0)
parts = nf.get("content", "").split("---", 2)
fm = yaml.safe_load(parts[1])
fm["pairs"].append({
    "metric_a": seed42, "metric_b": seed43, "abs_delta": abs_pair,
    "code_hash": "champion exp_tput_batch_2e17 + WEIGHT_DECAY 0.2->0.1 (AR64/w512/DEPTH8/MLP2/TOTAL 2**17/DBS64/compile); same code, seed 42 vs seed 43",
    "gpu_a": 1, "gpu_b": 1,
    "agents": [AGENT_NAME, AGENT_NAME],
    "date": "2026-10-24",
    "pair_type": "cross-seed ONLY (same GPU, same code)",
    "steps_a": 955, "steps_b": 952,
    "tokens_M_a": 125.2, "tokens_M_b": 124.8,
    "note": ("Exactly the sort of pair that kills a lucky-draw KEEP: seed 42 said -0.002440 (better), "
             "seed 43 said +0.001956 (worse). Also the LARGEST same-GPU seed pair on record (0.0044), "
             "so it pulls the pooled sigma up."),
    "final20_drop_a": final20_42, "final20_drop_b": final20_43,
})
squares = [p["abs_delta"] ** 2 for p in fm["pairs"]]
rms = math.sqrt(sum(squares) / len(squares))
sigma_new = rms / math.sqrt(2)
fm["n_pairs"] = len(fm["pairs"])
fm["sigma_estimate"] = round(sigma_new, 6)
fm["updated_at"] = now
fm["updated_by"] = AGENT_NAME

body = parts[2]
body += (f"\n- pair 6: {seed42:.6f} (GPU 1, seed 42) vs {seed43:.6f} (GPU 1, seed 43), |delta| = {abs_pair:.6f} — "
         f"identical WEIGHT_DECAY=0.1 code, SAME GPU, cross-seed only.\n"
         f"  Largest same-GPU seed pair so far: the seed-42 draw was -0.002440 vs champion and the seed-43 draw "
         f"was +0.001956. Same point estimate as MATRIX_LR=0.02 reversed sign; two-seed mean {mean2:.6f} "
         f"({delta_mean:+.6f} vs champion) = FLAT.\n\n"
         f"Pooled same-code sigma across {fm['n_pairs']} pairs = **{sigma_new:.6f}** (2-sigma band ~{2*sigma_new:.6f}).\n")
new_nf = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}"
r = requests.put(f"{API}/workspaces/{MAIN_WS_ID}/files/knowledge/noise_floor_data.md",
                 headers={**HEADERS, "If-Match": str(nf_ver)}, json={"content": new_nf})
print("noise ledger PUT:", r.status_code, "| n_pairs", fm["n_pairs"], "| sigma", round(sigma_new, 6))

# team noise_floor.md scalar mirror
tn = get_file(TEAM_WS, "knowledge/noise_floor.md")
tn_ver = tn.get("version", 0)
tparts = tn.get("content", "").split("---", 2)
tfm = yaml.safe_load(tparts[1])
tfm.update({"n_pairs": fm["n_pairs"], "sigma": round(sigma_new, 6),
            "near_miss_band_2sigma": round(2 * sigma_new, 6),
            "updated_at": now, "updated_by": AGENT_NAME})
tbody = tparts[2] + (f"\n## Update 2026-10-24 (pair 6, seed-only)\n"
                     f"| comparison | |delta| |\n|---|---|\n"
                     f"| WEIGHT_DECAY=0.1 code, seed 42 vs 43, same GPU, same code | {abs_pair:.6f} |\n\n"
                     f"sigma -> **{sigma_new:.6f}** (2-sigma {2*sigma_new:.6f}). Largest same-GPU seed pair on record, "
                     f"so the band widens slightly. The WD=0.1 arm's two seeds straddled the champion "
                     f"({seed42:.6f} better, {seed43:.6f} worse) -> FLAT.\n")
r2 = requests.put(f"{API}/workspaces/{TEAM_WS}/files/knowledge/noise_floor.md",
                  headers={**HEADERS, "If-Match": str(tn_ver)},
                  json={"content": f"---\n{yaml.safe_dump(tfm, sort_keys=False)}---{tbody}"})
print("team noise_floor.md PUT:", r2.status_code)
json.dump({"sigma": sigma_new, "n_pairs": fm["n_pairs"], "delta_mean": delta_mean,
           "abs_pair": abs_pair}, open("/tmp/noise.json", "w"))
