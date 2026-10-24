"""Harvest posted [RESULT] files from the workshop into logs/experiments.jsonl.

Pure coordination bookkeeping: reads results/*.md via the API and appends any
experiment that is not already logged. Deduplicates on exp_id.
"""
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from orch_common import API, FOCUS_ROOT, HEADERS, WS_ID, get_file, now_iso, parse_fm

import requests


def jz(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: jz(x) for k, x in v.items()}
    if isinstance(v, list):
        return [jz(x) for x in v]
    return v


def parse_body(text):
    """Fallback for result files written as plain markdown (no YAML frontmatter).

    Several GPU agents write the human-readable report directly; the same
    fields are still present as bold `key: value` lines, so scrape those.
    """
    def find(pattern, cast=str):
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if not m:
            return None
        try:
            return cast(m.group(1))
        except (TypeError, ValueError):
            return None

    rec = {}
    rec["metric_value"] = find(r"val_bpb\s*[=:]\s*\**\s*(-?[0-9.]+)", float)
    if rec["metric_value"] is None:
        # Agents that ran the multi-seed gate report the mean as the headline.
        rec["metric_value"] = find(r"2-seed mean\**?\s*[=:]\s*\**?\s*(-?[0-9.]+)", float)
    rec["outcome"] = find(r"outcome\**?\s*[=:]\s*\**\s*(KEEP|DISCARD|FAILED|BASELINE)", str)
    if rec["outcome"] is None:
        rec["outcome"] = find(r"\bresult\**?\s*[=:]\s*\**\s*(KEEP|DISCARD|FAILED|BASELINE)", str)
    rec["agent"] = find(r"agent\**?\s*[=:]\s*\**?\s*(ar_[A-Za-z0-9_]+)", str)
    rec["axis"] = find(r"\baxis\**?\s*[=:]\s*\**?\s*([a-z0-9_]+)", str)
    if rec["outcome"]:
        rec["outcome"] = rec["outcome"].upper()
    if rec["agent"] and rec["agent"].endswith("_gpu"):
        rec["agent"] = None
    return {k: v for k, v in rec.items() if v is not None}


def main():
    log_path = FOCUS_ROOT / "logs" / "experiments.jsonl"
    seen = set()
    if log_path.exists():
        for raw in log_path.read_text().splitlines():
            if raw.strip():
                try:
                    seen.add(json.loads(raw).get("exp_id"))
                except json.JSONDecodeError:
                    pass

    files = requests.get(f"{API}/workspaces/{WS_ID}/files", headers=HEADERS).json()["files"]
    paths = sorted(f["path"] for f in files if f["path"].startswith("results/"))

    appended = 0
    with open(log_path, "a") as f:
        for p in paths:
            exp_id = Path(p).stem
            if exp_id in seen:
                continue
            content = get_file(WS_ID, p).get("content", "")
            fm = parse_fm(content)
            if not fm:
                fm = parse_body(content)
            if not fm.get("outcome"):
                print(f"[skip] {exp_id}: no parsable outcome")
                continue
            rec = jz(dict(fm))
            rec.setdefault("exp_id", exp_id)
            rec["harvested_at"] = now_iso()
            f.write(json.dumps(rec) + "\n")
            seen.add(exp_id)
            appended += 1
            print(f"[harvest] {exp_id}: {rec.get('outcome')} {rec.get('metric_value')}")

    n = len([l for l in log_path.read_text().splitlines() if l.strip()])
    print(f"\nappended {appended}; experiments.jsonl now has {n} entries")


if __name__ == "__main__":
    main()
