import json, os, requests, yaml, re
from pathlib import Path

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

recent = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=30", headers=HEADERS).json().get("data", [])
print("num posts:", len(recent))
for p in recent[:30]:
    print(p.get("id"), p.get("created_at") or p.get("createdAt"), "|", p.get("title","")[:110])

trigger_posts = [p for p in recent if "[DISCUSSION-TRIGGER]" in p.get("title","")]
print("\nTRIGGERS:", [(p["id"], p["title"][:80]) for p in trigger_posts])
for tp in trigger_posts:
    cs = requests.get(f"{API}/posts/{tp['id']}/comments", headers=HEADERS).json().get("data", [])
    print(f"  trigger {tp['id']} comments={len(cs)} discuss_done={sum(1 for c in cs if '[DISCUSS-DONE]' in (c.get('content') or ''))}")

roster_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md", headers=HEADERS).json()
print("\nROSTER RAW keys:", list(roster_raw.keys())[:10])
roster = parse_frontmatter(roster_raw).get("teams", {}) or {}
print("TEAMS:", json.dumps({k: {"ws": v.get("workspace_id"), "members": v.get("members")} for k,v in roster.items()}, indent=1)[:3000])
