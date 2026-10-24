import json, os, re, yaml, requests
from pathlib import Path

AGENT_NAME = "ar_20261024_gpu9"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()

def parse_frontmatter(resp):
    content = resp.get("content", "") if isinstance(resp, dict) else ""
    parts = content.split("---")
    return yaml.safe_load(parts[1]) if len(parts) >= 3 else {}

print("=== CHECK A2: discussion triggers ===")
recent = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=30", headers=HEADERS, timeout=30).json().get("data", [])
print(f"recent posts: {len(recent)}")
for p in recent[:10]:
    print(" ", p.get("createdAt") or p.get("created_at"), "|", p.get("title","")[:100])
triggers = [p for p in recent if "[DISCUSSION-TRIGGER]" in p.get("title","")]
print(f"triggers found: {len(triggers)}")

print("\n=== CHECK B: roster ===")
roster_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md", headers=HEADERS, timeout=30).json()
roster = parse_frontmatter(roster_raw).get("teams", {}) or {}
MY_TEAM = TEAM_WS_ID = None
ALL_TEAM_WS_IDS = {}
for name, t in roster.items():
    ALL_TEAM_WS_IDS[name] = t["workspace_id"]
    if AGENT_NAME in t.get("members", []):
        MY_TEAM = name; TEAM_WS_ID = t["workspace_id"]
print(f"teams: {list(roster.keys())}")
print(f"MY_TEAM={MY_TEAM} TEAM_WS_ID={TEAM_WS_ID}")

print("\n=== CHECK C: pending result ===")
_agent_md = (AGENT_DIR / "AGENT.md").read_text() if (AGENT_DIR/"AGENT.md").exists() else ""
_m = re.search(r"^role:\s*(\S+)", _agent_md, re.MULTILINE)
MY_ROLE = _m.group(1).strip() if _m else "unknown"
print("MY_ROLE =", MY_ROLE)
pending_path = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace/result_latest.json")
print("result_latest.json exists:", pending_path.exists())
if pending_path.exists():
    print(pending_path.read_text()[:1500])
