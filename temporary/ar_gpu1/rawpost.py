import json, requests
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"
p=requests.get(f"{API}/posts/a1018d68-44ba-4f45-aff9-b27e246ec223",headers=H).json()
print(json.dumps({k:(v if k!='content' else str(v)[:200]) for k,v in p.items()},indent=2,default=str))
