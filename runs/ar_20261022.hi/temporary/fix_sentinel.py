import json
from pathlib import Path
p=Path("/root/autodl-tmp/ar_20261022.hi/agents/ar_20261022hi_gpu4/workspace/result_latest.json")
d=json.loads(p.read_text()); d["result_post_id"]="0e19055c-3b4e-41c4-b698-af6d4d5042c8"
p.write_text(json.dumps(d,indent=2,default=str)); print(d["status"], d["result_post_id"], d["outcome"], d["val_score"])
