import json, os, sys
import requests, yaml
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu7"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()


def pf(resp):
    content = resp.get("content", "")
    parts = content.split("---")
    return yaml.safe_load(parts[1]) if len(parts) >= 3 else {}


roster_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md", headers=HEADERS).json()
roster = pf(roster_raw).get("teams", {}) or {}
print("=== ROSTER ===")
for name, t in roster.items():
    print(name, t["workspace_id"], t.get("members"))

champ_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/champion.md", headers=HEADERS).json()
print("\n=== CHAMPION v", champ_raw.get("version"), "===")
print(champ_raw.get("content"))

print("\n=== MAIN WS FILES ===")
for f in requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files", headers=HEADERS).json().get("files", []):
    print(f["path"], "v" + str(f.get("version")), f.get("updatedAt"))

print("\n=== TEAM QUEUES ===")
for name, t in roster.items():
    q = requests.get(f"{API}/workspaces/{t['workspace_id']}/files/queue.md", headers=HEADERS).json()
    print(f"--- {name} queue v{q.get('version')} ---")
    print(q.get("content", "(missing)")[:4000])

print("\n=== RECENT POSTS ===")
posts = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=25", headers=HEADERS).json().get("data", [])
for p in posts:
    print(p.get("id"), p.get("createdAt") or p.get("created_at"), p.get("author"), "|", p.get("title"))

print("\n=== NOISE FLOOR ===")
for p in ("knowledge/noise_floor.md", "knowledge/noise_floor_data.md", "knowledge/near_miss_ledger.md"):
    r = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/{p}", headers=HEADERS)
    if r.status_code == 200:
        print(f"--- {p} ---")
        print(r.json().get("content", "")[:3000])
    else:
        print(f"--- {p}: HTTP {r.status_code}")
