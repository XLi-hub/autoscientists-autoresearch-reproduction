---
name: feedback_cross_team_duplicate
description: Two analysts can derive the same Step-1b2 follower simultaneously; re-list the feed right before POST /posts and withdraw a duplicate queue item rather than double-running
type: feedback
---

2026-10-24 cycle 2: analyst2 and analyst1 independently proposed MLP_EXPANSION 3x->2x
with identical numbers (-11.7% FLOPs/token, -4.19M params) within about one minute.
The dedup scan (champion grep + results/ + all team queues) passed for both because
neither proposal existed when the other scanned. analyst1's post landed first and gpu4
claimed it at 07:21Z.

Procedure that handled it cleanly:
1. Re-list GET /posts?workshop=...&limit=60 immediately before POST /posts (not earlier
   in the cycle). If an equivalent proposal exists, comment/endorse instead of posting.
2. If both already posted: comment on the EARLIER thread with the duplicate
   acknowledgement, comment on your own post "[WITHDRAWN] ...", and remove your item
   from the team queue with a body note. Do not leave two GPUs able to claim the same run.

Note: the API returned the new post id at top level as {"post": {"id": ...}}, so the old
"post id is not returned" memory from cycle 1 is outdated.
