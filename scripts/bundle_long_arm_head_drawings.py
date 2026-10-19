from pathlib import Path
import pymupdf,json,hashlib

root=Path(__file__).resolve().parents[1]
names=['触控视觉头部_长臂螺母防落候选','H10_宽槽螺母杯定位曲面头壳','H11_长臂卡扣螺母防落杯',
       'H05_触控屏与镜头圆角面框','H06_触控屏承架与隐藏走线槽','H07_触控屏齐平柔性密封圈']
out=pymupdf.open();sources=[]
for name in names:
    path=root/'drawings/pdf'/(name+'.pdf')
    with pymupdf.open(path) as src:
        assert len(src)==1 and '模块化机械宠物' in src[0].get_text()
        out.insert_pdf(src)
    sources.append({'路径':str(path),'SHA256':hashlib.sha256(path.read_bytes()).hexdigest()})
out.set_metadata({'title':'触控视觉头部 - 长臂螺母防落六页审阅图','author':'机械宠物建模项目','subject':'五张独立零件图与一张装配图；未制造释放'})
target=root/'drawings/pdf/触控视觉头部_长臂螺母防落六页审阅版.pdf'
out.save(target,garbage=4,deflate=True);out.close()
report={'合册':str(target),'页数':6,'源图':sources,'SHA256':hashlib.sha256(target.read_bytes()).hexdigest(),
        '逐页视觉检查':'待检查','边界':'名义结构审阅；制造公差、卡扣力学和完整电子紧固未冻结。头壳STEP导出仍未通过原生回读。'}
(root/'validation/长臂头部图纸交付复核.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(str(target))
