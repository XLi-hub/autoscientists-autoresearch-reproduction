import json, yaml, requests
from pathlib import Path
AGENT_NAME = "ar_20261024_gpu9"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
GQ = "005cb9ec-6fce-4bba-9340-21c08ab914c5"

for p in ["knowledge/noise_floor.md", "dead_ends.md"]:
    r = requests.get(f"{API}/workspaces/{GQ}/files/{p}", headers=HEADERS, timeout=30).json()
    print(f"========== {p} (v{r.get('version')}) ==========")
    print(r.get("content","")[:3500])
    print()

print("========== results/exp_gq_matrix_lr_lo.md ==========")
r = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/results/exp_gq_matrix_lr_lo.md", headers=HEADERS, timeout=30).json()
print(r.get("content","")[:4000])
