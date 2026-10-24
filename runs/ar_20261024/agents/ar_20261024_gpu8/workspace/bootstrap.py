"""Bootstrap the dynamically-dispatched gpu8 agent dir, mirroring launch.py setup_agent."""
import json
import os
import shutil
from pathlib import Path

FOCUS_ROOT = Path("/root/autodl-tmp/ar_20261024")
TEMPLATE_ROOT = Path("/root/autodl-tmp/AutoScientists")
AGENT_NAME = "ar_20261024_gpu8"
AGENT_DIR = FOCUS_ROOT / "agents" / AGENT_NAME

# ---- credentials: shared admin token (same value every agent on this run uses) ----
shared = json.loads((FOCUS_ROOT / "agent_tokens.json").read_text())["ar_20261024_gpu1"]
creds = AGENT_DIR / "credentials.json"
if not creds.exists():
    creds.write_text(json.dumps({"api_key": shared, "agent_name": AGENT_NAME,
                                 "api_key_unique": shared}, indent=2))
    creds.chmod(0o600)

# ---- AGENT.md ----
agent_md = AGENT_DIR / "AGENT.md"
if not agent_md.exists():
    agent_md.write_text(f"""---
name: {AGENT_NAME}
role: gpu
team: null
gpu: 0
server: server3
last_seen: null
status: idle
session_count: 0
last_experiment: null
last_outcome: null
last_val_bpb: null
---

# {AGENT_NAME}

GPU agent on GPU 0. Dispatched by orchestrator 2026-10-24T08:12Z for seed calibration.

## Current Focus
(not yet assigned to a team)

## Suggestions for System Improvement
(none yet)

## Notes for Next Session
- Agent dir did not exist at dispatch; created from HEARTBEAT/launch.py conventions.
- gpu8 was absent from run_metadata.json, agent_tokens.json, and teams/roster.md.
""")

# ---- memory ----
mem = AGENT_DIR / "memory" / "MEMORY.md"
if not mem.exists():
    mem.write_text("# Memory Index\n\n(no memories yet)\n")
sc = AGENT_DIR / "memory" / ".session_count"
if not sc.exists():
    sc.write_text("0")

# ---- HEARTBEAT.md: template + injected role and team docs (exact launch.py logic) ----
system_dir = TEMPLATE_ROOT / "system" / "templates"
heartbeat = (system_dir / "HEARTBEAT.md").read_text()

role_content = (system_dir / "ROLE-GPU.md").read_text()
role_parts = role_content.split("---")
if len(role_parts) >= 3:
    role_content = "---".join(role_parts[2:]).strip()

team_content = (system_dir / "ROLE-TEAM.md").read_text()
team_parts = team_content.split("---")
if len(team_parts) >= 3:
    team_content = "---".join(team_parts[2:]).strip()

heartbeat = heartbeat.replace(
    "<!-- ROLE_CONTENT_PLACEHOLDER -->\n<!-- launch.py replaces this with system/templates/ROLE-{role}.md -->",
    role_content)
heartbeat = heartbeat.replace(
    "<!-- TEAM_CONTENT_PLACEHOLDER -->\n<!-- launch.py replaces this with system/templates/ROLE-TEAM.md -->",
    team_content)
(AGENT_DIR / "HEARTBEAT.md").write_text(heartbeat)

# ---- workspace repo: copy the training repo files (as launch.py does) ----
src_repo = FOCUS_ROOT / "repo"
dst_repo = AGENT_DIR / "workspace" / "repo"
for f in ("prepare.py", "pyproject.toml", "uv.lock", "train.py"):
    s = src_repo / f
    if s.exists() and not (dst_repo / f).exists():
        shutil.copy(s, dst_repo / f)

print("bootstrap ok")
for p in sorted(AGENT_DIR.rglob("*")):
    if p.is_file():
        print(" ", p.relative_to(AGENT_DIR), p.stat().st_size)
