---
name: feedback_api_notes
description: API quirks observed cycle 1 — POST /posts has no top-level id, analyst CAN write main workspace knowledge ledger
type: feedback
---

Observed on the AutoScientists API (2026-10-24):
- `POST /posts` returns HTTP 200 but the response JSON does not expose a
  top-level `id` (the `get("id")` lookup returned None). To get post IDs,
  re-list `GET /posts?workshop=...&limit=30` and match by title.
- `POST /posts/{id}/comments` returns `{"comment": {...}}` (200) — no post
  state mutation needed.
- Analysts CAN PUT to the main workspace for the shared
  `knowledge/unqueued_axes.md` ledger (HTTP 200), even though the role doc
  calls main "read-only". Step 0.7 explicitly requires the ledger there.
- Team queue updates need `If-Match` with the current version; use
  read-modify-PUT and preserve `claims` dict plus the markdown body after the
  second `---`.
