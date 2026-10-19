"""独立减重候选与宠物护罩，保留已审计基线；每件保存、检查、关闭。"""
from build_mechanism_parts import *

def light_belly(d):
    def outline(sm):
        roundrect(sm,320,190,22)
        for x in (-117,-39,39,117):
            for y in (-42,42):roundrect(sm,66,60,9,x,y)
        for x in (-142,-100,-60,60,100,142):
            for y in (-88,88):sm.CreateCircleByRadius(x/1000,y/1000,0,.0017)
        for x in (-78,78):
            for y in (-80,-40,0,40,80):sm.CreateCircleByRadius(x/1000,y/1000,0,.0017)
    sketch(d,'周边承载环_三条横向连接带_八个圆角减重窗',outline)
    extrude(d,'承载薄板_厚2_5',2.5);chamfer_top(d,.2)

def light_deck(d):
    def outline(sm):
        roundrect(sm,220,190,14)
        for x in (-65,65):roundrect(sm,70,64,8,x,0)
        roundrect(sm,40,64,8)
        for y in (-72,72):roundrect(sm,170,20,8,0,y)
        for x in (-100,-60,60,100):
            for y in (-88,88):sm.CreateCircleByRadius(x/1000,y/1000,0,.0017)
        for x in (-50,0,50):
            for y in (-45,45):sm.CreateCircleByRadius(x/1000,y/1000,0,.0017)
    sketch(d,'储物导轨双承载带_五个减重窗',outline)
    extrude(d,'上层薄板_厚2',2);chamfer_top(d,.2)

def body_lower(d):
    loft(d,'机身下壳_四截面圆润过渡',[(0,lambda sm:roundrect(sm,316,190,38)),(10,lambda sm:roundrect(sm,330,210,40)),(48,lambda sm:roundrect(sm,340,224,45)),(65,lambda sm:roundrect(sm,332,218,42))])
    shell_open_end(d,65,2.2)
    def support(sm):
        roundrect(sm,332,218,42);roundrect(sm,322.6,208.6,37.3)
    sketch(d,'接缝内台阶_底座',support);extrude(d,'接缝台阶_厚1',1,64)
    def tongue(sm):
        roundrect(sm,326.6,212.6,39.3);roundrect(sm,322.6,208.6,37.3)
    sketch(d,'止口定位唇_轮廓',tongue);extrude(d,'止口定位唇_高3',3,65)
    def leg_slots(sm):
        for x in (-112,112):sm.CreateCircleByRadius(x/1000,-.044,0,.036)
    sketch(d,'四髋关节运动避空_直径72预留',leg_slots,index=1);cut(d,'左右贯通髋部避空_待最终电机扫掠校核',300,-150)
    def bosses(sm):
        for x in (-78,78):
            for y in (-80,80):sm.CreateCircleByRadius(x/1000,y/1000,0,.005)
    sketch(d,'底板四支承柱_轮廓',bosses);extrude(d,'底板支承柱_顶面15_3',13.3,2)
    def holes(sm):
        for x in (-78,78):
            for y in (-80,80):sm.CreateCircleByRadius(x/1000,y/1000,0,.00125)
    sketch(d,'支承柱M3攻丝底孔_样机',holes);cut(d,'柱顶盲孔_深10_3',10.3,5)

def body_upper(d):
    loft(d,'机身背盖_拱形曲面',[(0,lambda sm:roundrect(sm,332,218,42)),(15,lambda sm:roundrect(sm,323,209,43)),(30,lambda sm:roundrect(sm,306,194,48)),(36,lambda sm:roundrect(sm,286,178,52))])
    shell_open_end(d,0,2.2)
    sketch(d,'定位止口恒截面避空_单边0_6',lambda sm:roundrect(sm,327.8,213.8,39.9))
    cut(d,'止口插入区避空_顶端余量0_6',3.3,-.3)
    sketch(d,'储物舱可拆窗口_圆角20',lambda sm:roundrect(sm,172,132,20));cut(d,'储物舱贯通检修口',60,-5)
    sketch(d,'头部颈轴走线口_直径50',lambda sm:sm.CreateCircleByRadius(.125,0,0,.025));cut(d,'头颈贯通避空',60,-5)
    # Keep module clearance, service seams, and vent radii visible as deliberate flat/curved transitions.
    def vents(sm):
        for x in (-63,-42,-21,0,21,42,63):
            for y in (-88,88):
                # A capsule has two lines and two semicircles, no zero-length end lines.
                line(sm,(x-4.5,y-1.5),(x+4.5,y-1.5))
                arc(sm,(x+4.5,y-1.5),(x+4.5,y+1.5),(x+6,y))
                line(sm,(x+4.5,y+1.5),(x-4.5,y+1.5))
                arc(sm,(x-4.5,y+1.5),(x-4.5,y-1.5),(x-6,y))
    # FullyDefineSketch on 14 repeated capsules hung in the dimension solver.
    # These construction coordinates are fixed; dimensions remain generator parameters.
    plane(d,0);sm=cast(d.SketchManager,'ISketchManager');sm.InsertSketch(True)
    sm.AddToDB=True
    try:vents(sm)
    finally:sm.AddToDB=False
    active=cast(sm.ActiveSketch,'ISketch');segments=active.GetSketchSegments() or []
    assert len(segments)==56,('vent segments',len(segments))
    d.ClearSelection2(True)
    for i,segment in enumerate(segments):
        assert cast(segment,'ISketchSegment').Select4(i>0,None)
    d.SketchAddConstraints('sgFIXED');d.ClearSelection2(True);sm.InsertSketch(True)
    f=[x for x in features(d) if x.GetTypeName2()=='ProfileFeature'][-1]
    f.Name='背部圆头散热槽_坐标固定_尺寸由生成参数控制';f.Select2(False,0)
    cut(d,'散热槽贯通',60,-5)

def cheek(d):
    loft(d,'关节外罩_鼓形曲面',[(0,ellipse(63,63)),(6,ellipse(67,67)),(16,ellipse(57,57)),(20,ellipse(43,43))])
    shell_open_end(d,0,1.8)
    sketch(d,'轴心检修孔_直径12',lambda sm:sm.CreateCircleByRadius(0,0,0,.006));cut(d,'轴心检修孔贯通',30,-2)

def short_side_channel(d):
    yz=[(-5,0),(5,0),(5,2.5),(-2.5,2.5),(-2.5,51.5),(5,51.5),(5,54),(-5,54)]
    profile(d,'槽梁截面_端部避让曲面壳体',[(-z,y) for y,z in yz],(),300,-150,index=2)
    def holes(sm):
        for x in (-142,-100,-60,60,100,142):sm.CreateCircleByRadius(x/1000,.001,0,.0017)
    sketch(d,'上下翼缘M3连接孔',holes);cut(d,'M3贯穿上下翼缘_配压缩隔套',both=True)
    chamfer_top(d,.3)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');print('连接后台SolidWorks',flush=True);sw=connect();print('SW已连接',sw.RevisionNumber(),flush=True);cat=json.loads(CAT_PATH.read_text(encoding='utf-8'))
    background='--background' in sys.argv
    if background:
        import refine_curved_parts as refine_module
        refine_module.preview=lambda *a,**k:False
        # Keep the document active internally. Invisible documents/app windows failed
        # in this installed SW build; minimized main frame does not take keyboard input.
        sw.FrameState=C.swWindowMinimized
        sw.Visible=True
        sw.FrameState=C.swWindowMinimized
        sw.DocumentVisible(True,1)
    audit_path=ROOT/'validation/减重框架与护壳检查.json'
    sw.CommandInProgress=True;out=json.loads(audit_path.read_text(encoding='utf-8')) if audit_path.exists() else []
    requested={x for x in sys.argv[1:] if not x.startswith('--')}
    items=[
      ('F10_LightBelly','镂空下承载板',light_belly,'320×190×2.5；外角R22；8×66×60圆角窗；侧梁孔Y=±88','6061-T6 铝合金（设计假设）','独立减重候选；保留横梁连接带；不是原F01等刚度替换。须在真实腿安装位置冻结后做屈曲、扭转及冲击校核。'),
      ('F11_LightDeck','双承载带上板',light_deck,'220×190×2；导轨孔X=-50/0/50、Y=±45；侧梁孔Y=±88','6061-T6 铝合金（设计假设）','储物导轨下方保留连续承载带；独立候选，最终全机孔位尚未冻结。'),
      ('F12_ShortSideRail','端部避空承载槽梁',short_side_channel,'300×10×54；壁2.5；X=±142/±100/±60处D3.4孔；孔端距8','6061-T6 铝合金（设计假设）','匹配F10/F11；槽梁端部缩短避让背盖。上下翼缘夹紧需49mm压缩隔套，主载荷与紧固校核待完成。'),
      ('B01_LowerBody','圆润机身下护壳',body_lower,'最大外廓约340×224×68；壁2.2；四髋避空D72；支承顶面Z15.3','PA12（设计假设）','非主承载护壳。止口高3，背盖装配基准Z65.6，名义径向间隙约0.5。M3塑料攻丝仅样机；正式版嵌件、卡扣与工艺收缩待校核。'),
      ('B02_UpperBody','拱形机身背盖',body_upper,'332×218×36；主体壁2.2；止口避空327.8×213.8R39.9深3；舱口172×132R20；颈口D50','PA12（设计假设）','需在下壳Z65.6安装；止口局部减薄，需按打印工艺校核最小壁厚。储物舱和颈轴保留开口。末端紧固和全行程碰撞未完成。'),
      ('B03_JointCover','鼓形关节护罩',cheek,'最大外径约67；深20；壁1.8；检修孔D12','PA12（设计假设）','统一宠物外观的关节护罩候选；不能作为已选电机罩或轴向支承使用。')]
    try:
        for code,name,builder,dims,mat,notes in items:
            if requested and code not in requested:continue
            print('开始零件',code,name,flush=True)
            add_part(sw,cat,code,name,builder,dims,mat,notes)
            row=next(x for x in cat if x['id']==code)
            d=cast(sw.OpenDoc6(row['path'],1,1,'',0,0)[0],'IModelDoc2')
            errs=[(f.Name,f.GetErrorCode2()) for f in features(d) if f.GetErrorCode2()[0]]
            vol=sum(b.GetMassProperties(1)[3] for b in body_list(d));rho=2700 if code.startswith('F') else 1010
            out=[r for r in out if r['编号']!=code]
            out.append({'编号':code,'名称':name,'实体数':len(body_list(d)),'重建错误':errs,'体积_mm3':vol*1e9,'密度假设_kg_m3':rho,'估计质量_g':vol*rho*1000,'文件':row['path']})
            assert not errs,(code,errs)
            color(d,(.87,.88,.82) if code.startswith('B0') else (.24,.40,.43))
            save(d,row['path'])
            if not background:preview(d,name)
            sw.CloseDoc(d.GetTitle())
            (ROOT/'validation/减重框架与护壳检查.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
            print('AUDIT',out[-1],flush=True)
    finally:
        sw.CommandInProgress=False
        if background:
            sw.DocumentVisible(True,1)
            # Keep the app in background while the user is working in another application.
