import json, os, re, sys
import requests, yaml
from pathlib import Path
from datetime import datetime, timezone

FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_analyst2"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()

def parse_frontmatter(resp):
    content = resp.get("content", "")
    parts = content.split("---")
    return yaml.safe_load(parts[1]) if len(parts) >= 3 else {}

print("API:", API, "WS:", MAIN_WS_ID, "WORKSHOP:", WORKSHOP)
# roster
roster_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md", headers=HEADERS, timeout=30)
print("roster status:", roster_raw.status_code)
try:
    rj = roster_raw.json()
    print("ROSTER CONTENT:")
    print((rj.get("content") or "")[:4000])
except Exception as e:
    print("roster err", e, roster_raw.text[:500])

# recent posts
recent = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=30", headers=HEADERS, timeout=30)
print("\nposts status:", recent.status_code)
try:
    posts = recent.json().get("data", [])
    print("n posts:", len(posts))
    for p in posts[:30]:
        print(p.get("id"), "|", p.get("createdAt") or p.get("created_at"), "|", p.get("title")[:110])
except Exception as e:
    print("posts err", e, recent.text[:1000])
