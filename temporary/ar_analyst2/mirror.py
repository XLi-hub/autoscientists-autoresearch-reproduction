import json, os, requests
AGENT_NAME="ar_20261024_analyst2"; FOCUS_ROOT="/root/autodl-tmp/ar_20261024"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
WS=os.environ.get("MAIN_WS_ID","e14269b7-8ec4-4e74-947b-da7ee1484524")
path=f"{FOCUS_ROOT}/agents/{AGENT_NAME}/AGENT.md"
content=open(path).read()
url=f"{API}/workspaces/{WS}/files/agents/{AGENT_NAME}.md"
r=requests.get(url,headers=HEADERS)
ver=None
if r.status_code==200:
    j=r.json()
    d=j.get("file",j) if isinstance(j,dict) else {}
    ver=d.get("version") or d.get("version_number")
    print("existing version:",ver)
else:
    print("GET",r.status_code,r.text[:200])
h=dict(HEADERS)
if ver is not None: h["If-Match"]=str(ver)
r=requests.put(url,headers=h,json={"content":content})
print("PUT",r.status_code,r.text[:300])
