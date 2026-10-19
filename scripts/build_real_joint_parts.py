from build_mechanism_parts import *

BACK_ANGLES=(0,60,120,240,300)
OUTPUT_ANGLES=(-90,30,150)
def polar_holes(radius,angles,diameter):return [(radius*math.cos(math.radians(a)),radius*math.sin(math.radians(a)),diameter) for a in angles]


def stator_adapter(d):
    def outline(sm):
        roundrect(sm,64,64,10)
        for x,y,dia in polar_holes(22.5,BACK_ANGLES,2.9)+pattern(0,0,50,3.4)+[(0,0,22)]:sm.CreateCircleByRadius(x/1000,y/1000,0,dia/2000)
    sketch(d,'定子端安装盘_五孔与框架四孔',outline);extrude(d,'安装盘_厚3',3);chamfer_top(d,.2)


def output_adapter(d):
    profile(d,'输出转换盘_厚6',48,polar_holes(13.5,OUTPUT_ANGLES,2.9)+pcd(0,0,r=19,d=2.5)+[(0,0,8.2)],6)
    def recess(sm):
        for x,y,dia in polar_holes(13.5,OUTPUT_ANGLES,5.2):sm.CreateCircleByRadius(x/1000,y/1000,0,dia/2000)
    sketch(d,'三处螺钉与垫圈沉孔_草图',recess);cut(d,'直径5_2沉孔_深3_2',3.2,2.8)
    chamfer_top(d,.2)


def tangential_link(d,L):
    # Circular end lobes meet the concave transitions tangentially; transition meets the straight waist tangentially.
    R=24;w=14;r=30;cx=w+r;cy=-math.sqrt((R+r)**2-cx**2)
    px=R*cx/(R+r);py=R*cy/(R+r)
    angle=math.atan2(py-cy,px-cx);half=(angle+math.pi)/2;mid=(cx+r*math.cos(half),cy+r*math.sin(half))
    def contour(sm):
        arc(sm,(-px,py),(px,py),(0,R))
        arc(sm,(px,py),(w,cy),mid)
        line(sm,(w,cy),(w,-L-cy))
        arc(sm,(w,-L-cy),(px,-L-py),(mid[0],-L-mid[1]))
        arc(sm,(px,-L-py),(-px,-L-py),(0,-L-R))
        arc(sm,(-px,-L-py),(-w,-L-cy),(-mid[0],-L-mid[1]))
        line(sm,(-w,-L-cy),(-w,cy))
        arc(sm,(-w,cy),(-px,py),(-mid[0],mid[1]))
        for x,y,dia in pcd(0,0,r=19)+pcd(0,-L,r=19)+[(0,0,8.2),(0,-L,8.2)]:sm.CreateCircleByRadius(x/1000,y/1000,0,dia/2000)
        sm.CreateEllipse(0,-L/2000,0,0,(-L/2+L*.23)/1000,0,.006,-L/2000,0)
    sketch(d,'相切圆弧收腰轮廓_孔圆直径38',contour);extrude(d,'轻量承载连杆_厚5',5);chamfer_top(d,.3)


def screw25(d):
    profile(d,'M2_5公称螺杆_长8',2.5,(),8,-8);profile(d,'内六角圆柱头',4.5,(),2.5)
    pts=[(1/math.cos(math.pi/6)*math.cos(k*math.pi/3),1/math.cos(math.pi/6)*math.sin(k*math.pi/3)) for k in range(6)]
    sketch(d,'内六角对边2_草图',lambda sm:polygon(sm,pts));cut(d,'内六角孔_深1_2',1.2,1.3)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.CommandInProgress=True;cat=json.loads(CAT_PATH.read_text(encoding='utf-8'))
    try:
        add_part(sw,cat,'J05_AK4510StatorAdapter','AK45-10定子安装盘',stator_adapter,'64×64×3，圆角R10；5×直径2.9在分度圆45上；4×直径3.4在50方孔上；中心直径22',notes='五孔角度0、60、120、240、300度，对应厂家后端盖真实孔位；禁止改成等分五孔。M2.5×8加0.5垫圈理论旋入4.5，实际有效螺纹深度须确认。')
        add_part(sw,cat,'J06_AK4510OutputAdapter','AK45-10输出转换盘',output_adapter,'直径48×6；3×直径2.9在分度圆27上；沉孔直径5.2深3.2；4×M3底孔2.5在分度圆38上',notes='三孔角度-90、30、150度。沉孔内装M2.5×8与0.5垫圈；理论旋入4.7，螺钉顶面低于上表面0.2。连杆M3×10加垫圈理论旋入4.5；螺钉长度须按实物有效牙深复核。')
        for code,L in [('L01_UpperLink',145),('L02_LowerLink',145),('A01_ArmLink',120)]:
            revise(sw,cat,code,lambda d,L=L:tangential_link(d,L),f'轴距{L}；端部外径48；腰宽28；厚5；两端各4×直径3.4，分度圆38；中心孔8.2', '端部R24与收腰R30圆弧相切，直腰过渡相切；配合AK45-10输出转换盘。孔系已由概念版PCD30修订为PCD38，旧工程图需要更新。')
        add_part(sw,cat,'S04_M25x8','M2.5×8内六角螺钉',screw25,'M2.5×8；头径4.5高2.5；内六角对边2','钢（强度等级待选）','GB/T 70.1-2008尺寸系列。螺纹以公称实体表示；采购前确认强度等级和长度库存。')
        add_part(sw,cat,'S05_M25Washer','M2.5平垫圈',lambda d:profile(d,'平垫圈',6,[(0,0,2.7)],.5),'内径2.7、外径6、厚0.5','钢（设计假设）','GB/T 97.1-2002公称2.5尺寸系列；用于定子安装盘背側。')
        add_part(sw,cat,'S06_M25SmallWasher','M2.5小平垫圈',lambda d:profile(d,'小平垫圈',5,[(0,0,2.7)],.5),'内径2.7、外径5、厚0.5','钢（设计假设）','GB/T 848-2002公称2.5尺寸系列；用于输出转换盘沉孔。厂家尺寸来源 https://www.wqjgj.cn/product/dianquan/pingdian/7985.html 。未按模型创建采购订单。')
        for code in ('S04_M25x8','S05_M25Washer','S06_M25SmallWasher'):next(r for r in cat if r['id']==code)['kind']='standard_simplified'
        CAT_PATH.write_text(json.dumps(cat,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CommandInProgress=False
