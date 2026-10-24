"""Meta-diagnostics for the autoresearch run's periodic meta-improvement step.

Consumes `logs/experiments.jsonl` (one JSON object per experiment, with at
least an `outcome` field) and returns a Diagnostics object whose boolean
flags map one-to-one onto concrete template edits in the `meta_improve`
hook. Written by the orchestrator as pure coordination tooling.
"""
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Diagnostics:
    has_high_duplicates: bool = False
    has_low_activation: bool = False
    has_slow_propagation: bool = False
    has_low_keep_rate: bool = False
    keep_rate: float = 0.0
    n_experiments: int = 0
    n_keeps: int = 0
    recent_axes: list = field(default_factory=list)
    notes: list = field(default_factory=list)


def analyze_experiments(experiments_file, last_n=30, num_analysts=3):
    path = Path(experiments_file)
    if not path.exists():
        return Diagnostics(notes=["no experiments.jsonl yet"])

    lines = []
    for raw in path.read_text().splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            lines.append(json.loads(raw))
        except json.JSONDecodeError:
            continue

    lines = lines[-last_n:]
    n = len(lines)
    keeps = [x for x in lines if x.get("outcome") == "KEEP"]
    n_keeps = len(keeps)
    keep_rate = (n_keeps / n) if n else 0.0

    d = Diagnostics(n_experiments=n, n_keeps=n_keeps, keep_rate=keep_rate)
    d.recent_axes = [x.get("axis") for x in lines if x.get("axis")]

    # 1) Low keep rate: search is thrashing (>=5 experiments, <10% KEEP).
    if n >= 5 and keep_rate < 0.10:
        d.has_low_keep_rate = True

    # 2) High duplicates: the same axis retested many times without a win.
    if d.recent_axes:
        counts = Counter(d.recent_axes)
        top_axis, top_n = counts.most_common(1)[0]
        if top_n >= 3 and top_axis not in (None, "total_batch_size"):
            d.has_high_duplicates = True
            d.notes.append(f"axis '{top_axis}' retested {top_n}x")

    # 3) Low activation: far fewer experiments than the analyst pool implies
    #    over a full rotation (heuristic: < num_analysts experiments in window).
    if 0 < n < num_analysts:
        d.has_low_activation = True

    # 4) Slow propagation: a KEEP occurred early in the window yet the most
    #    recent experiments all DISCARD — suggesting the win wasn't built on.
    if n_keeps >= 1 and n >= 6:
        last_few = lines[-4:]
        if last_few and all(x.get("outcome") != "KEEP" for x in last_few):
            d.has_slow_propagation = True
            d.notes.append("KEEP not followed by further KEEPs in last 4")

    return d


def print_diagnostics(d: Diagnostics):
    print(f"[meta] experiments={d.n_experiments} keeps={d.n_keeps} "
          f"keep_rate={d.keep_rate:.2f}")
    print(f"[meta] high_duplicates={d.has_high_duplicates} "
          f"low_activation={d.has_low_activation} "
          f"slow_propagation={d.has_slow_propagation} "
          f"low_keep_rate={d.has_low_keep_rate}")
    if d.recent_axes:
        print(f"[meta] recent axes: {Counter(d.recent_axes).most_common(8)}")
    for note in d.notes:
        print(f"[meta] note: {note}")
