import json, os, requests, yaml
AGENT_NAME="ar_20261024_analyst2"; FOCUS_ROOT="/root/autodl-tmp/ar_20261024"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN_WS_ID=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAMS={"throughput":"6e6d22a0-cee2-4b39-b6df-799fea80be27",
       "gradient-quality":"005cb9ec-6fce-4bba-9340-21c08ab914c5",
       "capacity":"d7c6f814-aab0-4029-a887-04345d274f9b"}
r=requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files",headers=HEADERS).json()
print("MAIN FILES KEYS:",list(r.keys()))
for f in (r.get("files") or []):
    print("  ",f.get("path"),"v",f.get("version"),f.get("updated_at"))
for t,ws in TEAMS.items():
    print("\n"+"#"*90); print("### TEAM",t,ws)
    lr=requests.get(f"{API}/workspaces/{ws}/files",headers=HEADERS).json()
    for f in (lr.get("files") or []):
        print("  ",f.get("path"),"v",f.get("version"),f.get("updated_at"))
