import json, requests, yaml
from datetime import datetime, timezone
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu2"; TEAM_WS_ID="005cb9ec-6fce-4bba-9340-21c08ab914c5"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": AGENT_NAME}
API="http://localhost:3000/api/v1"
q = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=H).json()
fm = yaml.safe_load(q.get("content","").split("---")[1])
now = datetime.now(timezone.utc)
for it in fm["pending"]:
    pid = it.get("proposal_post"); created=None; ncomments=None
    if pid:
        p = requests.get(f"{API}/posts/{pid}", headers=H).json()
        created = p.get("createdAt") or p.get("created_at")
        cs = requests.get(f"{API}/posts/{pid}/comments", headers=H).json().get("data",[])
        ncomments = len(cs)
    age = None
    if created:
        age = (now - datetime.fromisoformat(created.replace("Z","+00:00"))).total_seconds()/60
    print(f"{it['id']:30s} discussion_pending={it.get('discussion_pending')} created={created} age_min={age if age is None else round(age,1)} comments={ncomments}")
