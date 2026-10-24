import json, os, requests, yaml
from pathlib import Path
from datetime import datetime, timezone
AGENT_NAME = "ar_20261022hi_gpu5"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
creds = json.load(open(Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")/"credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
st = json.load(open("/tmp/part0_state.json")); TEAM_WS_ID = st["TEAM_WS_ID"]
q = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=HEADERS).json()
fm = yaml.safe_load(q.get("content","").split("---")[1])
now = datetime.now(timezone.utc)
for it in fm.get("pending") or []:
    pa = it.get("proposed_at")
    age = None
    if pa:
        age = (now - datetime.fromisoformat(pa.replace("Z","+00:00"))).total_seconds()/60
    print(f"- {it.get('id')} | pri={it.get('priority')} | axis={it.get('axis')}/{it.get('direction')}/{it.get('value')}")
    print(f"    disc_pending={it.get('discussion_pending')} age={age if age is None else round(age,1)}min post={it.get('proposal_post')}")
    print(f"    diff: {it.get('diff')}")
    if it.get('proposal_post'):
        cs = requests.get(f"{API}/posts/{it['proposal_post']}/comments", headers=HEADERS).json().get("data",[])
        print(f"    comments={len(cs)}: " + "; ".join(f"{c.get('author')}:{str(c.get('content'))[:90]}" for c in cs[:3]))
