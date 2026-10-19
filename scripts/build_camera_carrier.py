"""Replaceable, insulated camera carrier based on the official standard Camera 3 STEP.

The official PDF and STEP differ in PCB thickness. This is a CAD-fit candidate,
not a released manufacturing stack; preserve H06 and the reviewed head assembly.
"""
from build_touch_head import *
import hashlib

CAM_ROT=(0,1,0,1,0,0,0,0,-1)
CAM_XYZ=(-12.5,15.6,53.85)
CARRIER_XYZ=(0,30,51.2)
CAM_HOLES=[(x,y) for x in (-10.5,10.5) for y in (-12.4,.1)]
BOSS_TOP=2.6373


def screen_mount(d):
    screen_bracket(d)
    sketch(d,'相机螺母与后插座避空28乘29_5',lambda s:roundrect(s,28,29.5,2,0,27.75))
    cut(d,'可换相机托架下部维修避空',both=True)
    sketch(d,'相机托架双M3连接孔',lambda s:holes(s,[(-20,25),(20,25)],3.4))
    cut(d,'托架安装孔贯通',both=True)


def camera_carrier(d):
    sketch(d,'圆角开框绝缘托板',lambda s:(roundrect(s,27.8,18,1.5,0,-6.7),roundrect(s,16,12,1,0,-6.2)))
    extrude(d,'托板抬高0_5并厚1_2',1.2,.5)
    sketch(d,'双侧下沉安装耳',lambda s:[roundrect(s,12,7,2,side*16.5,-5) for side in (-1,1)])
    extrude(d,'安装耳底面基准与厚1_7',1.7)
    sketch(d,'四点绝缘支承柱',lambda s:holes(s,CAM_HOLES,3.8))
    extrude(d,'官方模型板背支承高度',BOSS_TOP-1.7,1.7)
    sketch(d,'四个相机M2间隙孔',lambda s:holes(s,CAM_HOLES,2.2))
    cut(d,'相机紧固通孔',both=True)
    sketch(d,'双耳M3间隙孔',lambda s:holes(s,[(-20,-5),(20,-5)],3.4))
    cut(d,'托架连接通孔',both=True)
    sketch(d,'板背双器件圆角避空',lambda s:[roundrect(s,4.2,4.2,.6,x,y) for x,y in [(8.7,-4.6),(-8.7,-6)]])
    cut(d,'板背器件维护避空贯通',both=True)
    # Round plan corners keep the camera/FPC area smooth; keep support faces flat.
    d.ClearSelection2(True);edges=[]
    for raw in body_list(d)[0].GetEdges():
        e=cast(raw,'IEdge');a=e.GetStartVertex();b=e.GetEndVertex()
        if not a or not b:continue
        pts=[cast(v,'IVertex').GetPoint() for v in (a,b)]
        if all(abs(p[2]-.0017)<1e-7 for p in pts) and all(abs(p[0])>.014 for p in pts):edges.append(e)
    for i,e in enumerate(edges):assert cast(e,'IEntity').Select4(i>0,None)
    if edges:
        f=cast(d.FeatureManager,'IFeatureManager').InsertFeatureChamfer(0,1,.00015,math.pi/4,0,0,0,0)
        assert f;cast(f,'IFeature').Name='安装耳外缘去锐C0_15'
    d.ClearSelection2(True)


def main():
    sw=connect();assert sw.GetDocumentCount()==0
    sw.Visible=True;sw.FrameState=C.swWindowMinimized;sw.DocumentVisible(True,1);sw.CommandInProgress=True;d=None
    cat=json.loads(CAT_PATH.read_text(encoding='utf-8'))
    rows=[('H12_CameraScreenBracket','带可换相机接口的屏幕承架',screen_mount,'原H06接口保留；相机避空28×29.5；托架M3孔X±20 Y25','6061-T6 铝合金（密度2700kg/m3设计假设）'),
          ('H13_CameraCarrier','四点绝缘可换相机托架',camera_carrier,'托板27.8×18；双耳总宽45；相机孔距21×12.5 D2.2；支承顶2.6373','PA12（密度1010kg/m3设计假设）')]
    report=[]
    try:
        for code,name,builder,dims,material in rows:
            if len(sys.argv)>1 and code.split('_')[0] not in sys.argv[1:]:continue
            add_part(sw,cat,code,name,builder,dims,material,'Camera Module 3标准版STEP适配候选。官方PDF板厚1.12与STEP叠层不一致，支承高度、螺钉长度须实物复核；未制造释放。')
            row=next(r for r in cat if r['id']==code)
            d=cast(sw.OpenDoc6(row['path'],1,1,'',0,0)[0],'IModelDoc2')
            bs=body_list(d);errors=[f.Name for f in features(d) if f.GetErrorCode2()[0]]
            assert len(bs)==1 and not errors
            record={'编号':code,'原生文件':row['path'],'实体数':1,'特征错误':errors,'体积_mm3':bs[0].GetMassProperties(1)[3]*1e9,'Check2原始返回':bs[0].Check2()}
            save(d,ROOT/'exports/step'/(Path(row['path']).stem+'.STEP'))
            record['原生SHA256']=hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()
            report.append(record);sw.CloseDoc(d.GetTitle());d=None
            old_path=ROOT/'validation/相机可换托架原生零件检查.json'
            old=json.loads(old_path.read_text(encoding='utf-8')) if old_path.exists() else []
            old_path.write_text(json.dumps([r for r in old if r['编号']!=code]+[record],ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps(record,ensure_ascii=False),flush=True)
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized


if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
