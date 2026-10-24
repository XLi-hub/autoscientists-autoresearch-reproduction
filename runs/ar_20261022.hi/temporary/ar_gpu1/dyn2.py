import re, statistics, collections
from pathlib import Path
log=Path("/root/autodl-tmp/ar_20261022.hi/agents/ar_20261022hi_gpu1/workspace/train_exp_wd_0p0.stdout").read_text(errors="ignore")
for line in log.splitlines()[:20]:
    if any(k in line for k in ["Model config","Vocab","params"]): print(line[:250])
steps=[(int(m.group(1)),float(m.group(2)),float(m.group(3))) for m in re.finditer(r"step (\d+) \(([\d.]+)%\) \| loss: ([\d.]+)",log)]
b=collections.OrderedDict()
for lo,hi in [(0,5),(5,20),(20,40),(40,60),(60,80),(80,95),(95,100.01)]:
    v=[l for s,p,l in steps if lo<=p<hi]
    if v: b[f"{lo}-{hi}"]=round(statistics.mean(v),3)
print("n records",len(steps),"block-mean loss:",dict(b))
