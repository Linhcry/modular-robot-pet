from sw_drawings import *

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True;out=[]
    rows=json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))
    try:
        for prefix in ('H04','H05','H06','H07'):
            if len(sys.argv)>1 and prefix not in sys.argv[1:]:continue
            r=next(r for r in rows if r['id'].startswith(prefix+'_')).copy();r.update(drawing_scale=.85,drawing_iso_scale=.75)
            out.append(make(sw,r,True))
        if len(sys.argv)==1 or 'ASM' in sys.argv[1:]:
            r={'id':'ASM_TouchHead','name':'触控视觉头部齐平嵌入候选','path':str(ROOT/'assemblies/触控视觉头部_空间与安装候选.SLDASM'),'bbox_mm':[-55,-51,0,55,51,62.2],'drawing_scale':.85,'drawing_iso_scale':.85,'material_assumption':'PA12与6061-T6、黑色硅胶、厂家屏幕组件','key_dimensions_mm':'屏幕横置；玻璃、面框与柔性圈前面均Z62.2；承架顶Z51.2','notes':'5个组件、12个基准配合；柔性圈为名义装配态。紧固件、相机、计算板及线束待装入；未制造释放。'}
            out.append(make(sw,r,True))
        p=ROOT/'validation/触控头部工程图检查.json';old=json.loads(p.read_text(encoding='utf-8')) if p.exists() else []
        p.write_text(json.dumps([r for r in old if r['id'] not in {a['id'] for a in out}]+out,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
