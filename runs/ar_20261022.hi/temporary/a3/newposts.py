import json, requests
FR="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FR}/agents/ar_20261022hi_analyst3/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds["agent_name"]}
API="http://localhost:3000/api/v1"; WS=open(f"{FR}/WORKSHOP_NAME").read().strip()
for pid in ["a935d3ee-27c4-4c97-990d-ea1a1a090e88","3292d69f-4c8b-4775-b06e-9029139b7ac3","d913abef-8c5c-4b65-9fc3-daf38b478722"]:
    d=requests.get(f"{API}/posts/{pid}",headers=H).json()
    c=requests.get(f"{API}/posts/{pid}/comments",headers=H).json().get("data",[])
    print("\n"+"="*78)
    print(d.get("title"))
    print((d.get("content") or "")[:2600])
    print(f"--- comments: {len(c)}")
    for x in c: print("  *",(x.get("content") or "")[:400].replace("\n"," "))
