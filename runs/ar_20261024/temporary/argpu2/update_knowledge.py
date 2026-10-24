import json, math, requests, yaml
from datetime import datetime, timezone
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu2"
TEAM_WS_ID = "005cb9ec-6fce-4bba-9340-21c08ab914c5"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
NOW = datetime.now(timezone.utc).isoformat()
def pf(resp):
    c=resp.get("content",""); p=c.split("---")
    return yaml.safe_load(p[1]) if len(p)>=3 else {}

# ---------- noise_floor_data.md ----------
nf = requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/noise_floor_data.md", headers=H).json()
fm = pf(nf); pairs = fm.get("pairs") or []
new_pairs = [
 {"metric_a": 1.192527, "metric_b": 1.188308, "abs_delta": 0.004219,
  "code_hash": "upstream+dbs64+total2**19+muon098(0.95->0.98)", "gpu_a": 1, "gpu_b": 1,
  "agents": [AGENT_NAME, AGENT_NAME], "date": "2026-10-24",
  "note": "identical code, seed 42 vs 43 (same GPU). Momentum experiment's multi-seed confirmation."},
 {"metric_a": 1.169258, "metric_b": 1.164542, "abs_delta": 0.004716,
  "code_hash": "upstream+dbs64+total2**18+mlpexp4", "gpu_a": 0, "gpu_b": 1,
  "agents": ["ar_20261024_gpu1", AGENT_NAME], "date": "2026-10-24",
  "note": "identical code, seed 42 (GPU0) vs seed 43 (GPU1). Cross-GPU + cross-seed repeat."},
]
for p in new_pairs:
    if not any(abs((q.get("metric_a") or 0) - p["metric_a"]) < 1e-9 for q in pairs):
        pairs.append(p)
fm["pairs"] = pairs
fm["n_pairs"] = len(pairs)
fm["sigma_estimate"] = round(math.sqrt(sum(float(p["abs_delta"])**2 for p in pairs)/(2*len(pairs))), 6)
fm["updated_at"] = NOW
fm["updated_by"] = AGENT_NAME
body = nf.get("content","").split("---",2)[-1]
body = body.replace("Empirical same-code repeat measurements used by the multi-seed promotion gate.",
                    "Empirical same-code repeat measurements used by the multi-seed promotion gate.")
new = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}"
# rebuild human-readable list
lines = ["# Noise Floor Data", "", "Empirical same-code repeat measurements used by the multi-seed promotion gate.", ""]
for i,p in enumerate(pairs,1):
    lines.append(f"- pair {i}: {p['metric_a']} (GPU {p['gpu_a']}) vs {p['metric_b']} (GPU {p['gpu_b']}), |delta| = {p['abs_delta']:.6f} — {p['note']}")
lines += ["", f"Pooled same-code sigma across {len(pairs)} pairs = **{fm['sigma_estimate']:.6f}** "
              f"(2-sigma band ~{2*fm['sigma_estimate']:.4f}).", "",
          "Practical guidance: an experiment whose |delta| is below ~0.006 must be confirmed on a",
          "second seed before promotion. Same-code repeat noise is ~0.003-0.005, i.e. 2-3x the",
          "conservative 0.0015 default.", ""]
new = new.split("---",2)[0] + "---" + new.split("---",2)[1] + "---\n" + "\n".join(lines)
r = requests.put(f"{API}/workspaces/{MAIN}/files/knowledge/noise_floor_data.md",
                 headers={**H, "If-Match": str(nf.get("version",0))}, json={"content": new})
print("noise_floor_data PUT", r.status_code, r.text[:200])
print("sigma:", fm["sigma_estimate"], "n:", fm["n_pairs"])

# ---------- team dead_ends.md ----------
de = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/dead_ends.md", headers=H).json()
entry = (f"\n- exp_id: exp_gq_muon_mom_098\n"
         f"  axis: muon_momentum\n  direction: increase\n  value: 0.98\n"
         f"  delta_vs_contemporaneous_base: +0.000181 (improvement, seed 42, far below noise)\n"
         f"  delta_vs_current_champion(1.158107): worse by 0.034420\n"
         f"  seeds: [1.192527 (s42), 1.188308 (s43)] on identical code -> seed swing 0.004219\n"
         f"  family: exp_gq\n  date: 2026-10-24\n"
         f"  reason: Paired seed-42 effect 0.00018 vs same-code seed noise 0.0042 => no measurable mechanism. Tested on old base (TOTAL_BATCH 2**19, ~196 steps) where ramp frac only reached 0.65; on the new 2**18 base (~374 steps) the ramp saturates at step 300, so a retest would test a different regime. Not a permanent dead end for the new base.\n")
r = requests.put(f"{API}/workspaces/{TEAM_WS_ID}/files/dead_ends.md",
                 headers={**H, "If-Match": str(de.get("version",0))},
                 json={"content": de.get("content","") + entry})
print("dead_ends PUT", r.status_code)
