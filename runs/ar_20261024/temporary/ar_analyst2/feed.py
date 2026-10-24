import json, os, requests
AGENT_NAME="ar_20261024_analyst2"
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN_WS_ID=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
print("WORKSHOP",WORKSHOP,"MAIN",MAIN_WS_ID)
r=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=60",headers=HEADERS)
print("status",r.status_code)
posts=r.json().get("data",[])
print("N posts",len(posts))
for p in posts:
    print("="*100)
    print("ID:",p.get("id"),"| AUTHOR:",p.get("agent_name") or p.get("author"),"| AT:",p.get("created_at"))
    print("TITLE:",p.get("title"))
    print("TAGS:",p.get("tags"))
    c=requests.get(f"{API}/posts/{p['id']}/comments",headers=HEADERS).json().get("data",[])
    print(f"COMMENTS: {len(c)}")
    for cm in c:
        print(f"  -- [{cm.get('agent_name') or cm.get('author')} @ {cm.get('created_at')}] {cm.get('content','')[:1400]}")
