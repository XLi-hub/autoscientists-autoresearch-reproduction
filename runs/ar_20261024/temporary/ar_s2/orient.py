import json, os, requests, yaml
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"; AGENT_NAME="ar_20261024_analyst2"
AGENT_DIR=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds=json.load(open(AGENT_DIR/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN_WS_ID=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
TEAM_WS_ID="005cb9ec-6fce-4bba-9340-21c08ab914c5"
def pfm(resp):
    c=resp.get("content","") ; parts=c.split("---")
    return yaml.safe_load(parts[1]) if len(parts)>=3 else {}
def get(ws,path):
    return requests.get(f"{API}/workspaces/{ws}/files/{path}",headers=HEADERS).json()

print("="*30,"CHAMPION.MD","="*30)
champ_raw=get(MAIN_WS_ID,"champion.md"); print(champ_raw.get("content","")[:2000]); print("version",champ_raw.get("version"))
print("="*30,"MAIN FILES","="*30)
mf=requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files",headers=HEADERS).json().get("files",[])
for f in sorted(mf,key=lambda x:x.get("updatedAt","")):
    print(f'{f["path"]:55s} v{f.get("version")} {f.get("updatedAt")}')
print("="*30,"TEAM FILES","="*30)
tf=requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files",headers=HEADERS).json().get("files",[])
for f in sorted(tf,key=lambda x:x.get("updatedAt","")):
    print(f'{f["path"]:55s} v{f.get("version")} {f.get("updatedAt")}')
print("="*30,"POSTS","="*30)
posts=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=60",headers=HEADERS).json().get("data",[])
for p in posts:
    print(f'{p.get("createdAt")} | {p.get("id")} | {p.get("title")} | tags={p.get("tags")}')
