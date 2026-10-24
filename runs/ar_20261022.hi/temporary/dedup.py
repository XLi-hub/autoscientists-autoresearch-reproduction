import json, os, requests
from pathlib import Path
AGENT_NAME = "ar_20261022hi_gpu5"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
creds = json.load(open(Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")/"credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
mf = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files", headers=HEADERS).json().get("files",[])
print("MAIN WS FILES:")
for f in mf: print(" ", f.get("path"), "v", f.get("version"))
for kw in ["head_dim","HEAD_DIM"]:
    r = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/search?q={kw}", headers=HEADERS).json()
    print(f"\nSEARCH {kw}:", [h.get("path") for h in r.get("results",[])])
