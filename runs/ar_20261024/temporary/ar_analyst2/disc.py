import json, os, requests
AGENT_NAME="ar_20261024_analyst2"; FOCUS_ROOT="/root/autodl-tmp/ar_20261024"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip(); WS=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
for pid in ["c5e890d8-f63a-41e8-923a-91aa41b3fecc","263b1836-bd64-46d9-b8e6-870648ac6ed0","e3233fc5-6fe5-4390-a6d8-fdb85fe91e6d","32774936-fd8e-4501-96ea-daa4157c2d0f","22ce8a28-3710-48e6-94a0-efaacf3458a0"]:
    r=requests.get(f"{API}/posts/{pid}",headers=HEADERS).json()
    print("\n"+"="*100); print("POST",pid,"|",r.get("title")); print(r.get("content","")[:2600])
    c=requests.get(f"{API}/posts/{pid}/comments",headers=HEADERS).json().get("data",[])
    for cm in c: print("  COMMENT:",cm.get("content","")[:800])
