import json, os, requests, yaml
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu2"
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

print("=== roster ===")
roster_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md", headers=HEADERS).json()
print(json.dumps(roster_raw, indent=2)[:3000])
roster = (parse_frontmatter(roster_raw) or {}).get("teams", {}) or {}
print("roster teams:", list(roster.keys()))

MY_TEAM = TEAM_WS_ID = None
ALL_TEAM_WS_IDS = {}
for name, t in roster.items():
    ALL_TEAM_WS_IDS[name] = t["workspace_id"]
    if AGENT_NAME in t.get("members", []):
        MY_TEAM = name; TEAM_WS_ID = t["workspace_id"]
print("MY_TEAM:", MY_TEAM, "TEAM_WS_ID:", TEAM_WS_ID)

print("\n=== champion.md ===")
champ_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/champion.md", headers=HEADERS).json()
print("version:", champ_raw.get("version"))
print(json.dumps(parse_frontmatter(champ_raw), indent=2))

print("\n=== recent posts ===")
recent = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=30", headers=HEADERS).json().get("data", [])
for p in recent:
    print(p.get("id"), "|", p.get("title"), "|", p.get("created_at") or p.get("createdAt"), "| author:", p.get("author"))
print("n posts:", len(recent))

triggers = [p for p in recent if "[DISCUSSION-TRIGGER]" in p.get("title", "")]
print("triggers:", [(t["id"], t["title"]) for t in triggers])
