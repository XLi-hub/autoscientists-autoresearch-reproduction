import json, os, requests, yaml
from pathlib import Path
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_analyst3"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()

def parse_frontmatter(resp):
    content = resp.get("content", "")
    parts = content.split("---")
    return yaml.safe_load(parts[1]) if len(parts) >= 3 else {}

# all posts search for discussion trigger
r = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=200", headers=HEADERS, timeout=30)
posts = r.json().get("data", [])
trig = [p for p in posts if "[DISCUSSION-TRIGGER]" in p.get("title","")]
print("TOTAL posts:", len(posts), "triggers:", len(trig))
for p in trig:
    print("TRIG:", p.get("createdAt"), p["id"], p["title"][:120])

# roster
rr = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md", headers=HEADERS, timeout=20).json()
roster = parse_frontmatter(rr)
print("\nROSTER keys:", list(roster.keys()))
print(json.dumps(roster, indent=1)[:4000])
