import json, os, requests
AGENT_NAME="ar_20261024_analyst2"; FOCUS_ROOT="/root/autodl-tmp/ar_20261024"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
WS=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
posts=requests.get(f"{API}/posts?workshop={WS}&limit=6",headers=HEADERS).json().get("data",[])
for p in posts[:2]:
    full=requests.get(f"{API}/posts/{p['id']}",headers=HEADERS).json()
    print("\n"+"#"*100); print("ID:",p['id'],"|",p['title']); print(full.get("content",""))
    c=requests.get(f"{API}/posts/{p['id']}/comments",headers=HEADERS).json().get("data",[])
    for cm in c: print("  COMMENT:",cm.get("content","")[:900])
