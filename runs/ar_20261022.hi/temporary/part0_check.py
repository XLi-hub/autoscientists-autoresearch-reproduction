import json, os, requests, yaml
from pathlib import Path
from datetime import datetime, timezone

AGENT_NAME = "ar_20261022hi_gpu5"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
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

print("API", API, "WS", MAIN_WS_ID, "WORKSHOP", WORKSHOP)

# Check A2
recent = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=30", headers=HEADERS).json().get("data", [])
print("recent posts:", len(recent))
trigger_posts = [p for p in recent if "[DISCUSSION-TRIGGER]" in p.get("title","")]
print("triggers:", [(p["id"], p["title"], p.get("createdAt") or p.get("created_at")) for p in trigger_posts])
for p in trigger_posts[:2]:
    cs = requests.get(f"{API}/posts/{p['id']}/comments", headers=HEADERS).json().get("data", [])
    done = [c for c in cs if "[DISCUSS-DONE]" in str(c.get("content",""))]
    print(f"  trigger {p['id']}: comments={len(cs)} DISCUSS-DONE={len(done)}")

# Check B
roster_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md", headers=HEADERS).json()
roster = parse_frontmatter(roster_raw).get("teams", {}) or {}
print("roster teams:", json.dumps(roster, indent=1)[:2000])
MY_TEAM = TEAM_WS_ID = None
ALL_TEAM_WS_IDS = {}
for name, t in roster.items():
    ALL_TEAM_WS_IDS[name] = t.get("workspace_id")
    if AGENT_NAME in t.get("members", []):
        MY_TEAM = name; TEAM_WS_ID = t.get("workspace_id")
print("MY_TEAM:", MY_TEAM, "TEAM_WS_ID:", TEAM_WS_ID)

json.dump({"MY_TEAM": MY_TEAM, "TEAM_WS_ID": TEAM_WS_ID, "ALL_TEAM_WS_IDS": ALL_TEAM_WS_IDS},
          open("/tmp/part0_state.json","w"), indent=2)

# also print latest titles
print("\n=== RECENT POST TITLES ===")
for p in recent[:12]:
    print(p.get("createdAt") or p.get("created_at"), "|", p.get("title"))
