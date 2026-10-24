"""Bootstrap: seed champion, form teams, seed queues (cold-start fast path)."""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from orch_common import (FOCUS_ROOT, WS_ID, WORKSHOP, API, HEADERS, requests,
                         yaml, get_file, put_file, now_iso)

PREFIX = (FOCUS_ROOT / "AGENT_PREFIX").read_text().strip() if (FOCUS_ROOT / "AGENT_PREFIX").exists() else FOCUS_ROOT.name.replace("-", "_")
# Recompute prefix the same way launch.py does
RUN_ID = FOCUS_ROOT.name.replace("-", "_").replace(".", "")
PREFIX = RUN_ID

print(f"FOCUS_ROOT={FOCUS_ROOT}")
print(f"WS_ID={WS_ID}  WORKSHOP={WORKSHOP}  PREFIX={PREFIX}")

# ── 0. Seed champion/ from pristine repo/ (champion-promotion-style copy) ──
champ_dir = FOCUS_ROOT / "champion"
repo_dir = FOCUS_ROOT / "repo"
if not (champ_dir / "train.py").exists():
    for fname in ("train.py", "prepare.py", "pyproject.toml", "uv.lock"):
        src = repo_dir / fname
        if src.exists():
            shutil.copy2(src, champ_dir / fname)
    (champ_dir / "SOURCE").write_text(
        f"pristine upstream seed, populated {now_iso()}\n")
    print("  Seeded champion/ with pristine repo files")
else:
    print("  champion/train.py already present")

# ── 1. Team definitions ──
TEAMS = {
    "throughput": {
        "hypothesis": "H-throughput",
        "label": "Model is undertrained at the current 5-min compute budget",
        "prediction": "Experiments that increase effective optimizer steps by >=10% will KEEP",
        "falsification": "3 rotations of prediction-consistent experiments all DISCARD",
        "members": [f"{PREFIX}_analyst1", f"{PREFIX}_gpu1", f"{PREFIX}_gpu2"],
    },
    "gradient-quality": {
        "hypothesis": "H-gradient-quality",
        "label": "Gradient signal per step is suboptimal",
        "prediction": "Changes that reduce gradient noise or improve update direction will KEEP",
        "falsification": "3 rotations of prediction-consistent experiments all DISCARD",
        "members": [f"{PREFIX}_analyst2", f"{PREFIX}_gpu3", f"{PREFIX}_gpu4"],
    },
    "capacity": {
        "hypothesis": "H-capacity",
        "label": "The model's parametric capacity or representational structure limits the metric",
        "prediction": "Structural changes (depth/width/heads) will KEEP more than tuning",
        "falsification": "3 rotations of prediction-consistent experiments all DISCARD",
        "members": [f"{PREFIX}_analyst3", f"{PREFIX}_gpu5", f"{PREFIX}_gpu6"],
    },
}

# Seed experiments (one per team) — concrete single-change diffs to repo/train.py
SEED_EXPERIMENTS = {
    "throughput": [{
        "id": "exp_batch_2e18",
        "description": "Halve TOTAL_BATCH_SIZE 2**19 -> 2**18 (more optimizer steps)",
        "rationale": ("H-throughput: smaller total batch = more optimizer steps within "
                      "the fixed 5-min budget, giving the model more effective training."),
        "axis": "total_batch_size", "direction": "decrease", "value": "2**18",
        "diff": "In train.py change `TOTAL_BATCH_SIZE = 2**19` to `TOTAL_BATCH_SIZE = 2**18`.",
    }],
    "gradient-quality": [{
        "id": "exp_warmup_0p1",
        "description": "Add LR warmup WARMUP_RATIO 0.0 -> 0.1",
        "rationale": ("H-gradient-quality: no warmup means the first steps take large, noisy "
                      "updates; a short warmup improves early gradient signal."),
        "axis": "warmup_ratio", "direction": "increase", "value": "0.1",
        "diff": "In train.py change `WARMUP_RATIO = 0.0` to `WARMUP_RATIO = 0.1`.",
    }],
    "capacity": [{
        "id": "exp_depth_10",
        "description": "Increase DEPTH 8 -> 10 (more capacity)",
        "rationale": ("H-capacity: the current depth-8 model may be capacity-limited; "
                      "a deeper model has more representational power for the same budget."),
        "axis": "depth", "direction": "increase", "value": "10",
        "diff": "In train.py change `DEPTH = 8` to `DEPTH = 10`.",
    }],
}

# ── 2. Create team workspaces + files ──
roster_teams = {}
for team_name, meta in TEAMS.items():
    r = requests.post(f"{API}/workspaces", headers=HEADERS, json={
        "title": f"{WORKSHOP}-{team_name}",
        "workshop": WORKSHOP,
        "visibility": "public",
    })
    if r.status_code >= 300:
        print(f"  ERROR creating workspace for {team_name}: {r.status_code} {r.text[:200]}")
        sys.exit(1)
    team_ws_id = r.json()["id"]
    print(f"  Team '{team_name}' workspace: {team_ws_id}")

    strategy = f"""---
hypothesis: {meta['hypothesis']}
prediction: "{meta['prediction']}"
falsification: "{meta['falsification']}"
age_rotations: 0
supported_keeps: 0
refuted_discards: 0
---

# Team {team_name}

**Hypothesis ({meta['hypothesis']}):** {meta['label']}

**Prediction:** {meta['prediction']}

**Falsification:** {meta['falsification']}

Proposals this team queues must be evaluable against the prediction.
Any axis is in-scope as long as the change is one the hypothesis predicts will KEEP.
"""
    put_file(team_ws_id, "strategy.md", strategy)
    put_file(team_ws_id, "queue.md", "---\nclaims: {}\npending: []\ncompleted: []\n---\n\n# Experiment Queue\n")
    put_file(team_ws_id, "dead_ends.md", "---\ncount: 0\n---\n\n# Dead Ends\n\n(none yet)\n")
    put_file(team_ws_id, "hypotheses.md", "---\ncount: 1\n---\n\n# Hypotheses\n\n(none yet)\n")

    roster_teams[team_name] = {
        "workspace_id": team_ws_id,
        "members": meta["members"],
        "hypothesis": meta["hypothesis"],
        "prediction": meta["prediction"],
        "falsification": meta["falsification"],
    }

# ── 3. Write roster.md ──
roster_fm = {"teams": roster_teams, "updated_at": now_iso(), "phase": "executing"}
roster_content = f"---\n{yaml.safe_dump(roster_fm, sort_keys=False)}---\n\n# Team Roster\n\nHypothesis-based teams.\n"
r = put_file(WS_ID, "teams/roster.md", roster_content)
print(f"  roster.md write: {r.status_code}")
assert r.status_code < 300, r.text

# ── 4. Seed queues: post [PROPOSAL] + write queue.md ──
for team_name, exps in SEED_EXPERIMENTS.items():
    team_ws_id = roster_teams[team_name]["workspace_id"]
    members = roster_teams[team_name]["members"]
    pending_items = []
    for exp in exps:
        r = requests.post(f"{API}/posts", headers=HEADERS, json={
            "workshop": WORKSHOP,
            "title": f"[PROPOSAL] {exp['id']}: {exp['description']}",
            "content": (f"## Mechanism\n{exp['rationale']}\n\n"
                        f"## Axis\naxis: {exp['axis']}\ndirection: {exp['direction']}\nvalue: {exp['value']}\n\n"
                        f"## Diff\n```python\n{exp['diff']}\n```\n\n## Team\n{team_name}"),
            "notify_agents": members,
            "tags": [f"team:{team_name}", "type:proposal", f"axis:{exp['axis']}", f"direction:{exp['direction']}"],
        })
        post_id = r.json().get("post", {}).get("id") if r.status_code < 300 else None
        print(f"  [PROPOSAL] {exp['id']} -> HTTP {r.status_code} (post {post_id})")
        pending_items.append({
            "id": exp["id"],
            "description": exp["description"],
            "priority": "high",
            "axis": exp["axis"],
            "direction": exp["direction"],
            "value": exp["value"],
            "diff": exp["diff"],
            "proposed_by": "orchestrator",
            "proposal_post": post_id,
            "proposed_at": now_iso(),
        })

    q_fm = {"claims": {}, "pending": pending_items, "completed": []}
    q_content = f"---\n{yaml.safe_dump(q_fm, sort_keys=False)}---\n\n# Experiment Queue\n"
    r = put_file(team_ws_id, "queue.md", q_content)
    print(f"  queue.md for {team_name}: HTTP {r.status_code}")

print("\nBootstrap complete.")
print(json.dumps({k: v["workspace_id"] for k, v in roster_teams.items()}, indent=2))
