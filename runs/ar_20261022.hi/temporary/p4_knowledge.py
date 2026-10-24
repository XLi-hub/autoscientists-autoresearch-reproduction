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
TEAM_WS_ID = "3a33313e-18ff-4e17-9c47-66b54cfe576d"
def get(ws, path):
    return requests.get(f"{API}/workspaces/{ws}/files/{path}", headers=HEADERS, timeout=20).json()

for path, label in [("strategy.md","TEAM STRATEGY"),("dead_ends.md","TEAM DEAD_ENDs"),
                    ("knowledge/baseline_coverage.md","TEAM BASELINE COVERAGE"),
                    ("knowledge/axis_priors.md","TEAM AXIS PRIORS"),
                    ("knowledge/noise_floor.md","TEAM NOISE FLOOR")]:
    r = get(TEAM_WS_ID, path)
    print(f"\n===== {label} (v{r.get('version')}) =====")
    print(r.get("content","")[:4500])

print("\n===== MAIN noise_floor.md =====")
print(get(MAIN_WS_ID,"knowledge/noise_floor.md").get("content","")[:2500])
print("\n===== MAIN noise_floor_data.md =====")
print(get(MAIN_WS_ID,"knowledge/noise_floor_data.md").get("content","")[:2500])
