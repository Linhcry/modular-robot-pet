"""Cargo interface revision. Native parts are saved and closed one at a time."""
from build_mechanism_parts import *

def cargo_mounts(d):
    cargo_tab(d)
    def holes(sm):
        for x in (-55,-35,35,55):sm.CreateCircleByRadius(x/1000,-.035,0,.0017)
    sketch(d,'铰链固定页安装孔_草图',holes,index=1)
    cut(d,'后舱壁四个M3间隙孔',both=True)
    for x in (-60,60):
        for y in (-43,43):profile(d,'内托盘支承柱',8,(),4,3) if False else profile(d,'内托盘支承柱',rect(8,8,cx=x,cy=y,c=2),(),4,3)

def lid_mounts(d):
    lid(d)
    for x in (-45,45):
        for y in (45,53):
            def boss(sm,x=x,y=y):
                sm.CreateCircleByRadius(x/1000,y/1000,0,.00375)
                sm.CreateCircleByRadius(x/1000,y/1000,0,.00125)
            sketch(d,'铰链螺纹凸台_草图',boss);extrude(d,'铰链安装凸台_高7',7)
    def taps(sm):
        for x in (-45,45):
            for y in (45,53):sm.CreateCircleByRadius(x/1000,y/1000,0,.00125)
    sketch(d,'M3底孔_草图',taps);cut(d,'M3底孔直径2_5深6_5',6.5)

def moving_leaf(d):
    profile(d,'舱盖铰接页',rect(11,27,cy=-8.5),[(0,-7,3.4),(0,-15,3.4)],3,3)
    def barrel(sm):
        sm.CreateCircleByRadius(0,.005,0,.004);sm.CreateCircleByRadius(0,.005,0,.0021)
    sketch(d,'活动页轴孔',barrel,index=2);extrude(d,'中间铰接轴套',11,-5.5)

def relieved_fixed_leaf(d):
    fixed_hinge(d)
    sketch(d,'活动轴套圆角避让_草图',lambda sm:roundrect(sm,12.4,8,1,cy=2),index=1)
    cut(d,'中间轴套避让口_圆角R1',3.1)

def thick_shoe(d):
    pts=[(-11,2.3),(-5.4,2.3),(-7.5,8.4),(7.5,8.4),(5.4,2.3),(11,2.3),(11,15),(-11,15)]
    profile(d,'燕尾滑靴_避空截面',pts,(),130)
    def holes(sm):
        for z in (25,105):sm.CreateCircleByRadius(0,-z/1000,0,.00125)
    sketch(d,'M3螺纹底孔_草图',holes,index=1);cut(d,'M3底孔直径2_5贯穿顶壁',both=True)
    chamfer_top(d,.2)

def shoulder_pin(d):
    profile(d,'销头',7,(),2)
    profile(d,'直径4光轴_有效长36_5',4,(),36.5,2)
    profile(d,'M3轴端螺纹_公称实体',3,(),5,38.5)

def screw8(d):
    profile(d,'M3螺杆_公称实体',3,(),8,-8)
    profile(d,'内六角圆柱头',5.5,(),3)
    profile_pts=[(1.25/math.cos(math.pi/6)*math.cos(k*math.pi/3),1.25/math.cos(math.pi/6)*math.sin(k*math.pi/3)) for k in range(6)]
    sketch(d,'内六角对边2_5_草图',lambda sm:polygon(sm,profile_pts));cut(d,'内六角孔_深1_5',1.5,1.5)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();cat=json.loads(CAT_PATH.read_text(encoding='utf-8'));sw.CommandInProgress=True
    try:
        revise(sw,cat,'C01_CargoShell',cargo_mounts,'外廓150×120×48；壁厚3；后壁4×直径3.4；内托盘支柱高4','后壁铰链孔坐标X=±35、±55，Z=35；孔轴沿Y。内托盘高于舱底螺钉头。')
        revise(sw,cat,'C02_Lid',lid_mounts,'拱盖154×124×14；抽壳2.5；4个M3安装凸台高7','凸台中心(±45,45)、(±45,55)；M3×0.5底孔直径2.5深6.5，有效螺纹深5.5。采用从活动页下侧安装的M3×8螺钉。')
        revise(sw,cat,'C05_MovingHinge',moving_leaf,'轴套长11，内径4.2；页片11×27×3；2×直径3.4，孔距10','两孔限制铰链页绕紧固螺钉转动；双耳铰座两侧各留0.5轴向间隙。')
        revise(sw,cat,'Q02_Shoe',thick_shoe,'长130；宽22；顶部高度15；承载顶壁6.6；2×M3底孔2.5','M3×8螺钉穿过0.5垫圈与3厚舱底，理论旋入4.5；螺钉端部距导轨顶面2.5，不碰导轨。')
        revise(sw,cat,'Q03_PinSeat',lambda d:profile(d,'销座',rect(20,20,c=4),[(0,0,4.2),(-6,-6,3.4),(6,6,3.4)],15),'20×20×15；中心直径4.2；2×直径3.4','高度随滑靴顶面统一为15；需与舱底连接耳同轴。')
        add_part(sw,cat,'C06_HingePin','舱盖铰链肩销',shoulder_pin,'销头直径7×2；光轴直径4×36.5；轴端M3×5','不锈钢（设计假设）','光轴比固定页外跨36长0.5；螺母压紧光轴肩部，不夹死活动页。螺纹仅用公称实体表示。')
        add_part(sw,cat,'S01_M3x8','M3x8内六角螺钉',screw8,'M3×8；头部直径5.5高3；内六角对边2.5','钢（强度等级待选）','GB/T 70.1-2008尺寸系列；螺纹简化为公称直径实体。')
        next(x for x in cat if x['id']=='S01_M3x8')['kind']='standard_simplified'
        CAT_PATH.write_text(json.dumps(cat,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CommandInProgress=False
