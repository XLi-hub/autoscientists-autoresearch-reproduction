import json, requests
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"
for pid in ["a1018d68-44ba-4f45-aff9-b27e246ec223","3292d69f","d913abef"]:
    # find full id if short
    if len(pid)<20:
        r=requests.get(f"{API}/posts?limit=100",headers=HEADERS)
        pass
    p=requests.get(f"{API}/posts/{pid}",headers=HEADERS)
    print("="*100); print(pid,"status",p.status_code)
    if p.ok:
        d=p.json()
        print("TITLE:", d.get("title"))
        print("CREATED:", d.get("createdAt"), "UPDATED:", d.get("updatedAt"))
        print(str(d.get("content",""))[:3000])
        cs=requests.get(f"{API}/posts/{pid}/comments",headers=HEADERS).json().get("data",[])
        print(f"-- comments ({len(cs)}) --")
        for c in cs:
            print("*", c.get("author"), ":", str(c.get("content",""))[:600])
