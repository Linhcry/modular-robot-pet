from pathlib import Path
import pymupdf,json,hashlib
root=Path(__file__).resolve().parents[1];out=pymupdf.open();names=['触控视觉头部_承架紧固候选','H04_触控视觉曲面头壳','H05_触控屏与镜头圆角面框','H06_触控屏承架与隐藏走线槽','H07_触控屏齐平柔性密封圈'];sources=[]
for name in names:
    path=root/'drawings/pdf'/(name+'.pdf');src=pymupdf.open(path);assert len(src)==1 and '模块化机械宠物' in src[0].get_text();out.insert_pdf(src);src.close();sources.append(str(path))
out.set_metadata({'title':'触控视觉头部齐平嵌入 - 五页结构审阅图','author':'机械宠物建模项目','subject':'四张独立零件图与一张装配图；未制造释放'})
target=root/'drawings/pdf/触控视觉头部_齐平嵌入五页审阅版.pdf';out.save(target,garbage=4,deflate=True);out.close();renders=[]
with pymupdf.open(target) as check:
    for n,page in enumerate(check):
        p=root/'previews/drawings'/f'触控头部_最终_{n+1}.png';page.get_pixmap(dpi=120,alpha=False).save(p);renders.append(str(p))
report={'合册':str(target),'页数':5,'源图':sources,'页面渲染':renders,'SHA256':hashlib.sha256(target.read_bytes()).hexdigest(),'逐页视觉检查':'待检查','取代':'本版更新承架孔横距78mm和21组件44配合紧固总成；旧74mm五页版已留存wip历史目录，四页版为更早凹入方案'}
(root/'validation/触控头部图纸交付复核.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
