import json,hashlib
from pathlib import Path
import pymupdf

root=Path(__file__).resolve().parents[1]
names=['分体曲面背盖与储物舱_维护候选','储物舱_导轨锁止与承载板','F13_锁座连体支承上板','Q09_燕尾导轨等高垫块','B04_锁座避空曲面主背盖','B05_可拆曲面后背盖','Q10_后背盖圆角连接压板']
out=pymupdf.open();sources=[]
for name in names:
    p=root/'drawings/pdf'/(name+'.pdf');src=pymupdf.open(p);assert len(src)==1 and '模块化机械宠物' in src[0].get_text()
    out.insert_pdf(src);sources.append(str(p));src.close()
out.set_metadata({'title':'机械宠物储物舱承载与分体背盖 - 七页结构审阅图','author':'机械宠物建模项目','subject':'五张零件图、两张装配图；未制造释放'})
target=root/'drawings/pdf/储物舱承载与分体背盖_七页审阅版.pdf';out.save(target,garbage=4,deflate=True);out.close()
check=pymupdf.open(target);assert len(check)==7
renders=[]
for n,page in enumerate(check):
    p=root/'previews/drawings'/f'承载与分体背盖_最终_{n+1}.png';page.get_pixmap(dpi=120,alpha=False).save(p);renders.append(str(p))
report={'合册':str(target),'页数':len(check),'源图':sources,'页面渲染':renders,'SHA256':hashlib.sha256(target.read_bytes()).hexdigest(),'逐页人工视觉检查':'待进行'}
(root/'validation/承载与分体背盖图纸交付复核.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
