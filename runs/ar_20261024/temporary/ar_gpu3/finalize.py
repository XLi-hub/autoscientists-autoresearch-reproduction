"""Post-training bookkeeping: parse metric, record result, release claim, post [RESULT]."""
import sys, os, json, re, time, shutil, yaml, requests
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0,'/tmp/ar_gpu3')
from api import *

def parse_metrics(log):
    m = {}
    for key, pat in [
        ('val_bpb', r'val_bpb:\s*([0-9.]+)'),
        ('training_seconds', r'training_seconds:\s*([0-9.]+)'),
        ('total_seconds', r'total_seconds:\s*([0-9.]+)'),
        ('peak_vram_mb', r'peak_vram_mb:\s*([0-9.]+)'),
        ('mfu_percent', r'mfu_percent:\s*([0-9.]+)'),
        ('total_tokens_M', r'total_tokens_M:\s*([0-9.]+)'),
        ('num_steps', r'num_steps:\s*([0-9]+)'),
        ('num_params_M', r'num_params_M:\s*([0-9.]+)'),
        ('depth', r'depth:\s*([0-9]+)'),
    ]:
        mm = re.search(pat, log)
        if mm:
            m[key] = float(mm.group(1)) if '.' in mm.group(1) else int(mm.group(1))
    return m

def parse_curve(log):
    rows = []
    for mm in re.finditer(r'step (\d{5}) \(([0-9.]+)%\) \| loss: ([0-9.]+)', log):
        rows.append((int(mm.group(1)), float(mm.group(2)), float(mm.group(3))))
    return rows

def main(exp_id, description, axis, direction, value, current_value, extra_md="", seed=None):
    ws = Path(f'{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace')
    rep = ws/'repo'
    log = (ws/f'train_{exp_id}.stdout').read_text(errors='ignore')
    err = (ws/f'train_{exp_id}.stderr').read_text(errors='ignore')
    rc_path = Path('/tmp/ar_gpu3/train.rc')
    rc = int(rc_path.read_text().strip()) if rc_path.exists() else None
    met = parse_metrics(log)
    curve = parse_curve(log)
    our_metric = met.get('val_bpb')
    print('parsed:', met, 'rc=', rc, 'curve points', len(curve))
    if our_metric is None:
        print('NO METRIC — training failed'); print(err[-3000:]); return None

    # fresh champion read — HARD FAIL if unparseable. NEVER default to +/-inf:
    # that is what caused the 2026-10-24 erroneous promotion of exp_cap_window_ssll.
    champ = None
    for attempt in range(5):
        fresh_raw = get(MAIN_WS_ID,'champion.md')
        champ_try = pf(fresh_raw) if isinstance(fresh_raw, dict) else {}
        if isinstance(champ_try, dict) and isinstance(champ_try.get('metric_value'), (int,float)):
            champ = champ_try; break
        print(f'[champion read] attempt {attempt+1} unusable: keys={list(champ_try)[:5]}'); time.sleep(3)
    if champ is None:
        raise RuntimeError('FATAL: cannot parse champion.md metric_value — refusing to compare/promote')
    metric_name = champ.get('metric_name','val_bpb')
    direction_opt = champ.get('direction','minimize')
    current_best = float(champ['metric_value'])
    print(f'[champion] {champ.get("experiment_id")} {metric_name}={current_best}')
    delta = (current_best - our_metric) if direction_opt=='minimize' else (our_metric - current_best)

    # noise floor
    nf = get(MAIN_WS_ID,'knowledge/noise_floor_data.md')
    nfm = pf(nf)
    sigma = float(nfm.get('sigma_estimate', 0.002865))
    improved = (direction_opt=='minimize' and our_metric < current_best) or \
               (direction_opt=='maximize' and our_metric > current_best)
    outcome = 'KEEP' if improved else 'DISCARD'
    noise_note = ''
    if improved and abs(delta) <= sigma*2:
        outcome = 'NEAR-MISS'
        noise_note = (f'|delta| {abs(delta):.6f} <= 2*sigma {2*sigma:.6f} — NOT promoted; '
                      f'needs a second-seed confirmation.')
    print(f'outcome={outcome} delta={delta:+.6f} best={current_best} sigma={sigma}')

    # dynamics table
    dyn = []
    for (s,p,l) in curve:
        if len(curve) > 1:
            pass
    if curve:
        n=len(curve)
        for frac in (0.0,0.2,0.4,0.6,0.8,1.0):
            i=min(n-1,int(round(frac*(n-1))))
            dyn.append((curve[i][1], curve[i][0], curve[i][2]))
    last20 = (curve[-1][2]-curve[int(n*0.8)][2]) if curve and n>5 else None
    first = curve[0][2] if curve else None
    dyn_md = '\n'.join(f'| {p:.0f}% | {s} | {l:.3f} |' for p,s,l in dyn) or '| n/a | n/a | n/a |'

    stamp = datetime.now(timezone.utc)
    # stamped copies
    # (no submission.csv in this task; stamp train.py)
    shutil.copy(rep/'train.py', rep/f'train_{exp_id}.py')

    result_md = f"""# {exp_id} — {description}

- metric: **val_bpb = {our_metric:.6f}** (minimize)
- outcome: **{outcome}** (delta {delta:+.6f} vs champion {current_best:.6f})
- agent: {AGENT_NAME} (GPU 0), team: capacity
- timestamp: {stamp.isoformat()}
- axis: {axis} | direction: {direction} | value: {value} (current: {current_value})

## Result

- val_bpb: {our_metric:.6f} vs {current_best:.6f} -> {delta:+.6f}
- Steps: **{met.get('num_steps')}** | tokens {met.get('total_tokens_M')}M | tok/s {int((met.get('total_tokens_M') or 0)*1e6/300):,}
- training_seconds {met.get('training_seconds')} | total_seconds {met.get('total_seconds')} | peak_vram {met.get('peak_vram_mb')}MB | params {met.get('num_params_M')}M | depth {met.get('depth')}
- Noise gate: |delta| {abs(delta):.6f} vs 2*sigma {2*sigma:.6f} (sigma {sigma:.6f}). {noise_note or 'Outside/inside band as classified above.'}
{extra_md}
## Training Dynamics

| progress | step | smooth loss |
|---|---|---|
{dyn_md}

- final-20% loss drop: {f'{last20:.4f}' if last20 is not None else 'n/a'} (range {f'{first:.3f} -> {curve[-1][2]:.3f}' if curve else 'n/a'})

## Reproduction

```bash
cd {FOCUS_ROOT}/agents/{AGENT_NAME}/workspace/repo
CUDA_VISIBLE_DEVICES=0 HF_HOME=/root/autodl-tmp/cache/huggingface HF_HUB_OFFLINE=1 python train.py
```
"""
    r = requests.put(f'{API}/workspaces/{MAIN_WS_ID}/files/results/{exp_id}.md',
                     headers=HEADERS, json={'content':result_md}, timeout=30)
    print('result file PUT', r.status_code)

    # queue: release claim + move pending->completed
    q_raw = get(TEAM_WS_ID,'queue.md')
    q_fm = pf(q_raw)
    q_fm.setdefault('claims',{}).pop(AGENT_NAME,None)
    pend = q_fm.get('pending') or []
    comp = q_fm.get('completed') or []
    run_new = []
    for it in pend:
        if it.get('id')==exp_id:
            it=dict(it); it['completed_at']=stamp.isoformat(); it['completed_by']=AGENT_NAME
            it['outcome']=outcome; it['val_score']=our_metric
            comp.append(it)
        else:
            run_new.append(it)
    q_fm['pending']=run_new; q_fm['completed']=comp
    body=q_raw.get('content','').split('---',2)[-1]
    nc=f"---\n{yaml.safe_dump(q_fm,sort_keys=False)}---{body}"
    assert yaml.safe_load(nc.split('---')[1])==q_fm
    r=requests.put(f'{API}/workspaces/{TEAM_WS_ID}/files/queue.md',
                   headers={**HEADERS,'If-Match':str(q_raw.get('version',0))},json={'content':nc},timeout=30)
    print('queue PUT', r.status_code)

    # champion update on KEEP
    promoted = False
    if outcome=='KEEP':
        cur = get(MAIN_WS_ID,'champion.md'); cur_v=cur.get('version',0)
        # read the ACTUAL constants from the trained file (do not hardcode)
        import ast as _ast
        _src = (rep/'train.py').read_text()
        def _c(name):
            mm = re.search(rf'^{name}\s*=\s*([^#\n]+)', _src, re.MULTILINE)
            if not mm: return None
            expr = mm.group(1).strip()
            try:
                return _ast.literal_eval(expr)
            except Exception:
                return eval(expr, {'__builtins__': {}}, {})   # simple arithmetic like 2**18
        _cfg = {
            'DEPTH': _c('DEPTH'), 'ASPECT_RATIO': _c('ASPECT_RATIO'), 'HEAD_DIM': _c('HEAD_DIM'),
            'WINDOW_PATTERN': _c('WINDOW_PATTERN'), 'MLP_EXPANSION': _c('MLP_EXPANSION'),
            'TOTAL_BATCH_SIZE': _c('TOTAL_BATCH_SIZE'), 'DEVICE_BATCH_SIZE': _c('DEVICE_BATCH_SIZE'),
            'compile_mode': 'max-autotune-no-cudagraphs', 'num_steps': met.get('num_steps'),
            'params_M': met.get('num_params_M'),
        }
        print('[champion cfg]', _cfg)
        champ_md=f"""---
metric_name: val_bpb
metric_value: {our_metric}
seed_values: [{our_metric}]
direction: minimize
experiment_id: {exp_id}
agent: {AGENT_NAME}
timestamp: {stamp.isoformat()}
status: established
---

# Champion: {exp_id}

## Experiment Description

{description}

## Result

- **Recorded metric (1 seed):** val_bpb = {our_metric}
- **Delta from previous:** {delta:+.6f}
- Steps: {met.get('num_steps')}; {met.get('total_tokens_M')}M tokens; peak VRAM {met.get('peak_vram_mb')}MB; params {met.get('num_params_M')}M

## Complete Hyperparameters

```json
{json.dumps(_cfg, indent=2)}
```

## Reproduction

1. Copy `{FOCUS_ROOT}/champion/train.py`
2. Run: `CUDA_VISIBLE_DEVICES=0 HF_HOME=/root/autodl-tmp/cache/huggingface HF_HUB_OFFLINE=1 python train.py`
3. Expected: val_bpb ~ {our_metric}

## Provenance

- Agent: {AGENT_NAME}; GPU 0
- Timestamp: {stamp.isoformat()}
"""
        r=requests.put(f'{API}/workspaces/{MAIN_WS_ID}/files/champion.md',
                       headers={**HEADERS,'If-Match':str(cur_v)},json={'content':champ_md},timeout=30)
        print('champion PUT', r.status_code)
        if r.status_code in (200,201):
            promoted=True
            src=rep/f'train_{exp_id}.py'; dst=Path(f'{FOCUS_ROOT}/champion/train.py'); tmp=dst.with_suffix('.py.tmp')
            shutil.copy(src,tmp); tmp.replace(dst)
            with open(f'{FOCUS_ROOT}/champion/SOURCE','a') as f:
                f.write(f'{exp_id} {our_metric:.6f} {AGENT_NAME} {stamp.isoformat()} ({description})\n')
            print('propagated champion/train.py')

    # near-miss ledger entry in dead_ends for DISCARD
    if outcome=='DISCARD':
        de_raw = get(TEAM_WS_ID,'dead_ends.md')
        de = de_raw.get('content','# Dead Ends\n')
        entry=(f"\n- exp_id: {exp_id}\n  axis: {axis}\n  direction: {direction}\n  value: {value}\n"
               f"  delta: {delta:+.6f}\n  family: {'_'.join(exp_id.split('_')[:2])}\n"
               f"  date: {stamp.date()}\n  reason: {description[:160]}\n")
        r=requests.put(f'{API}/workspaces/{TEAM_WS_ID}/files/dead_ends.md',
                       headers={**HEADERS,'If-Match':str(de_raw.get('version',0))},json={'content':de+entry},timeout=30)
        print('dead_ends PUT', r.status_code)

    # post [RESULT]
    r=requests.post(f'{API}/posts',headers=HEADERS,json={
        'workshop':WORKSHOP,
        'title':f"[RESULT] {exp_id}: {metric_name}={our_metric:.6f} ({outcome})",
        'content':(f"## Experiment\n{description}\n\n## Result\n{metric_name}: {our_metric:.6f}\n"
                   f"Delta: {delta:+.6f} (champion {current_best:.6f})\nOutcome: {outcome}\n"
                   f"Steps: {met.get('num_steps')} | tokens {met.get('total_tokens_M')}M | peak VRAM {met.get('peak_vram_mb')}MB\n"
                   f"Noise: sigma {sigma:.6f}, 2-sigma band {2*sigma:.6f}\n\n## Team\ncapacity"),
        'notify_agents':['ar_20261024_gpu6','ar_20261024_analyst3'],
        'tags':['team:capacity','type:result',f'outcome:{outcome}']},timeout=30)
    post_id = r.json().get('id') if r.ok else None
    print('RESULT post', r.status_code, post_id)

    # sentinel
    rl = ws/'result_latest.json'
    prior = json.loads(rl.read_text()) if rl.exists() else {}
    prior.update({'val_score':our_metric,'direction':'minimize','exp_id':exp_id,'agent':AGENT_NAME,
                  'status':'posted','posted_to_workshop':True,'result_post_id':post_id,
                  'posted_at':stamp.isoformat(),'description':description,
                  'item':{'id':exp_id,'axis':axis,'direction':direction,'value':value}})
    rl.write_text(json.dumps(prior,indent=2,default=str))
    return {'exp_id':exp_id,'val_bpb':our_metric,'outcome':outcome,'delta':delta,'steps':met.get('num_steps'),'promoted':promoted}

if __name__=='__main__':
    a=sys.argv
    res=main(a[1],a[2],a[3],a[4],a[5],a[6], extra_md=(a[7] if len(a)>7 else ''))
    print('FINAL:',json.dumps(res))
