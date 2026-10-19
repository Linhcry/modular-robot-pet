from refine_curved_parts import *

def add_part(sw,cat,code,name,builder,dims,material='6061-T6 铝合金（设计假设）',notes=''):
    row=next((x for x in cat if x['id']==code),None)
    if not row:
        row={'id':code,'name':name,'kind':'custom','path':str(ROOT/'parts'/f"{code.split('_')[0]}_{name}.SLDPRT"),'material_assumption':material,'key_dimensions_mm':dims,'notes':notes,'solid_count':1};cat.append(row)
    row['material_assumption']=material
    revise(sw,cat,code,builder,dims,notes)

def rail(d):
    pts=[(-10,0),(10,0),(10,2),(5,2),(7,8),(-7,8),(-5,2),(-10,2)]
    profile(d,'燕尾导轨截面',pts,(),130)
    def holes(sm):
        for z in (15,65,115):sm.CreateCircleByRadius(0,-z/1000,0,.0017)
    sketch(d,'导轨安装通孔_草图',holes,index=1);cut(d,'导轨M3间隙通孔',both=True)
    def cb(sm):
        for z in (15,65,115):sm.CreateCircleByRadius(0,-z/1000,0,.0031)
    sketch(d,'螺钉头沉孔_草图',cb,index=1);cut(d,'沉孔_直径6_2深3',3,5)
    chamfer_top(d,.2)

def shoe(d):
    pts=[(-11,2.3),(-5.4,2.3),(-7.5,8.4),(7.5,8.4),(5.4,2.3),(11,2.3),(11,12),(-11,12)]
    profile(d,'燕尾滑靴_避空截面',pts,(),130)
    def holes(sm):
        for z in (25,105):sm.CreateCircleByRadius(0,-z/1000,0,.0015)
    sketch(d,'舱底固定M3孔_草图',holes,index=1);cut(d,'滑靴连接孔_螺纹简化',both=True)
    chamfer_top(d,.2)

def cargo_tab(d):
    cargo(d)
    profile(d,'防退出销连接耳',rect(18,16,cx=83,cy=0,c=3),[(83,0,4.2)],3)
    # Existing four floor holes remain as reserved mounting holes; two hole families are explicit.
    def holes(sm):
        for x in (-40,40):
            for y in (-45,45):sm.CreateCircleByRadius(x/1000,y/1000,0,.0017)
    sketch(d,'滑靴连接孔_草图',holes);cut(d,'四孔连接燕尾滑靴',both=True)

def fixed_hinge(d):
    profile(d,'固定页_外壁安装面',rect(36,18,cy=9),[(x,10,3.4) for x in (-10,10)],3,0,index=1)
    for x in (-18,6):
        def draw(sm):
            sm.CreateCircleByRadius(0,.005,0,.004)
            sm.CreateCircleByRadius(0,.005,0,.0021)
        sketch(d,'双耳铰座轴孔'+str(x),draw,index=2);extrude(d,'双耳轴套'+str(x),12,x)

def moving_hinge(d):
    profile(d,'舱盖铰接页',rect(11,27,cy=-8.5),[(0,-14,3.4)],3,3)
    def draw(sm):
        sm.CreateCircleByRadius(0,.005,0,.004);sm.CreateCircleByRadius(0,.005,0,.0021)
    sketch(d,'活动页轴孔',draw,index=2);extrude(d,'中间铰接轴套',11,-5.5)

def pull_pin(d):
    profile(d,'防退出定位杆',4,(),15)
    profile(d,'轴向止挡肩',8,(),3,15)
    loft(d,'圆润拉拔帽',[(18,ellipse(8,8)),(21,ellipse(12,12)),(24,ellipse(8,8)),(25,ellipse(2,2))])
    chamfer_top(d,.2)

def side_channel(d):
    # Right-plane coordinates are (-Z,Y); extrusion follows X.
    yz=[(-5,0),(5,0),(5,2.5),(-2.5,2.5),(-2.5,51.5),(5,51.5),(5,54),(-5,54)]
    profile(d,'轻量槽梁截面',[(-z,y) for y,z in yz],(),312,-156,index=2)
    def holes(sm):
        for x in (-142,-100,-60,60,100,142):sm.CreateCircleByRadius(x/1000,.001,0,.0017)
    sketch(d,'上下翼缘连接孔',holes);cut(d,'M3贯穿上下翼缘',both=True)
    chamfer_top(d,.3)

def core_standoff(d):profile(d,'支承隔柱',8,[(0,0,3.4)],35)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();cat=json.loads(CAT_PATH.read_text(encoding='utf-8'));sw.CommandInProgress=True
    try:
        add_part(sw,cat,'Q01_Rail','快拆燕尾导轨',rail,'length130; base20x2; dovetail top14 at height8; 3 x3.4 with6.2x3 counterbores',notes='在底座承担垂直载荷；导轨配合仅保留纵向滑动。间隙为设计值，需按加工工艺试装。')
        add_part(sw,cat,'Q02_Shoe','快拆燕尾滑靴',shoe,'length130; width22; topZ12; cavity side clearance0.3~0.5; roof3.6',notes='上方两处M3螺纹连接舱底；孔距80。M3螺纹以公称直径简化。')
        revise(sw,cat,'C01_CargoShell',cargo_tab,'150x120x48 R16; front tab toX92; 4x3.4 at(+-40,+-45); pin4.2','圆弧舱壁、燕尾滑靴连接、防退出销耳；销用于防止模块沿导轨退出。')
        add_part(sw,cat,'Q03_PinSeat','快拆防退出销座',lambda d:profile(d,'销座',rect(20,20,c=4),[(0,0,4.2)]+[(x,y,3.4) for x,y in ((-6,-6),(6,6))],12),'20x20x12; pin4.2; mounting2x3.4',notes='销座固定于上板；与舱耳同轴。')
        add_part(sw,cat,'Q04_PullPin','圆帽快拆定位销',pull_pin,'shaft4x15; shoulder8x3; rounded pull cap height7','不锈钢杆＋打印拉帽（设计假设）','拆装时先拔销再滑出；最终需防跳脱保持/系绳设计，不将重力保持当成抗跳跃锁止。')
        revise(sw,cat,'C04_HingeLeaf',fixed_hinge,'width36; two barrels12 separated12; bore4.2; OD8; external mounting plate3','双耳固定铰座，轴向间隙每侧0.5mm，配合活动页形成单转动副。')
        add_part(sw,cat,'C05_MovingHinge','舱盖活动铰链页',moving_hinge,'barrel11 long; bore4.2; plate11x27x3; matching fork gap12',notes='与C04构成双耳支承；舱盖闭合时安装面离铰轴6mm。')
        revise(sw,cat,'F03_SideRail',side_channel,'312x10x54; C-channel2.5; 6x3.4 atY1','采用槽形截面减重；上下翼缘的每根贯穿螺钉必须配49mm压缩隔套，防止夹紧时压瘪。')
        add_part(sw,cat,'F07_CompressionSleeve','侧梁压缩隔套',lambda d:profile(d,'压缩隔套',6,[(0,0,3.4)],49),'OD6 / ID3.4 x49',notes='置于上下翼缘之间，传递紧固预紧力；不能省去。')
        add_part(sw,cat,'F08_CoreStandoff','智能核心支承隔柱',core_standoff,'OD8 / ID3.4 x35',notes='位置需随最终计算板孔位调整。')
        def pedestal(d):
            profile(d,'底部安装法兰',rect(64,64,c=6),pattern(0,0,44),4)
            profile(d,'中空承载柱',rect(54,54,c=5),(),46,4,inner=rect(46,46,c=3))
            profile(d,'顶部安装法兰',rect(64,64,c=6),pattern(0,0,44),4,50)
        add_part(sw,cat,'F09_ArmPedestal','机械臂中空安装柱',pedestal,'64x64 flanges; height54; middle wall4',notes='肩部反力通过上下法兰传至框架，内部保留走线空间。')
    finally:sw.CommandInProgress=False
