from pathlib import Path
import json,hashlib,sys
import pymupdf
from sw_core import connect

ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/'validation'/name).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
parts=read('减重框架与护壳检查.json')
assert len(parts)==6 and all(p['实体数']==1 and not p['重建错误'] for p in parts)
shoe=read('分体短滑靴检查.json');assert shoe['实体数']==1 and not shoe['重建错误']
body=read('机身壳体与框架空间检查.json')
assert len(body['零件实例'])==6 and len(body['配合'])==15 and not body['干涉']
assert all(not m['错误'][0] for m in body['配合'])
cargo=read('短滑靴储物舱装配审计.json');assert len(cargo['components'])==49 and len(cargo['mates'])==96
assert all(not r['error'][0] for r in cargo['mates'])
assert max(r['max_origin_error_mm'] for r in cargo['components'])<1e-4
motion=read('短滑靴储物舱开启干涉检查.json')
assert [r['angle_deg'] for r in motion]==[0,15,30,45,60,75,90]
assert all(not r['mate_errors'] and r['origin_error_mm']<1e-4 for r in motion)
assert all(len(r['interferences'])==8 and all(c['classification']=='螺纹公称杆与攻丝底孔的预期简化交叠' for c in r['interferences']) for r in motion)
draw=read('后台设计工程图检查.json');assert len(draw)==5
review=read('后台工程图渲染检查.json')
combined=ROOT/'drawings/pdf/后台建模阶段工程图_五页审阅版.pdf'
with pymupdf.open(combined) as doc:
    assert len(doc)==5
    for i,r in enumerate(review):
        # The inspected single-page renders and the final binder are pixel-identical.
        pix=doc[i].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False)
        original=pymupdf.Pixmap(r['PNG'])
        assert pix.width==original.width and pix.height==original.height and pix.samples==original.samples,(i,'binder pixels changed')
        r.update(视觉审阅='已查看最终PNG；修复F11尺寸压线、放大Q05视图；未发现明显裁切或文字重叠',PDF_SHA256=sha(r['PDF']),合订本页面像素一致=True)
(ROOT/'validation/后台工程图渲染检查.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
sw=connect()
report={'阶段':'本批后台设计审核；非整机验收或制造释放','新建独立候选零件数':7,'机身空间候选':{'实例':6,'实际配合':15,'非预期干涉':0},'短滑靴储物舱':{'实例':49,'实际配合':96,'离散开盖配置':7,'每配置预期螺纹简化交叠':8,'非预期干涉':0},'原生工程图数':5,'PDF页数':5,'PDF':str(combined),'PDF_SHA256':sha(combined),'本体质量候选估计_kg':read('减重候选质量决策.json')['局部候选代入估计本体_kg'],'图形界面输入':'未操作鼠标或键盘；原生CAD通过最小化COM执行','SW剩余打开文档数':sw.GetDocumentCount(),'未完成':'整机质量目标、最终电机与大工程师模型、50项机械参考、整机装配及制造/实物验证'}
(ROOT/'validation/后台建模阶段审核.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
