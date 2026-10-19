import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'data/parts_catalog.json';rows=json.loads(p.read_text(encoding='utf-8'))
for row in rows:
    if row['id'] in ('B04_MainBack','B05_ServiceBack'):
        row['notes']='保留放样曲面；拆两块压板后移开后盖，再解锁取舱。十一种离散姿态无额外干涉；连续行程、螺母防掉落及工具空间待完善。'
p.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
hashes={str(i):hashlib.sha256((root/'previews/drawings'/f'承载与分体背盖_最终_{i}.png').read_bytes()).hexdigest() for i in range(1,8)}
(root/'validation/图纸复核前页面哈希.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
