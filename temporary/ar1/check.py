import json, os, requests
from pathlib import Path
FOCUS=Path("/root/autodl-tmp/ar_20261022.hi")
creds=json.load(open(FOCUS/"agents/ar_20261022hi_analyst1/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name")}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN=open(FOCUS/"WORKSPACE_ID").read().strip()
print("=== current main file list ===")
r=requests.get(f"{API}/workspaces/{MAIN}/files",headers=H).json()
for f in r.get("files",[]):
    print(f"  {f['path']:<45} v{f.get('version')} {f.get('updatedAt','')[:19]}")
print("\n=== try version history ===")
for q in ["?version=2","?version=1","/history","/versions"]:
    rr=requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/noise_floor_data.md{q}",headers=H)
    print(q, rr.status_code, (rr.text or "")[:200].replace("\n"," "))
print("\n=== search main for same-code seed pairs ===")
for kw in ["seed_values","seed 43","same-code","noise_floor"]:
    try:
        s=requests.get(f"{API}/workspaces/{MAIN}/search?q={kw}",headers=H).json()
        res=s.get("results",[])
        print(kw, "->", [x.get("path") for x in res][:8])
    except Exception as e:
        print(kw,"ERR",e)
