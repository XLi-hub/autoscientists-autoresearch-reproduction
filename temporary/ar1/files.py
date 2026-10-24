import json, os, requests
from pathlib import Path
FOCUS=Path("/root/autodl-tmp/ar_20261022.hi")
creds=json.load(open(FOCUS/"agents/ar_20261022hi_analyst1/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name")}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN=open(FOCUS/"WORKSPACE_ID").read().strip()
def ls(ws,label):
    r=requests.get(f"{API}/workspaces/{ws}/files",headers=HEADERS).json()
    print(f"=== {label} ({ws[:8]}) ===")
    for f in r.get("files",[]):
        print(f"  {f['path']:<55} v{f.get('version')} {f.get('updatedAt','')[:19]}")
ls(MAIN,"MAIN")
# team ws ids from roster via file
rr=requests.get(f"{API}/workspaces/{MAIN}/files/teams/roster.md",headers=HEADERS).json()
print("---roster raw head---")
print(rr.get("content","")[:1500])
