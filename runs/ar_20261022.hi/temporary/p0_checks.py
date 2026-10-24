import json, os, requests, yaml
from pathlib import Path

AGENT_NAME = "ar_20261022hi_gpu4"
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

print("API:", API, "WS:", MAIN_WS_ID, "WORKSHOP:", WORKSHOP)

# --- Check A2: discussion trigger ---
recent = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=30", headers=HEADERS).json().get("data", [])
print(f"\n=== A2: {len(recent)} recent posts ===")
for p in recent[:30]:
    print(f"  {p.get('createdAt','?')[:19]} | {p.get('author','?')[:22]:22} | {p.get('title','')[:95]}")
triggers = [p for p in recent if "[DISCUSSION-TRIGGER]" in p.get("title","")]
print(f"\nDISCUSSION-TRIGGER posts: {len(triggers)}")
for t in triggers:
    comments = requests.get(f"{API}/posts/{t['id']}/comments", headers=HEADERS).json().get("data", [])
    done = [c for c in comments if "[DISCUSS-DONE]" in str(c.get("content",""))]
    more = [c for c in comments if "[DISCUSS-MORE]" in str(c.get("content",""))]
    print(f"  {t['title'][:80]} | comments={len(comments)} DONE={len(done)} MORE={len(more)}")

# --- Check B: roster ---
roster_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md", headers=HEADERS).json()
roster = parse_frontmatter(roster_raw).get("teams", {}) or {}
print(f"\n=== B: roster ({len(roster)} teams) ===")
MY_TEAM = TEAM_WS_ID = None
ALL = {}
for name, t in roster.items():
    ALL[name] = t["workspace_id"]
    print(f"  {name}: ws={t['workspace_id']} members={t.get('members')}")
    if AGENT_NAME in t.get("members", []):
        MY_TEAM, TEAM_WS_ID = name, t["workspace_id"]
print(f"\nMY_TEAM={MY_TEAM} TEAM_WS_ID={TEAM_WS_ID}")
json.dump({"MY_TEAM": MY_TEAM, "TEAM_WS_ID": TEAM_WS_ID, "ALL": ALL}, open("/tmp/p0_state.json","w"))
