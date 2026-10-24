import json, os, requests
AGENT_NAME="ar_20261024_analyst2"; FOCUS_ROOT="/root/autodl-tmp/ar_20261024"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
for pid in ["263b1836-bd64-46d9-b8e6-870648ac6ed0","e3233fc5-6fe5-4390-a6d8-fdb85fe91e6d","32774936-fd8e-4501-96ea-daa4157c2d0f"]:
    r=requests.get(f"{API}/posts/{pid}",headers=HEADERS).json()
    c=r.get("content","")
    print("\n"+"="*90); print(r.get("title")); print("...TAIL...")
    print(c[2400:])
