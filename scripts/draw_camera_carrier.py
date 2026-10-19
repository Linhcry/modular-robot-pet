from sw_drawings import *

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();assert sw.GetDocumentCount()==0
    sw.FrameState=C.swWindowMinimized;sw.DocumentVisible(True,1);sw.DocumentVisible(True,3);sw.CommandInProgress=True
    cat=json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))
    try:
        for prefix in ('H12','H13'):
            if '--assembly-only' in sys.argv:continue
            row=next(r for r in cat if r['id'].startswith(prefix+'_')).copy()
            row.update(drawing_scale=3 if prefix=='H13' else .85,drawing_iso_scale=3 if prefix=='H13' else .75)
            r=make(sw,row,True);p=ROOT/'validation/相机可换托架工程图检查.json'
            old=json.loads(p.read_text(encoding='utf-8')) if p.exists() else []
            p.write_text(json.dumps([x for x in old if x['id']!=row['id']]+[r],ensure_ascii=False,indent=2),encoding='utf-8')
        path=ROOT/'assemblies/触控视觉头部_自动对焦相机空间候选.SLDASM'
        row={'id':'ASM_AutofocusCamera','name':'自动对焦相机头部空间候选','path':str(path),
             'bbox_mm':[-56,-51,0,56,51,62.2],'drawing_scale':.85,'drawing_iso_scale':.85,
             'material_assumption':'PA12与6061-T6、硅胶、钢制连接件及厂家电子组件',
             'key_dimensions_mm':'镜头封装前端Z61.5，面框前面Z62.2；相机孔距21×12.5',
             'notes':'27组件58基准及紧固配合；相机与托架自身紧固件尚未加入。官方PDF与STEP板厚不同；光路、线束及实物待验证。'}
        r=make(sw,row,True);p=ROOT/'validation/相机可换托架工程图检查.json'
        old=json.loads(p.read_text(encoding='utf-8'));p.write_text(json.dumps([x for x in old if x['id']!=row['id']]+[r],ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
