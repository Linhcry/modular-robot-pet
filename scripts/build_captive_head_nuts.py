"""Removable nut cups: washer insertion remains possible; clamp load bypasses cup."""
from build_touch_head import *

CAP_Z=39.6

def captive_shell(d):
    head_shell(d)
    sketch(d,'四个螺母杯圆角定位座',lambda s:[roundrect(s,11,11,2,x,y) for x,y in MOUNT_HOLES])
    extrude(d,'定位座向后伸出4_6',4.6,42.1)
    # A round through entrance admits the 7 mm steel washer. Hex capture belongs in the removable cup.
    sketch(d,'螺母杯与钢垫圈可通过的D8_6入口',lambda s:holes(s,MOUNT_HOLES,8.6))
    cut(d,'定位座贯通至环肩背面',4.6,42.1)
    sketch(d,'八处底盖卡钩定位凹口',lambda s:[polygon(s,rect(.6,3,cx=x+side*5.4,cy=y)) for x,y in MOUNT_HOLES for side in (-1,1)])
    cut(d,'卡钩槽高1_0',1,44.7)

def nut_cup(d):
    sketch(d,'底盖圆角底板与螺杆避空',lambda s:(roundrect(s,14,14,2),s.CreateCircleByRadius(0,0,0,.0019)))
    extrude(d,'底盖厚1',1)
    # Cup outside diameter8.4; the lower floor supports a loose nut before clamp preload.
    sketch(d,'螺母杯圆柱外壁',lambda s:(s.CreateCircleByRadius(0,0,0,.0042),s.CreateCircleByRadius(0,0,0,.0019)))
    extrude(d,'螺母杯高5_4',5.4,1)
    r=5.7/math.sqrt(3)
    sketch(d,'六角螺母防转槽对边5_7',lambda s:polygon(s,[(r*math.cos(k*math.pi/3),r*math.sin(k*math.pi/3)) for k in range(6)]))
    cut(d,'螺母杯六角入口深2_4',2.4,4)
    sketch(d,'四点轴向止挡小柱',lambda s:[s.CreateCircleByRadius(x/1000,y/1000,0,.0006) for x in (-4,4) for y in (-4,4)])
    extrude(d,'止挡柱高1_5',1.5,1)
    sketch(d,'双侧可释放弹性臂',lambda s:[polygon(s,rect(.6,2.4,cx=side*6.0)) for side in (-1,1)])
    extrude(d,'卡扣臂自由高5',5,1)
    # Concave arm roots: real fillets, not just rounded outer appearance.
    roots=[]
    for raw in body_list(d)[0].GetEdges():
        e=cast(raw,'IEdge');v=e.GetStartVertex();w=e.GetEndVertex()
        if not v or not w:continue
        a=cast(v,'IVertex').GetPoint();b=cast(w,'IVertex').GetPoint()
        if all(abs(p[2]-.001)<1e-7 and abs(abs(p[0])-.0057)<1e-7 for p in (a,b)):roots.append(e)
    assert len(roots)==2,('arm root edges',len(roots))
    d.ClearSelection2(True)
    for i,e in enumerate(roots):assert cast(e,'IEntity').Select4(i>0,None)
    f=cast(cast(d.FeatureManager,'IFeatureManager').FeatureFillet3(3,.0004,0,0,0,0,0,None,None,None,None,None,None,None),'IFeature')
    assert f,'arm root R0.4';f.Name='卡扣根部圆角R0_4';d.ClearSelection2(True)
    for side in (-1,1):
        loft(d,'卡钩导入斜面'+str(side),[(5.2,lambda s,side=side:polygon(s,rect(.5,2.4,cx=side*5.45))),(6,lambda s,side=side:polygon(s,rect(.01,2.4,cx=side*5.695)))])

NEW_PARTS=[('H08_CaptiveHeadShell','螺母杯定位曲面头壳',captive_shell,'沿用H04外形与78×56承架孔距；4个11×11定位座，D8.6入口；卡槽Z44.7至45.7'),('H09_CaptiveNutCup','卡扣式螺母杯防落底盖',nut_cup,'底板14×14×1 R2；杯D8.4高5.4，六角槽AF5.7深2.4；双卡臂厚0.6，根R0.4')]

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.Visible=True;sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True;d=None
    cat=json.loads(CAT_PATH.read_text(encoding='utf-8'));records=[]
    try:
        for code,name,builder,dims in NEW_PARTS:
            if len(sys.argv)>1 and code.split('_')[0] not in sys.argv[1:]:continue
            add_part(sw,cat,code,name,builder,dims,'PA12（密度1010kg/m3设计假设）','卡扣为名义装配态；变形、打印方向、公差、保持力与疲劳须试样验证。钢垫圈传递预紧载荷，底盖只定位、防转和承接松开后的螺母。')
            row=next(r for r in cat if r['id']==code);d=cast(sw.OpenDoc6(row['path'],1,1,'',0,0)[0],'IModelDoc2');bs=body_list(d)
            errors=[f.Name for f in features(d) if f.GetErrorCode2()[0]];assert len(bs)==1 and not errors
            volume=sum(b.GetMassProperties(1)[3] for b in bs)*1e9
            color(d,(.86,.88,.82) if code.startswith('H08') else (.12,.16,.17));save(d,row['path']);preview(d,name)
            save(d,ROOT/'exports/step'/(Path(row['path']).stem+'.STEP'))
            records.append({'编号':code,'名称':name,'体积_mm3':volume,'质量_g_密度假设':volume*.00101,'实体数':1,'重建错误':errors,'文件':row['path']})
            sw.CloseDoc(d.GetTitle());d=None
        p=ROOT/'validation/头部螺母防落零件检查.json';old=json.loads(p.read_text(encoding='utf-8')) if p.exists() else [];ids={r['编号'] for r in records};p.write_text(json.dumps([r for r in old if r['编号'] not in ids]+records,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(records,ensure_ascii=False,indent=2))
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
