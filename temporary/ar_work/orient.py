import json, os, yaml, requests
from pathlib import Path
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_analyst2"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAM_WS_ID = "032e5282-1362-4eef-9226-3d40299116aa"
def pf(resp):
    c = resp.get("content",""); p=c.split("---")
    return yaml.safe_load(p[1]) if len(p)>=3 else {}
def getfile(ws, path):
    r = requests.get(f"{API}/workspaces/{ws}/files/{path}", headers=HEADERS, timeout=30)
    return r.json() if r.ok else {"content": f"<<404 {r.status_code}>>"}

print("=== CHAMPION.MD ==="); print(getfile(MAIN_WS_ID,"champion.md").get("content","")[:2000])
for f in ["queue.md","strategy.md","dead_ends.md"]:
    print(f"\n=== TEAM {f} ==="); print(getfile(TEAM_WS_ID,f).get("content","")[:3500])
print("\n=== MAIN FILES ===")
mf = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files", headers=HEADERS, timeout=30).json().get("files",[])
for f in mf: print(f["path"], "| v", f.get("version"), "|", f.get("updatedAt"))
print("\n=== TEAM FILES ===")
tf = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files", headers=HEADERS, timeout=30).json().get("files",[])
for f in tf: print(f["path"], "| v", f.get("version"), "|", f.get("updatedAt"))
