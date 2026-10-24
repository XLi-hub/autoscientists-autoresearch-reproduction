import json, os, requests, yaml
from pathlib import Path
AGENT_NAME = "ar_20261022hi_gpu5"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
def pf(resp):
    c = resp.get("content","")
    p = c.split("---")
    return yaml.safe_load(p[1]) if len(p)>=3 else {}

st = json.load(open("/tmp/part0_state.json"))
TEAM_WS_ID = st["TEAM_WS_ID"]

print("=== CHAMPION ===")
champ_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/champion.md", headers=HEADERS).json()
print("version:", champ_raw.get("version"))
print(champ_raw.get("content","")[:3000])

print("\n=== TEAM FILES (capacity) ===")
tf = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files", headers=HEADERS).json().get("files",[])
for f in tf: print(f.get("path"), "v", f.get("version"), f.get("updatedAt"))

print("\n=== QUEUE ===")
q_raw = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=HEADERS).json()
print("version:", q_raw.get("version"))
print(q_raw.get("content","")[:6000])
