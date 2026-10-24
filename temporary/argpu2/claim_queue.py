import json, requests, yaml
from datetime import datetime, timezone
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu2"
TEAM_WS_ID = "005cb9ec-6fce-4bba-9340-21c08ab914c5"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": AGENT_NAME}
API = "http://localhost:3000/api/v1"

def pf(resp):
    c = resp.get("content",""); parts = c.split("---")
    return yaml.safe_load(parts[1]) if len(parts)>=3 else {}

q_raw = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=HEADERS).json()
print("queue v", q_raw.get("version"))
fm = pf(q_raw)
print("pending:", [it.get("id") for it in (fm.get("pending") or [])])
print("claims:", fm.get("claims"))

target = None
for it in (fm.get("pending") or []):
    if it.get("id") == "exp_gq_muon_mom_098":
        target = it; break
if target is None:
    print("TARGET NOT PENDING — not claiming")
    raise SystemExit

fm.setdefault("claims", {})[AGENT_NAME] = {"exp_id": target["id"], "claimed_at": datetime.now(timezone.utc).isoformat()}
body = q_raw.get("content", "").split("---", 2)[-1]
new_content = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}"
assert yaml.safe_load(new_content.split("---")[1]) == fm
r = requests.put(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md",
                 headers={**HEADERS, "If-Match": str(q_raw.get("version", 0))},
                 json={"content": new_content})
print("PUT", r.status_code, r.text[:300])
