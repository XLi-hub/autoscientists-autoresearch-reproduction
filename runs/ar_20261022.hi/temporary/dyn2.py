import re
from pathlib import Path
def curve(p):
    txt=Path(p).read_text(errors="ignore").replace("\r","\n")
    return [(int(m.group(1)),float(m.group(2)),float(m.group(3))) for m in re.finditer(r"step (\d+) \(([\d.]+)%\) \| loss: ([\d.]+)",txt)]
mine=curve("/root/autodl-tmp/ar_20261022.hi/agents/ar_20261022hi_gpu4/workspace/train_exp_muon_beta2_hi.stdout")
champ=curve("/root/autodl-tmp/ar_20261022.hi/agents/ar_20261022hi_gpu2/workspace/train_exp_batch_2e17.stdout")
print(f"mine={len(mine)} champ={len(champ)}")
def at(c,f): return c[min(len(c)-1,int(len(c)*f))]
for f in (0.1,0.2,0.4,0.6,0.8,0.9,0.99):
    a,b=at(mine,f),at(champ,f)
    print(f"  {int(f*100):3d}%: mine {a[2]:.4f} | champ {b[2]:.4f} | diff {a[2]-b[2]:+.4f}")
print("\nloss drop 80->99%: mine",round(at(mine,.99)[2]-at(mine,.8)[2],4),"champ",round(at(champ,.99)[2]-at(champ,.8)[2],4))
print("final train loss: mine",mine[-1][2],"champ",champ[-1][2])
