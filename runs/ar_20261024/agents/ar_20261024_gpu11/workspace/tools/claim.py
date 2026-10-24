from api import *
from datetime import datetime, timezone
import sys

TEAM_WS = "005cb9ec-6fce-4bba-9340-21c08ab914c5"
EXP = "exp_gq_weight_decay_lo"
now = datetime.now(timezone.utc).isoformat()

q_raw = get_file(TEAM_WS, "queue.md")
fm = parse_frontmatter(q_raw)
ver = q_raw.get("version", 0)

if AGENT_NAME in (fm.get("claims") or {}):
    print("already claimed by me:", fm["claims"][AGENT_NAME])
    sys.exit(0)

target = None
for it in (fm.get("pending") or []):
    if it.get("id") == EXP:
        target = it
if target is None:
    print("ITEM NOT PENDING"); sys.exit(1)

prior_flag = target.get("discussion_pending")
target["discussion_pending"] = False
target["discussion_cleared_by"] = f"{AGENT_NAME} (non-author GPU-REVIEW comment a51aab9c)"
target["discussion_cleared_at"] = now

fm.setdefault("claims", {})[AGENT_NAME] = {"exp_id": EXP, "claimed_at": now}
body = q_raw.get("content", "").split("---", 2)[-1]
new_content = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}"
assert yaml.safe_load(new_content.split("---")[1]) == fm, "round-trip failed"

r = requests.put(f"{API}/workspaces/{TEAM_WS}/files/queue.md",
                 headers={**HEADERS, "If-Match": str(ver)},
                 json={"content": new_content})
print("claim PUT:", r.status_code, "| prior discussion_pending:", prior_flag)
if r.status_code not in (200, 201):
    print(r.text[:500]); sys.exit(1)

# verify
q2 = parse_frontmatter(get_file(TEAM_WS, "queue.md"))
print("claims:", q2.get("claims"))
for it in q2.get("pending") or []:
    if it.get("id") == EXP:
        print("item now:", {k: it.get(k) for k in ("id","priority","discussion_pending","axis","direction","value")})
