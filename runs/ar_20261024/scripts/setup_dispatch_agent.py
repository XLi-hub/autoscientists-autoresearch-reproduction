#!/usr/bin/env python3
"""Ensure an agent exists (dirs, credentials, API registration, roster membership)
BEFORE an orchestrator dispatches it.

Discovered the hard way at cycle 3: gpu7 was dispatched without setup_agent, so it had
no directory, no API registration and no roster entry; Check B would have idled it and
POST /posts returned 404 "Agent ... not found" (its first [RESULT] post was lost).

Usage: python3 scripts/setup_dispatch_agent.py <agent_name> [team]

Idempotent: safe to re-run before every dispatch.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import orch_common as oc  # noqa: E402
import requests  # noqa: E402
import shutil  # noqa: E402


def ensure_local_dirs(name, role="gpu"):
    agent_dir = oc.FOCUS_ROOT / "agents" / name
    (agent_dir / "workspace" / "repo").mkdir(parents=True, exist_ok=True)
    (agent_dir / "memory").mkdir(parents=True, exist_ok=True)
    creds = agent_dir / "credentials.json"
    if not creds.exists():
        creds.write_text(json.dumps({"api_key": oc.TOKEN, "agent_name": name}, indent=2))
        creds.chmod(0o600)
    # HEARTBEAT/AGENT templates: copy from a sibling agent if missing
    for fname in ("HEARTBEAT.md", "AGENT.md"):
        dst = agent_dir / fname
        if dst.exists():
            continue
        for sib in sorted((oc.FOCUS_ROOT / "agents").glob("*_gpu*")):
            src = sib / fname
            if src.exists() and sib != agent_dir:
                shutil.copy(src, dst)
                break
    # repo/ (train.py, prepare.py, ...) for GPU agents
    repo_dst = agent_dir / "workspace" / "repo"
    if role == "gpu" and not (repo_dst / "train.py").exists():
        bundle = oc.FOCUS_ROOT / "repo"
        if bundle.exists():
            for f in bundle.iterdir():
                if f.is_file():
                    shutil.copy(f, repo_dst / f.name)
    return agent_dir


def ensure_registered(name):
    r = requests.post(f"{oc.API}/agents/register", headers=oc.HEADERS,
                      json={"name": name, "description": "GPU agent (RTX 4080S)"})
    return r.status_code, r.text[:160]


def ensure_roster(name, team):
    if not team:
        return "no team given"
    raw = oc.get_file(oc.WS_ID, "teams/roster.md")
    parts = raw["content"].split("---", 2)
    import yaml
    d = yaml.safe_load(parts[1])
    teams = d.get("teams") or {}
    if team not in teams:
        return f"team {team} not in roster"
    members = teams[team].setdefault("members", [])
    if name in members:
        return "already a member"
    members.append(name)
    new = "---\n" + yaml.safe_dump(d, sort_keys=False) + "---" + parts[2]
    rr = requests.put(f"{oc.API}/workspaces/{oc.WS_ID}/files/teams/roster.md",
                      headers={**oc.HEADERS, "If-Match": str(raw["version"])},
                      json={"content": new})
    return f"roster put {rr.status_code}"


if __name__ == "__main__":
    name = sys.argv[1]
    team = sys.argv[2] if len(sys.argv) > 2 else None
    print("dirs:", ensure_local_dirs(name))
    print("register:", ensure_registered(name))
    print("roster:", ensure_roster(name, team))
