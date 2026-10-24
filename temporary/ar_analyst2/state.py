import json, os, requests, yaml
AGENT_NAME="ar_20261024_analyst2"; FOCUS_ROOT="/root/autodl-tmp/ar_20261024"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN_WS_ID=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
def pf(r):
    c=r.get("content",""); p=c.split("---")
    return yaml.safe_load(p[1]) if len(p)>=3 else {}
def get(ws,path):
    return requests.get(f"{API}/workspaces/{ws}/files/{path}",headers=HEADERS).json()
roster_raw=get(MAIN_WS_ID,"teams/roster.md")
roster=pf(roster_raw)
print("### ROSTER ###"); print(json.dumps(roster,indent=1)[:3000])
print("\n### CHAMPION.MD ###"); print(get(MAIN_WS_ID,"champion.md").get("content","")[:3000])
print("\n### MAIN FILES ###")
for f in requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files",headers=HEADERS).json().get("files",[]):
    print(f" {f.get('path')}  v{f.get('version')}  {f.get('updated_at')}")
