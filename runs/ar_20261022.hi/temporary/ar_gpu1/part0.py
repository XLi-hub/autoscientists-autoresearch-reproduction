import json, os, re, yaml, requests
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_gpu1"
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

# A2: discussion trigger
recent = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=30", headers=HEADERS).json().get("data", [])
print("recent posts:", len(recent))
trigger_posts = [p for p in recent if "[DISCUSSION-TRIGGER]" in p.get("title","")]
print("trigger posts:", [(p['id'], p['title'][:80]) for p in trigger_posts])
DONE_NEEDED = 5
active_trigger = None
if trigger_posts:
    t = trigger_posts[0]
    comments = requests.get(f"{API}/posts/{t['id']}/comments", headers=HEADERS).json().get("data", [])
    done = [c for c in comments if "[DISCUSS-DONE]" in str(c.get("content",""))]
    print(f"trigger {t['id']}: comments={len(comments)} discuss-done={len(done)}")
    if len(done) < DONE_NEEDED:
        active_trigger = t

print("ACTIVE_TRIGGER:", bool(active_trigger))

# B: roster
r = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md", headers=HEADERS)
print("roster status:", r.status_code)
roster_raw = r.json() if r.ok else {}
roster = parse_frontmatter(roster_raw).get("teams", {}) or {}
print("teams:", list(roster.keys()))
MY_TEAM = TEAM_WS_ID = None
for name, t in roster.items():
    if AGENT_NAME in t.get("members", []):
        MY_TEAM = name; TEAM_WS_ID = t["workspace_id"]
print("MY_TEAM:", MY_TEAM, "TEAM_WS_ID:", TEAM_WS_ID)

# C: pending result
_agent_md = (AGENT_DIR / "AGENT.md").read_text()
_m = re.search(r"^role:\s*(\S+)", _agent_md, re.MULTILINE)
MY_ROLE = _m.group(1).strip() if _m else "unknown"
print("MY_ROLE:", MY_ROLE)
pending_path = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace/result_latest.json")
pending_result = json.loads(pending_path.read_text()) if pending_path.exists() else None
print("pending result:", json.dumps(pending_result, indent=2)[:1200] if pending_result else None)

def _alive(pid):
    try: os.kill(int(pid), 0); return True
    except Exception: return False

json.dump({"active_trigger": active_trigger['id'] if active_trigger else None,
           "MY_TEAM": MY_TEAM, "TEAM_WS_ID": TEAM_WS_ID,
           "MY_ROLE": MY_ROLE, "roster": roster},
          open("/tmp/ar_gpu1/part0.json","w"), indent=2)
