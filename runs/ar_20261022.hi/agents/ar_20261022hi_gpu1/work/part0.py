import json, os, requests, yaml
from pathlib import Path

AGENT_NAME = "ar_20261022hi_gpu1"
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

print("=== A2: recent posts ===")
recent = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=30", headers=HEADERS).json().get("data", [])
print("n_posts:", len(recent))
for p in recent[:12]:
    print(" ", p.get("id"), "|", p.get("title"), "|", p.get("created_at") or p.get("createdAt"))

trigs = [p for p in recent if "[DISCUSSION-TRIGGER]" in p.get("title","")]
print("triggers:", [(t["id"], t["title"]) for t in trigs])

print("=== B: roster ===")
roster_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md", headers=HEADERS).json()
print("roster raw keys:", list(roster_raw.keys())[:8])
print("status:", roster_raw.get("error") or "ok")
fm = parse_frontmatter(roster_raw)
print("frontmatter:", json.dumps(fm, default=str)[:1500])

print("=== champion.md ===")
champ_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/champion.md", headers=HEADERS).json()
champ = parse_frontmatter(champ_raw)
print("version:", champ_raw.get("version"))
print(json.dumps(champ, default=str)[:800])

print("=== Check C: result_latest ===")
p = AGENT_DIR / "workspace/result_latest.json"
print("exists:", p.exists())
print("=== workspace files (main) ===")
mf = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files", headers=HEADERS).json()
for f in mf.get("files", []):
    print(" ", f.get("path"), f.get("version"))
