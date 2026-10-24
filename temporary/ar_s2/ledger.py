import json, os, requests, yaml
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"; AGENT_NAME="ar_20261024_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN_WS_ID=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
r=requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/knowledge/unqueued_axes.md",headers=HEADERS).json()
print("VERSION",r.get("version"))
c=r.get("content","")
i=c.find("| window_pattern |")
print(c[i:i+5000])
