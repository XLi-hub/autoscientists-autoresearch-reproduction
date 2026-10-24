import json, os, requests
from pathlib import Path
AGENT_NAME = "ar_20261022hi_gpu5"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
creds = json.load(open(Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")/"credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
for p in ["knowledge/noise_floor_data.md","knowledge/patterns.md","knowledge/exhausted.md"]:
    r = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/{p}", headers=HEADERS).json()
    print(f"\n===== {p} v{r.get('version')} =====")
    print(r.get("content","")[:3500])
# proposal post + comments
pid = "f82bbb14-7582-4237-8cb2-9036757640d7"
p = requests.get(f"{API}/posts/{pid}", headers=HEADERS).json()
print("\n===== PROPOSAL head_dim_64 =====")
print(p.get("title"))
print((p.get("content") or "")[:2500])
cs = requests.get(f"{API}/posts/{pid}/comments", headers=HEADERS).json().get("data",[])
print("COMMENTS:", len(cs))
for c in cs: print(" -", c.get("author"), ":", str(c.get("content"))[:600])
