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
TEAM_WS_ID = "005cb9ec-6fce-4bba-9340-21c08ab914c5"  # gradient-quality

def fm(resp):
    c = resp.get("content","")
    parts = c.split("---")
    return yaml.safe_load(parts[1]) if len(parts)>=3 else {}

print("=== baseline_lock.md ===")
r = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/baseline_lock.md", headers=HEADERS)
print(r.status_code, r.text[:500])

print("\n=== team files ===")
tf = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files", headers=HEADERS).json()
print(json.dumps(tf, indent=2)[:2500])

for fname in ("queue.md","strategy.md","dead_ends.md"):
    rr = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/{fname}", headers=HEADERS)
    print(f"\n=== {fname} (HTTP {rr.status_code}, v={rr.json().get('version') if rr.ok else '?'}) ===")
    if rr.ok:
        print(rr.json().get("content","")[:4000])
