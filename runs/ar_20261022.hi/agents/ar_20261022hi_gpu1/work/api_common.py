"""Shared AnonAPI helpers for ar_20261022hi_gpu1."""
import json, os, re
from pathlib import Path
from datetime import datetime, timezone

import requests
import yaml

AGENT_NAME = "ar_20261022hi_gpu1"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
TEAM_WS_ID = "54202fe1-b766-43f1-b374-9e4ed188c153"  # team: throughput

_creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {_creds['api_key']}",
           "Content-Type": "application/json",
           "X-Agent-Name": AGENT_NAME}


def parse_frontmatter(resp):
    content = resp.get("content", "")
    parts = content.split("---")
    return yaml.safe_load(parts[1]) if len(parts) >= 3 else {}


def get_file(ws, path):
    return requests.get(f"{API}/workspaces/{ws}/files/{path}", headers=HEADERS).json()


def put_file(ws, path, content, version=None):
    h = dict(HEADERS)
    if version is not None:
        h["If-Match"] = str(version)
    return requests.put(f"{API}/workspaces/{ws}/files/{path}", headers=h,
                        json={"content": content})


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def roster():
    return parse_frontmatter(get_file(MAIN_WS_ID, "teams/roster.md")).get("teams", {}) or {}


def team_members():
    t = roster().get("throughput", {})
    return t.get("members", [])
