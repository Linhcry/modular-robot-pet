from sw_drawings import *

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    rows={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))}
    result=[]
    try:
        for code in ('Q06_LockBase','Q07_LockBridge','Q08_CaptivePin'):
            r=rows[code].copy();r['drawing_scale']=1.5;r['drawing_iso_scale']=1.5
            result.append(make(sw,r,True))
        r={'id':'ASM_CaptiveCargoLock','name':'储物舱防脱锁止装入检查','path':str(ROOT/'assemblies/储物舱防脱锁止_装入检查.SLDASM'),'bbox_mm':[-75,-60,-5.5,95,60,64.2],'drawing_scale':.8,'drawing_iso_scale':.8,'material_assumption':'6061-T6与PA12，销及紧固件为钢','key_dimensions_mm':'20个实例；销升9解锁；销尖高20；舱耳顶面19.2；向负X滑出','notes':'此图验证防脱机构与舱体安装空间；导轨和机身尚待接入。M6公称杆与底孔有预期交叠，不等于实际干涉。螺旋运动与振动防松未验证。'}
        result.append(make(sw,r,True))
        (ROOT/'validation/防脱锁止工程图检查.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
