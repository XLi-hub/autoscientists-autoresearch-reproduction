import json, requests
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_analyst3"
creds=json.load(open(Path(FOCUS_ROOT)/"agents"/AGENT_NAME/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"
posts=requests.get(f"{API}/posts?workshop=ar_ar_20261022hi&limit=200",headers=HEADERS,timeout=30).json().get("data",[])
for p in posts:
    if "mfu_percent" in p.get("title","") or "Discussion-Before-Queuing" in p.get("title",""):
        d=requests.get(f"{API}/posts/{p['id']}",headers=HEADERS,timeout=20).json()
        print("="*20, p["id"], p["title"])
        print((d.get("content") or "")[:1800])
