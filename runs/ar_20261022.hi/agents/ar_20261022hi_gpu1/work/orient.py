import json, os, requests, yaml
from pathlib import Path

AGENT_NAME = "ar_20261022hi_gpu1"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": AGENT_NAME}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
TEAM_WS_ID = "54202fe1-b766-43f1-b374-9e4ed188c153"

def parse_frontmatter(resp):
    content = resp.get("content", "")
    parts = content.split("---")
    return yaml.safe_load(parts[1]) if len(parts) >= 3 else {}

print("=== MAIN files ===")
for f in requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files", headers=HEADERS).json().get("files", []):
    print("  ", f.get("path"), "v", f.get("version"))

print("=== baseline_lock ===")
r = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/baseline_lock.md", headers=HEADERS)
print("status", r.status_code, str(r.json())[:300] if r.ok else r.text[:200])

print("\n=== TEAM files ===")
tf = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files", headers=HEADERS).json()
for f in tf.get("files", []):
    print("  ", f.get("path"), "v", f.get("version"), f.get("updatedAt"))

for name in ("queue.md", "strategy.md", "dead_ends.md"):
    rr = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/{name}", headers=HEADERS)
    print(f"\n===== {name} (HTTP {rr.status_code}, v{rr.json().get('version')}) =====")
    if rr.ok:
        c = rr.json().get("content","")
        print(c[:3000])

print("\n=== posts full ===")
recent = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=30", headers=HEADERS).json().get("data", [])
for p in recent:
    print("\n---", p.get("id"), p.get("title"))
    detail = requests.get(f"{API}/posts/{p['id']}", headers=HEADERS).json()
    print((detail.get("content") or "")[:1500])
    cs = requests.get(f"{API}/posts/{p['id']}/comments", headers=HEADERS).json().get("data", [])
    print("  comments:", len(cs))
    for c in cs:
        print("   *", c.get("author"), ":", (c.get("content") or "")[:300])
