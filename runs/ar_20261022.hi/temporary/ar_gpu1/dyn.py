import re, statistics
from pathlib import Path
p=Path("/root/autodl-tmp/ar_20261022.hi/agents/ar_20261022hi_gpu1/workspace/train_exp_gqa_kv1.stdout")
log=p.read_text(errors="ignore")
# header
for line in log.splitlines()[:20]:
    if any(k in line for k in ["Model config","Vocab","params","estimate_flops","grad_accum","total_params"]):
        print(line[:300])
steps=[]
for m in re.finditer(r"step (\d+) \(([\d.]+)%\) \| loss: ([\d.]+)", log):
    steps.append((int(m.group(1)), float(m.group(2)), float(m.group(3))))
print("n step records", len(steps))
if steps:
    # block means by pct
    import collections
    buckets=collections.OrderedDict()
    edges=[(0,5),(5,20),(20,40),(40,60),(60,80),(80,95),(95,100.01)]
    for lo,hi in edges:
        vals=[l for s,pct,l in steps if lo<=pct<hi]
        if vals: buckets[f"{lo}-{hi}"]=round(statistics.mean(vals),3)
    print("block-mean loss:", dict(buckets))
    print("first loss",steps[0][2],"last loss",steps[-1][2])
