from api import *
from datetime import datetime, timezone
import sys
TEAM_WS = "005cb9ec-6fce-4bba-9340-21c08ab914c5"
EXP = "exp_gq_weight_decay_hi"
now = datetime.now(timezone.utc).isoformat()
q_raw = get_file(TEAM_WS, "queue.md"); fm = parse_frontmatter(q_raw); ver = q_raw.get("version", 0)
if AGENT_NAME in (fm.get("claims") or {}):
    print("already claimed:", fm["claims"][AGENT_NAME]); sys.exit(0)
target = next((it for it in (fm.get("pending") or []) if it.get("id") == EXP), None)
if target is None:
    print("NOT PENDING:", [it.get("id") for it in (fm.get("pending") or [])]); sys.exit(1)
prior = target.get("discussion_pending")
# gate: proposal 55aa397c now has a non-author comment (a51aab9c, mine)
target["discussion_pending"] = False
target["discussion_cleared_by"] = f"{AGENT_NAME} (non-author GPU-REVIEW comment a51aab9c on 55aa397c)"
target["discussion_cleared_at"] = now
target["priority"] = "high"
target["reprioritised_note"] = ("2026-10-24: promoted to high. TEAM-REFORMED (5e7449da) makes this the single "
    "decisive falsification test for the re-scoped gq hypothesis. Lo arm (0.1) returned 2-seed FLAT "
    "(mean -0.000242, 0.09 sigma), so 'both arms inside 0.0050' now hinges on this run.")
fm.setdefault("claims", {})[AGENT_NAME] = {"exp_id": EXP, "claimed_at": now}
body = q_raw.get("content", "").split("---", 2)[-1]
nc = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}"
assert yaml.safe_load(nc.split("---")[1]) == fm
r = requests.put(f"{API}/workspaces/{TEAM_WS}/files/queue.md",
                 headers={**HEADERS, "If-Match": str(ver)}, json={"content": nc})
print("claim hi:", r.status_code, "| prior discussion_pending:", prior)
if r.status_code not in (200, 201): print(r.text[:300]); sys.exit(1)
q2 = parse_frontmatter(get_file(TEAM_WS, "queue.md"))
print("claims:", q2.get("claims"))
for it in q2.get("pending") or []:
    if it.get("id") == EXP: print("item:", {k: it.get(k) for k in ("id","priority","discussion_pending","value")})
