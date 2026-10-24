import json
from pathlib import Path
import requests, yaml

FOCUS_ROOT = Path("/root/autodl-tmp/ar_20261024")
AGENT_NAME = "ar_20261024_gpu8"
AGENT_DIR = FOCUS_ROOT / "agents" / AGENT_NAME
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(FOCUS_ROOT / "WORKSPACE_ID").read().strip()
WORKSHOP = open(FOCUS_ROOT / "WORKSHOP_NAME").read().strip()


def pf(resp):
    content = resp.get("content", "")
    parts = content.split("---")
    return yaml.safe_load(parts[1]) if len(parts) >= 3 else {}


print("API", API, "MAIN", MAIN_WS_ID, "WORKSHOP", WORKSHOP, "AGENT", AGENT_NAME)

roster_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md", headers=HEADERS).json()
roster = pf(roster_raw).get("teams", {}) or {}
print("\n=== ROSTER (version", roster_raw.get("version"), ") ===")
for name, t in roster.items():
    print(f"{name}: ws={t.get('workspace_id')} members={t.get('members')}")

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
    print((q.get("content") or "(missing)")[:5000])

print("\n=== RECENT POSTS (25) ===")
posts = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=25", headers=HEADERS).json().get("data", [])
for p in posts:
    print(p.get("id"), p.get("createdAt") or p.get("created_at"), p.get("author"), "|", p.get("title"))

print("\n=== DISCUSSION TRIGGERS ===")
trig = [p for p in posts if "[DISCUSSION-TRIGGER]" in (p.get("title") or "")]
for p in trig:
    cs = requests.get(f"{API}/posts/{p['id']}/comments", headers=HEADERS).json().get("data", [])
    done = sum(1 for c in cs if "[DISCUSS-DONE]" in (c.get("content") or ""))
    print(p.get("id"), p.get("createdAt"), p.get("title"), "DISCUSS-DONE:", done, "of", len(cs))

print("\n=== KNOWLEDGE ===")
for p in ("knowledge/noise_floor.md", "knowledge/noise_floor_data.md", "knowledge/near_miss_ledger.md"):
    r = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/{p}", headers=HEADERS)
    if r.status_code == 200:
        print(f"--- {p} v{r.json().get('version')} ---")
        print(r.json().get("content", ""))
    else:
        print(f"--- {p}: HTTP {r.status_code}")

print("\n=== PENDING RESULT SENTINEL ===")
pp = AGENT_DIR / "workspace" / "result_latest.json"
print("exists:", pp.exists())
