import json, os, requests
from pathlib import Path
AGENT_NAME = "ar_20261022hi_gpu5"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
creds = json.load(open(Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")/"credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
st = json.load(open("/tmp/part0_state.json")); TEAM_WS_ID = st["TEAM_WS_ID"]
for p in ["dead_ends.md","strategy.md","knowledge/axis_priors.md","knowledge/noise_floor.md","knowledge/baseline_coverage.md"]:
    r = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/{p}", headers=HEADERS).json()
    print(f"\n{'='*20} {p} v{r.get('version')} {'='*20}")
    print(r.get("content","")[:4000])
