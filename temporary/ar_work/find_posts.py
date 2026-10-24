import json, os, requests
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_analyst2"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
recent = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=12", headers=HEADERS, timeout=30).json()
print(json.dumps(recent, indent=1)[:600])
for p in recent.get("data", [])[:10]:
    print(p.get("id"), "|", p.get("createdAt") or p.get("created_at"), "|", p.get("title")[:100], "| author:", p.get("author") or p.get("author_name") or p.get("authorName"))
