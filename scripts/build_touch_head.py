"""Curved head with measured vendor touch panel mounting interface; revision candidate."""
from build_integrated_cargo_deck import *

PANEL_ROT=(0,1,0,-1,0,0,0,0,1)
SCREEN_HOLES=[(x,y) for x in (-29.35,30.12) for y in (8.45,-32.45)]
MOUNT_HOLES=[(x,y) for x in (-39,39) for y in (-28,28)]
BEZEL_HOLES=[(x,y) for x in (-47,47) for y in (-20,20)]

def holes(sm,pts,diam):
    for x,y in pts:sm.CreateCircleByRadius(x/1000,y/1000,0,diam/2000)

def head_shell(d):
    loft(d,'头壳_圆角平面过渡曲面',[(0,lambda s:roundrect(s,80,70,26)),(10,lambda s:roundrect(s,104,92,24)),(40,lambda s:roundrect(s,108,100,22)),(60,lambda s:roundrect(s,104,96,20))])
    shell_open_end(d,60,2.5)
    sketch(d,'屏幕支架环形承托肩',lambda s:(roundrect(s,102,90,18),roundrect(s,70,58,14)))
    extrude(d,'内承托肩厚2_5_顶49_2',2.5,46.7)
    sketch(d,'面框平面连接止口',lambda s:(roundrect(s,104,96,20),roundrect(s,90,82,15)))
    extrude(d,'面框连接止口厚3',3,57)
    sketch(d,'支架连接M3贯穿孔',lambda s:holes(s,MOUNT_HOLES,3.4));cut(d,'支架环肩四通孔',2.5,46.7)
    sketch(d,'面框连接M2_5贯穿孔',lambda s:holes(s,BEZEL_HOLES,2.9));cut(d,'面框止口四通孔',3,57)
    sketch(d,'后壁颈部接口与穿线口',lambda s:(s.CreateCircleByRadius(0,0,0,.009),holes(s,[(15,0),(-15,0),(0,15),(0,-15)],3.4)))
    cut(d,'后壁穿线与颈部预留连接孔',2.5,0)
    from sw_drawings import circle_edge
    d.ClearSelection2(True);e=circle_edge(d,(0,0,0),9);assert cast(e,'IEntity').Select4(False,None)
    f=cast(d.FeatureManager,'IFeatureManager').InsertFeatureChamfer(0,1,.0003,math.pi/4,0,0,0,0)
    assert f,'rear cable opening chamfer';cast(f,'IFeature').Name='后壁穿线口去锐边C0_3';d.ClearSelection2(True)

def bezel(d):
    sketch(d,'圆角面框与触控屏全玻璃避空',lambda s:(roundrect(s,104,96,20),roundrect(s,72.3,53.9,3.5,0,-12),s.CreateCircleByRadius(0,.03,0,.008),holes(s,BEZEL_HOLES,2.9)))
    extrude(d,'齐平触控面框厚2_2',2.2)
    sketch(d,'柔性密封圈背面限位沉台',lambda s:roundrect(s,76.7,58.3,5.7,0,-12));cut(d,'密封圈承边沉台深1_2',1.2,0)
    sketch(d,'柔性圈背装防脱薄唇',lambda s:(roundrect(s,76.7,58.3,5.7,0,-12),roundrect(s,75.3,56.9,5,0,-12)))
    extrude(d,'密封圈限位薄唇厚0_6',.6)
    # Only bevel the exterior and screw-hole edges; keep the screen-seal border flush.
    d.ClearSelection2(True);edges=[]
    for raw in body_list(d)[0].GetEdges():
        e=cast(raw,'IEdge');a=e.GetStartVertex();b=e.GetEndVertex()
        if not a or not b:continue
        a=cast(a,'IVertex').GetPoint();b=cast(b,'IVertex').GetPoint()
        if abs(a[2]-.0022)<1e-7 and abs(b[2]-.0022)<1e-7 and (max(abs(a[0]),abs(b[0]))>.040 or max(abs(a[1]),abs(b[1]))>.042):edges.append(e)
    for i,e in enumerate(edges):assert cast(e,'IEntity').Select4(i>0,None)
    f=cast(d.FeatureManager,'IFeatureManager').InsertFeatureChamfer(0,1,.00025,math.pi/4,0,0,0,0);assert f;cast(f,'IFeature').Name='面框外缘柔和倒角C0_25';d.ClearSelection2(True)

def screen_seal(d):
    # Installed nominal shape. Free-state interference and silicone hardness remain sample decisions.
    sketch(d,'密封圈背部防脱承边',lambda s:(roundrect(s,76.3,57.9,5.5,0,-12),roundrect(s,71.3,52.9,3,0,-12)))
    extrude(d,'柔性承边厚0_6',.6)
    sketch(d,'齐平黑色柔性收口唇',lambda s:(roundrect(s,72.3,53.9,3.5,0,-12),roundrect(s,71.3,52.9,3,0,-12)))
    extrude(d,'收口唇高1',1,.6)

def screen_bracket(d):
    sketch(d,'屏幕圆角承架_厂家孔轴与通风口',lambda s:(roundrect(s,88,84,20),roundrect(s,50,32,4,0,-12),holes(s,SCREEN_HOLES,2.9),holes(s,MOUNT_HOLES,3.4)))
    extrude(d,'屏幕承架厚2',2)
    # Camera mounting remains a replaceable insert; this opening is an explicit keep-out.
    sketch(d,'摄像板可换安装区26乘25',lambda s:roundrect(s,26,25,2,0,30));cut(d,'摄像板安装区避空',both=True)
    sketch(d,'四处隐藏扎带应力释放槽',lambda s:[roundrect(s,2.5,10,1,x,y) for x in (-38,38) for y in (-16,0)])
    cut(d,'内侧走线扎带槽贯穿',both=True);assert chamfer_top(d,.2)

PARTS=[('H04_TouchHeadShell','触控视觉曲面头壳',head_shell,'四段圆角放样，深60，壁2.5；前面104×96；承托肩顶Z49.2，安装孔±39/±28；后壁D18穿线','PA12（密度1010kg/m3设计假设）'),('H05_TouchBezel','触控屏与镜头圆角面框',bezel,'104×96×2.2 R20；屏口72.3×53.9；背面沉台76.7×58.3深1.2；防脱薄唇厚0.6','PA12（密度1010kg/m3设计假设）'),('H06_ScreenBracket','触控屏承架与隐藏走线槽',screen_bracket,'88×84×2 R20；屏孔X=-29.35/30.12，Y=8.45/-32.45，D2.9；安装孔±39/±28 D3.4','6061-T6 铝合金（密度2700kg/m3设计假设）'),('H07_ScreenSeal','触控屏齐平柔性密封圈',screen_seal,'装配态：内71.3×52.9 R3；唇外72.3×53.9 R3.5；承边外76.3×57.9 R5.5；总高1.6','黑色硅胶（密度1100kg/m3设计假设）')]

def main():
    sw=connect();sw.FrameState=C.swWindowMinimized;sw.Visible=True;sw.FrameState=C.swWindowMinimized;sw.DocumentVisible(True,1);sw.DocumentVisible(True,2);sw.CommandInProgress=True
    cat=json.loads(CAT_PATH.read_text(encoding='utf-8'));audit=[];d=None
    try:
        if '--assembly-only' not in sys.argv:
            for code,name,builder,dims,mat in PARTS:
                if len(sys.argv)>1 and not any(s.startswith('--') for s in sys.argv[1:]) and code.split('_')[0] not in sys.argv[1:]:continue
                notes='装配态名义几何；自由态过盈量、硅胶硬度及压缩量待试样验证，不能据此直接开模。' if code.startswith('H07') else '玻璃与面框齐平，黑色柔性圈收口。屏幕孔位来自厂家STEP；相机、散热与颈部线缆待定型。未制造释放。'
                add_part(sw,cat,code,name,builder,dims,mat,notes)
        rows={r['id']:r for r in cat}
        for code,_,_,_,_ in PARTS:
            if code not in rows:return
            r=rows[code];doc=cast(sw.OpenDoc6(r['path'],1,1,'',0,0)[0],'IModelDoc2');bs=body_list(doc);errs=[f.Name for f in features(doc) if f.GetErrorCode2()[0]]
            assert len(bs)==1 and not errs,(code,errs)
            volume=sum(b.GetMassProperties(1)[3] for b in bs)*1e9;assert volume>1
            color(doc,{'H04_TouchHeadShell':(.86,.88,.82),'H05_TouchBezel':(.055,.065,.075),'H06_ScreenBracket':(.67,.72,.75),'H07_ScreenSeal':(.025,.025,.03)}[code]);save(doc,r['path'])
            save(doc,ROOT/'exports/step'/(Path(r['path']).stem+'.STEP'))
            audit.append({'编号':code,'实体数':len(bs),'重建错误':errs,'体积_mm3':volume,'质量_g_材料密度假设':volume*(.0027 if code.startswith('H06') else .0011 if code.startswith('H07') else .00101)});sw.CloseDoc(doc.GetTitle())
        d=newdoc(sw,'asm');plan=[('H04_TouchHeadShell','曲面头壳',(0,0,0),IDENTITY),('H05_TouchBezel','触控与相机面框',(0,0,60),IDENTITY),('H06_ScreenBracket','屏幕承架',(0,0,49.2),IDENTITY),('V03_DsiScreen','厂家触控屏',(-2,-12,61.1),PANEL_ROT),('H07_ScreenSeal','齐平柔性密封圈',(0,0,60.6),IDENTITY)]
        root=None;poses=[]
        for code,name,xyz,rot in plan:
            c=add(sw,d,rows[code]['path'],name,xyz,rot)
            if root is None:root=c
            else:mate_pose(d,root,c,xyz,rot,name)
            poses.append({'零件':code,'目标_mm':xyz,'实际变换':list(c.Transform2.ArrayData)})
        clashes=interferences(d);errors=[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]]
        out=ROOT/'assemblies/触控视觉头部_空间与安装候选.SLDASM';save(d,out);preview(d,'触控视觉头部_空间与安装候选')
        result={'阶段':'头部空间与安装候选；尚未装入紧固件和相机板','零件':audit,'配合数':len(list(all_mates(d))),'配合错误':errors,'装配变换':poses,'干涉':clashes,'厂家屏幕原坐标到头部':'X=-厂家Y-2，Y=厂家X-12，Z=厂家Z+61.1，mm','安装支承':'厂家四螺柱端面Z=-9.9变换后Z51.2；承架顶Z51.2；环肩顶与承架底同为Z49.2','未完成':['四个屏螺柱内孔仅D1.76，与M2.5名称的螺纹底孔口径不一致；拧入深度待厂家/实物核验','M3/M2.5紧固件、工具进入路径与防掉落结构未完成','摄像头26×25区域只是避空，镜头D16为可换面框预留，不代表视场无遮挡验证','控制模块和散热未装入；12cm屏线的实际路由与动态弯曲未验证','隐藏扎带槽用于应力释放，线束模型尚未创建','未与整机颈部、储物舱和机械臂做全运动干涉复核']}
        (ROOT/'validation/触控视觉头部候选检查.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
        assert not errors and not clashes
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
