import json, os, requests
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_analyst2"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
def show(pid, label, bodylim=2500):
    r = requests.get(f"{API}/posts/{pid}", headers=HEADERS, timeout=30)
    j = r.json() if r.ok else {}
    print(f"\n##### {label} | {pid} | status {r.status_code}")
    print("TITLE:", j.get("title"))
    print("AUTHOR:", j.get("author"), j.get("author_name"), j.get("agent"))
    print("TAGS:", j.get("tags"))
    print("BODY:", (j.get("content") or "")[:bodylim])
    c = requests.get(f"{API}/posts/{pid}/comments", headers=HEADERS, timeout=30)
    comments = c.json().get("data", []) if c.ok else []
    print(f"COMMENTS ({len(comments)}):")
    for x in comments:
        print("  -", x.get("author") or x.get("agent_name") or x.get("agent"), "|", (x.get("content") or "")[:300].replace("\n"," "))
show("14908204-ef10-4a91-9234-d47ad171281c","exp_batch_2e16 proposal")
show("76745351-264c-41b1-a158-1a32c07a972c","adam_beta2 (mine)")
show("d52b1379-db14-4f47-adff-693fc56e76cd","embedding_lr (mine)")
show("d2a434dd-d5ad-4a81-968d-873ccaecf35a","weight_decay bracket",1500)
show("e1ae7b90-a177-41ea-96e7-92cb1cb326a3","aspect_ratio bracket",1200)
print("\n##### NOTIFICATIONS")
n = requests.get(f"{API}/notifications?limit=15", headers=HEADERS, timeout=30)
print(json.dumps(n.json(), indent=1)[:3000] if n.ok else n.text[:500])
