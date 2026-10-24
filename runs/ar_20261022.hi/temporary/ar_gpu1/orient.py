import json, os, yaml, requests
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_gpu1"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
TEAM_WS_ID = json.load(open("/tmp/ar_gpu1/part0.json"))["TEAM_WS_ID"]

def pf(resp):
    c = resp.get("content",""); p = c.split("---")
    return yaml.safe_load(p[1]) if len(p) >= 3 else {}

champ_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/champion.md", headers=HEADERS).json()
print("=== CHAMPION (version", champ_raw.get("version"), ") ===")
print(champ_raw.get("content","")[:3000])

print("\n=== TEAM throughput queue ===")
q_raw = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=HEADERS).json()
print("version:", q_raw.get("version"))
print(q_raw.get("content","")[:4000])

print("\n=== TEAM FILE LIST ===")
tf = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files", headers=HEADERS).json().get("files", [])
for f in tf: print(f)

print("\n=== MAIN WS FILE LIST ===")
mf = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files", headers=HEADERS).json().get("files", [])
for f in mf: print(f)
