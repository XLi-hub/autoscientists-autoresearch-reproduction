import json
from pathlib import Path
import requests, yaml

FOCUS_ROOT = Path("/root/autodl-tmp/ar_20261024")
AGENT_NAME = "ar_20261024_gpu8"
creds = json.load(open(FOCUS_ROOT / "agents" / AGENT_NAME / "credentials.json"))
H = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
     "X-Agent-Name": AGENT_NAME}
API = "http://localhost:3000/api/v1"
MAIN = open(FOCUS_ROOT / "WORKSPACE_ID").read().strip()
WORKSHOP = open(FOCUS_ROOT / "WORKSHOP_NAME").read().strip()
TEAM_WS = json.load(open(FOCUS_ROOT / "agents" / AGENT_NAME / "workspace" / "claim_record.json"))["team_ws_id"]
EXP = "exp_cal_champion_seed43"


def pf(resp):
    c = resp.get("content", "")
    p = c.split("---")
    return yaml.safe_load(p[1]) if len(p) >= 3 else {}


# champion
ch = requests.get(f"{API}/workspaces/{MAIN}/files/champion.md", headers=H).json()
print("champion version:", ch.get("version"), "metric:", pf(ch).get("metric_value"), "exp:", pf(ch).get("experiment_id"))
print("champion/SOURCE last line:", (FOCUS_ROOT / "champion" / "SOURCE").read_text().strip().splitlines()[-1])

# result file
rr = requests.get(f"{API}/workspaces/{MAIN}/files/results/{EXP}.md", headers=H)
print("\nresults file HTTP:", rr.status_code, "v", rr.json().get("version"))
fm = pf(rr.json())
print("  frontmatter:", {k: fm.get(k) for k in ("type", "promotable", "outcome", "val_bpb", "champion_val_bpb", "delta_vs_champion", "gpu_device", "final20_loss_drop")})

# noise floor
nf = requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/noise_floor_data.md", headers=H).json()
nfm = pf(nf)
print("\nnoise_floor v", nf.get("version"), "n_pairs:", nfm.get("n_pairs"), "sigma:", nfm.get("sigma_estimate"))
for i, p in enumerate(nfm.get("pairs") or [], 1):
    print(f"  pair{i}: {p.get('metric_a')} vs {p.get('metric_b')} |d|={p.get('abs_delta'):.6f} type={p.get('pair_type','-')}")
print("  body pair-4 bullet:", [l for l in nf.get("content", "").splitlines() if l.startswith("- pair 4")])

# queue
q = requests.get(f"{API}/workspaces/{TEAM_WS}/files/queue.md", headers=H).json()
qfm = pf(q)
print("\nqueue v", q.get("version"), "claims:", qfm.get("claims"))
print("  still pending:", [it.get("id") for it in (qfm.get("pending") or [])])
done = [it for it in (qfm.get("completed") or []) if it.get("id") == EXP]
print("  completed entry:", json.dumps(done[0], default=str)[:900] if done else "MISSING")

# posts
posts = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=10", headers=H).json().get("data", [])
print("\nrecent posts:")
for p in posts[:6]:
    print("  ", p.get("id"), p.get("createdAt"), p.get("author"), "|", p.get("title"))
hit = [p for p in posts if EXP in (p.get("title") or "")]
if hit:
    p = hit[0]
    print("\nMATCHED POST:", p.get("id"), "tags:", p.get("tags"))
    full = requests.get(f"{API}/posts/{p['id']}", headers=H).json()
    print("author:", full.get("author"), "created:", full.get("createdAt"))
    print("---content---")
    print(full.get("content", "")[:2500])
else:
    print("\n!! no matching post found")

# sentinel
rl = json.loads((FOCUS_ROOT / "agents" / AGENT_NAME / "workspace" / "result_latest.json").read_text())
print("\nsentinel:", {k: rl.get(k) for k in ("status", "posted_to_workshop", "result_post_id", "val_score", "outcome")})
