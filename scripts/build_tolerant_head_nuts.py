"""Revised clearance and longer snap arms; preserve H08/H09 as history."""
from build_touch_head import *

CAP_Z = 37.6


def shell_revision(d):
    head_shell(d)
    sketch(d,'四个加宽螺母杯定位座',lambda s:[roundrect(s,13,13,2,x,y) for x,y in MOUNT_HOLES])
    extrude(d,'定位座深4_6',4.6,42.1)
    sketch(d,'四处D9_0螺母杯装入孔',lambda s:holes(s,MOUNT_HOLES,9.0))
    cut(d,'定位座贯通至承压环肩',4.6,42.1)
    sketch(d,'八处加深卡钩槽',lambda s:[polygon(s,rect(1.4,3,cx=x+side*6.05,cy=y)) for x,y in MOUNT_HOLES for side in (-1,1)])
    cut(d,'卡钩槽高1_8',1.8,44.3)


def cup_revision(d):
    sketch(d,'圆角底盖与螺杆避空',lambda s:(roundrect(s,16,16,2),s.CreateCircleByRadius(0,0,0,.0019)))
    extrude(d,'底盖厚1',1)
    sketch(d,'D8_4螺母杯外壁',lambda s:(s.CreateCircleByRadius(0,0,0,.0042),s.CreateCircleByRadius(0,0,0,.0019)))
    extrude(d,'杯壁至高度8_0',7,1)
    radius=5.7/math.sqrt(3)
    sketch(d,'六角防转槽对边5_7',lambda s:polygon(s,[(radius*math.cos(k*math.pi/3),radius*math.sin(k*math.pi/3)) for k in range(6)]))
    cut(d,'防转槽深2_4_杯底5_6',2.4,5.6)
    sketch(d,'四处加长止挡柱',lambda s:[s.CreateCircleByRadius(x/1000,y/1000,0,.0009) for x in (-4.7,4.7) for y in (-4.7,4.7)])
    extrude(d,'止挡顶面高度4_5',3.5,1)
    sketch(d,'双侧长弹性臂',lambda s:[polygon(s,rect(.6,2.4,cx=side*7.2)) for side in (-1,1)])
    extrude(d,'卡扣臂至高度8',7,1)
    roots=[]
    for raw in body_list(d)[0].GetEdges():
        e=cast(raw,'IEdge');a=e.GetStartVertex();b=e.GetEndVertex()
        if not a or not b:continue
        pts=[cast(v,'IVertex').GetPoint() for v in (a,b)]
        if all(abs(p[2]-.001)<1e-7 and abs(abs(p[0])-.0069)<1e-7 for p in pts):roots.append(e)
    assert len(roots)==2,('snap root edges',len(roots))
    d.ClearSelection2(True)
    for i,e in enumerate(roots):assert cast(e,'IEntity').Select4(i>0,None)
    feature=cast(cast(d.FeatureManager,'IFeatureManager').FeatureFillet3(3,.0004,0,0,0,0,0,None,None,None,None,None,None,None),'IFeature')
    assert feature;feature.Name='弹性臂根部R0_4';d.ClearSelection2(True)
    for side in (-1,1):
        loft(d,'长卡钩导入斜面'+str(side),[(7.2,lambda s,side=side:polygon(s,rect(1.4,2.4,cx=side*6.2))),(8,lambda s,side=side:polygon(s,rect(.01,2.4,cx=side*6.895)))])


PARTS_REV=[
    ('H10_ClearanceHeadShell','宽槽螺母杯定位曲面头壳',shell_revision,'四个13×13 R2定位座；D9.0入口；卡槽高1.8，底Z44.3；原承架孔78×56'),
    ('H11_LongArmNutCup','长臂卡扣螺母防落杯',cup_revision,'底板16×16×1 R2；杯D8.4高8；六角AF5.7深2.4，底Z5.6；止挡顶Z4.5；臂厚0.6根R0.4')]


def main():
    sw=connect();sw.Visible=True;sw.FrameState=C.swWindowMinimized
    sw.DocumentVisible(True,1);sw.DocumentVisible(True,2);sw.CommandInProgress=True;d=None
    cat=json.loads(CAT_PATH.read_text(encoding='utf-8'));audit=[]
    try:
        for code,name,builder,dims in PARTS_REV:
            if len(sys.argv)>1 and code.split('_')[0] not in sys.argv[1:]:continue
            require_memory('单件构建:'+code)
            add_part(sw,cat,code,name,builder,dims,'PA12（密度1010kg/m3设计假设）','名义候选；装入力、疲劳、公差与工具释放待验证。杯原点装配Z37.6，名义杯底卸载间隙0.6。')
            row=next(r for r in cat if r['id']==code)
            d=cast(sw.OpenDoc6(row['path'],1,1,'',0,0)[0],'IModelDoc2')
            bs=body_list(d);errors=[f.Name for f in features(d) if f.GetErrorCode2()[0]]
            assert len(bs)==1 and not errors
            volume=sum(b.GetMassProperties(1)[3] for b in bs)*1e9
            color(d,(.86,.88,.82) if code.startswith('H10') else (.12,.16,.17))
            save(d,row['path']);preview(d,name)
            save(d,ROOT/'exports/step'/(Path(row['path']).stem+'.STEP'))
            audit.append({'编号':code,'文件':row['path'],'实体数':len(bs),'重建错误':errors,'体积_mm3':volume,'质量_g_密度假设':volume*.00101})
            bs.clear();sw.CloseDoc(d.GetTitle());d=None
            p=ROOT/'validation/长臂螺母杯零件检查.json'
            old=json.loads(p.read_text(encoding='utf-8')) if p.exists() else []
            p.write_text(json.dumps([r for r in old if r['编号']!=code]+[audit[-1]],ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps(audit[-1],ensure_ascii=False),flush=True)
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
