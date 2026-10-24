"""Orchestrator coordination helpers for the autoresearch run.

Pure coordination only — no experiments. The orchestrator's writes are
champion-promotion copies and log appends, plus (per the task profile)
team formation and queue seeding, which are coordination actions.
"""
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

FOCUS_ROOT = Path(os.environ.get("FOCUS_ROOT", "/root/autodl-tmp/ar_20261022.hi"))
WS_ID = (FOCUS_ROOT / "WORKSPACE_ID").read_text().strip()
WORKSHOP = (FOCUS_ROOT / "WORKSHOP_NAME").read_text().strip()

API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
# Orchestrator uses the admin bootstrap token so it can create team workspaces.
_token = None
for p in (FOCUS_ROOT / ".key", Path.home() / ".clawinstitute" / "token"):
    if p.exists():
        _token = p.read_text().strip()
        break
if not _token and os.environ.get("CLAWINSTITUTE_TOKEN"):
    _token = os.environ["CLAWINSTITUTE_TOKEN"]
if not _token:
    tokens = json.loads((FOCUS_ROOT / "agent_tokens.json").read_text())
    _token = list(tokens.values())[0]
TOKEN = _token

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "X-Agent-Name": "orchestrator",
}


def parse_fm(resp_or_text):
    text = resp_or_text.get("content", "") if isinstance(resp_or_text, dict) else resp_or_text
    parts = text.split("---")
    if len(parts) >= 3:
        try:
            return yaml.safe_load(parts[1]) or {}
        except Exception:
            return {}
    return {}


def get_file(ws_id, path):
    r = requests.get(f"{API}/workspaces/{ws_id}/files/{path}", headers=HEADERS)
    r.raise_for_status()
    return r.json()


def put_file(ws_id, path, content, if_match=None):
    h = dict(HEADERS)
    if if_match is not None:
        h["If-Match"] = str(if_match)
    r = requests.put(f"{API}/workspaces/{ws_id}/files/{path}", headers=h,
                     json={"content": content})
    return r


def now_iso():
    return datetime.now(timezone.utc).isoformat()
