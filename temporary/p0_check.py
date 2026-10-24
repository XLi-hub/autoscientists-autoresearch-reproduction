import json, os, requests, yaml
from pathlib import Path
from datetime import datetime, timezone

FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_analyst3"
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

print("API", API, "MAIN_WS", MAIN_WS_ID, "WORKSHOP", WORKSHOP)
# Check A2: recent posts
r = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=30", headers=HEADERS, timeout=20)
print("posts status", r.status_code)
posts = r.json().get("data", [])
print("n posts", len(posts))
for p in posts[:30]:
    print(p.get("createdAt") or p.get("created_at"), "|", p.get("id"), "|", p.get("title","")[:110])
