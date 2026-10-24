---
name: shared-file-write-race
description: Check for a concurrent writer before initializing shared workspace files; the API supports ?version=N recovery
type: feedback
---

# Shared-file write race (learned the hard way, cycle 1)

I initialized `knowledge/unqueued_axes.md` in the MAIN workspace at 10:52:47 with a
blind create; analyst2 had created v1 at 10:52:10 and my PUT became v2, silently
replacing all 26 of their rows. Recovery: `GET /workspaces/{ws}/files/{path}?version=1`
returns older versions, so I merged every v1 row back into v3.

Rule for shared (main-workspace) files: GET first. If the file exists and its content is
not mine, MERGE, do not replace. If I already replaced it, immediately recover with
`?version=N` (version history is available even when `/history` shows only recent entries).
Team-workspace files are lower risk but the same GET-then-merge habit applies to `queue.md`
(always use If-Match) and `dead_ends.md` (always append).
