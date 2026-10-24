import json, os, requests, yaml
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"; AGENT_NAME="ar_20261024_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
TEAM_WS="005cb9ec-6fce-4bba-9340-21c08ab914c5"
print("=== FEED (newest first) ===")
feed=requests.get(f"{API}/workshops/{WORKSHOP}/feed",headers=HEADERS).json()
items = feed.get("data") if isinstance(feed,dict) else feed
if items is None:
    items=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=60",headers=HEADERS).json().get("data",[])
for p in items:
    print(p.get("createdAt"),"|",p.get("id"),"|",p.get("title","")[:110])
print("\n=== QUEUE VERIFY ===")
q=requests.get(f"{API}/workspaces/{TEAM_WS}/files/queue.md",headers=HEADERS).json()
fm=yaml.safe_load(q["content"].split("---")[1])
print("claims",fm.get("claims"))
for it in fm.get("pending",[]):
    print(it["id"],"|",it.get("priority"),"|",it.get("axis"),"|",it.get("direction"),"| dp",it.get("discussion_pending"),"| post",it.get("proposal_post"))
print("\n=== NOTIFICATIONS ===")
n=requests.get(f"{API}/notifications?limit=10",headers=HEADERS).json()
print(json.dumps(n)[:1500])
