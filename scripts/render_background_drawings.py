from pathlib import Path
import json,sys
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
names=['F10_镂空下承载板','F11_双承载带上板','Q05_分体短燕尾滑靴','L01_大腿连杆','机身壳体与框架_空间候选']
out=ROOT/'previews/drawings/pdf_review';out.mkdir(parents=True,exist_ok=True)
combined=pymupdf.open();log=[]
for name in names:
    path=ROOT/'drawings/pdf'/f'{name}.pdf'
    with pymupdf.open(path) as doc:
        assert len(doc)==1,(name,len(doc))
        text=doc[0].get_text()
        assert '模块化机械宠物' in text and '未制造释放' in text,(name,'missing annotations')
        target=out/f'{name}.png';doc[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).save(target)
        combined.insert_pdf(doc)
        log.append({'PDF':str(path),'PNG':str(target),'文本提取长度':len(text),'页数':len(doc),'视觉审阅':'待人工/模型检查渲染PNG'})
target=ROOT/'drawings/pdf/后台建模阶段工程图_五页审阅版.pdf';combined.save(target);combined.close()
(ROOT/'validation/后台工程图渲染检查.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8');print(json.dumps({'合订本':str(target),'页面':log},ensure_ascii=False,indent=2))
