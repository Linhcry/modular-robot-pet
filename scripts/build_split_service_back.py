"""Retain the curved B02 master; create independent front shell and removable rear shell."""
from build_mechanism_parts import *
import shutil

def split_shell(d,rear):
    # A 0.6 mm butt seam, preserving the original loft and wall thickness.
    if rear:
        sketch(d,'前部切除_后盖接缝X负77_3',lambda sm:polygon(sm,rect(500,400,cx=172.7)))
    else:
        sketch(d,'后部切除_主盖接缝X负76_7',lambda sm:polygon(sm,rect(500,400,cx=-326.7)))
    cut(d,'前后护盖分件_接缝间隙0_6',both=True)
    if not rear:
        sketch(d,'锁座局部圆角避空_26乘64_R6',lambda sm:roundrect(sm,26,64,6,83,0));cut(d,'锁座与螺旋销穿出开口',both=True)
    x=-90 if rear else -64
    def seats(sm):
        for y in (-78,78):roundrect(sm,14,14,2,x,y)
    sketch(d,'两个连接压板平面支承座',seats);extrude(d,'支承座_底32顶39',7,32)
    def holes(sm):
        for y in (-78,78):sm.CreateCircleByRadius(x/1000,y/1000,0,.0017)
    sketch(d,'两个M3贯穿连接孔',holes);cut(d,'连接孔_双向贯穿',both=True)
    assert chamfer_top(d,.2),'support seat chamfer failed'

def strap(d):
    sketch(d,'圆角可拆连接压板与两孔',lambda sm:(roundrect(sm,44,14,3),sm.CreateCircleByRadius(-.013,0,0,.0017),sm.CreateCircleByRadius(.013,0,0,.0017)))
    extrude(d,'压板厚2',2);assert chamfer_top(d,.2)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.Visible=True;sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    cat=json.loads(CAT_PATH.read_text(encoding='utf-8'));source=next(r['path'] for r in cat if r['id']=='B02_UpperBody');audits=[]
    try:
        for code,name,rear in [('B04_MainBack','锁座避空曲面主背盖',False),('B05_ServiceBack','可拆曲面后背盖',True)]:
            path=ROOT/'parts'/f'{code.split("_")[0]}_{name}.SLDPRT';shutil.copy2(source,path)
            d=cast(sw.OpenDoc6(str(path),1,1,'',0,0)[0],'IModelDoc2');assert d
            try:
                split_shell(d,rear);d.ForceRebuild3(False)
                errors=[f.Name for f in features(d) if f.GetErrorCode2()[0]];bs=body_list(d);assert len(bs)==1 and not errors,(code,len(bs),errors)
                dims='沿X=-77处分件，接缝0.6；支承座顶Z39，D3.4孔Y±78、X'+('-90' if rear else '-64')
                notes='原B02独立副本保留放样曲面；与可拆压板配合。拆下两块压板后先抬高后盖解除下壳止口，再取出储物舱；拆装行程尚待本次总装复核。'
                props=cast(cast(d.Extension,'IModelDocExtension').CustomPropertyManager(''),'ICustomPropertyManager')
                for k,v in {'零件编号':code,'零件名称':name,'关键尺寸':dims,'设计说明':notes}.items():props.Add3(k,C.swCustomInfoText,v,C.swCustomPropertyReplaceValue)
                color(d,(.87,.88,.82));save(d,path);bs=body_list(d)
                row={'id':code,'name':name,'kind':'custom','path':str(path),'material_assumption':'PA12（设计假设）','key_dimensions_mm':dims,'notes':notes,'bbox_mm':[v*1000 for v in bs[0].GetBodyBox()],'solid_count':1,'features':[{'name':f.Name,'type':f.GetTypeName2(),'error':f.GetErrorCode2()} for f in features(d)]}
                cat=[r for r in cat if r['id']!=code]+[row];CAT_PATH.write_text(json.dumps(cat,ensure_ascii=False,indent=2),encoding='utf-8')
                audits.append({'编号':code,'实体数':len(bs),'重建错误':errors,'质量_g_按1010kg_m3':sum(b.GetMassProperties(1)[3] for b in bs)*1010*1000,'文件':str(path)})
            finally:sw.CloseDoc(d.GetTitle())
        import refine_curved_parts as ref
        ref.preview=lambda *a,**k:False
        add_part(sw,cat,'Q10_BackStrap','后背盖圆角连接压板',strap,'44×14×2，R3，两D3.4孔距26','6061-T6 铝合金（设计假设）','两块压板连接前后背盖；四个螺钉均从上方可达。几何夹紧不等于预紧力/疲劳验证。')
        (ROOT/'validation/曲面背盖分件零件检查.json').write_text(json.dumps(audits,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
