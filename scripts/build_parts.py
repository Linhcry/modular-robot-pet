"""Native, editable P0 robot components. All dimensions are millimetres.
Vendor actuators are explicitly envelope assumptions, not vendor CAD.
"""
from sw_core import *

CATALOG=[]
def polygon(sm,pts):
    for a,b in zip(pts,pts[1:]+pts[:1]):sm.CreateLine(a[0]/1000,a[1]/1000,0,b[0]/1000,b[1]/1000,0)
def rect(w,h,cx=0,cy=0,c=0):
    x,y=cx-w/2,cy-h/2
    if not c:return [(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
    return [(x+c,y),(x+w-c,y),(x+w,y+c),(x+w,y+h-c),(x+w-c,y+h),(x+c,y+h),(x,y+h-c),(x,y+c)]
def pattern(cx,cy,spacing,d=3.4):return [(cx+x*spacing/2,cy+y*spacing/2,d) for x in (-1,1) for y in (-1,1)]
def pcd(cx,cy,r=15,d=3.4):return [(cx+r,cy,d),(cx-r,cy,d),(cx,cy+r,d),(cx,cy-r,d)]
def profile(d,name,outline,holes=(),depth=4,z=0,index=0,inner=None):
    def draw(sm):
        if isinstance(outline,(int,float)):sm.CreateCircleByRadius(0,0,0,outline/2000)
        else:polygon(sm,outline)
        if inner:polygon(sm,inner)
        for x,y,diam in holes:sm.CreateCircleByRadius(x/1000,y/1000,0,diam/2000)
    f,status=sketch(d,name+'_SK',draw,index)
    extrude(d,name,depth,z)
    return status

def part(sw,code,label,build,material='6061-T6 aluminium (design assumption)',rgb=(.30,.39,.48),dims='',note='',kind='custom'):
    path=ROOT/'parts'/f'{code}.SLDPRT'
    if path.exists():
        print('EXISTS',code,flush=True)
        d=cast(sw.GetOpenDocumentByName(str(path)),'IModelDoc2')
        if d is None:d=cast(sw.OpenDoc6(str(path),1,1,'',0,0)[0],'IModelDoc2')
    else:
        d=newdoc(sw,'part');build(d)
        try:ch=bool(chamfer_top(d,.3))
        except Exception as e:ch=False;print('CHAMFER_SKIP',code,str(e),flush=True)
        color(d,rgb)
        for k,v in {'PartNumber':code,'Description':label,'DesignStatus':'P0 — STRUCTURAL STUDY; NOT RELEASED','MaterialAssumption':material,'KeyDimensions_mm':dims,'DesignNotes':note,'Source':'Original parameterized design; not vendor geometry'}.items():d.AddCustomInfo3('',k,30,v)
        assert len(body_list(d))==1,(code,'not one connected solid')
        save(d,path)
    b=body_list(d)[0]
    feat=[]
    for f in features(d):
        if f.GetTypeName2() in ('Extrusion','Chamfer','Fillet','ProfileFeature','Cut'):
            feat.append({'name':f.Name,'type':f.GetTypeName2(),'error':f.GetErrorCode2()})
    CATALOG.append({'id':code,'name':label,'kind':kind,'path':str(path),'material_assumption':material,'key_dimensions_mm':dims,'notes':note,'bbox_mm':[round(x*1000,3) for x in b.GetBodyBox()],'solid_count':1,'features':feat})
    print('PART_OK',code,label,flush=True)
    sw.CloseDoc(d.GetTitle())
    return d

def run():
    sw=connect();sw.CommandInProgress=True
    try:
        part(sw,'F01_Belly','下承载板',lambda d:profile(d,'LOAD_PLATE',rect(320,190,c=10),pattern(0,0,0) if False else [(x,y,3.4) for x in (-142,-100,-60,60,100,142) for y in (-87,87)]+[(x,y,3.4) for x in (-78,78) for y in (-80,-40,0,40,80)],depth=4),dims='320 x 190 x 4; 22 x diameter 3.4',note='Hole coordinates defined in fully dimensioned sketch; GB/T70.1 M3 clearance assumption.')
        part(sw,'F02_Deck','上承载板',lambda d:profile(d,'DECK',rect(220,190,c=8),[(x,y,3.4) for x in (-100,-60,60,100) for y in (-87,87)]+pattern(0,0,100),depth=3),dims='220 x 190 x 3')
        part(sw,'F03_SideRail','侧承载梁',lambda d:profile(d,'RAIL',rect(312,10),[(x,0,3.4) for x in (-142,-100,-60,60,100,142)],depth=54),dims='312 x 10 x 54; 6 x diameter 3.4',note='Long vertical through bolts; section and weight will be optimized after load calculation.')
        part(sw,'F04_Bulkhead','髋关节安装隔板',lambda d:profile(d,'BULKHEAD',rect(184,54,c=2),pattern(-62,0,44)+pattern(62,0,44)+[(-62,0,26),(62,0,26)],depth=4),dims='184 x 54 x 4; joint centres 124; 8 x diameter 3.4 on 44 square',note='Two actuator mounts. Lower plate contact and brace interfaces need final fastener design.')
        part(sw,'F05_BatteryTray','电池托架',lambda d:(profile(d,'FLOOR',rect(146,76,c=4),pattern(0,0,60),3,0),profile(d,'RIM',rect(146,76,c=4),(),18,3,inner=rect(140,70,c=2))),material='PA12 (design assumption)',rgb=(.17,.20,.24),dims='146 x 76 x 21; inside 140 x 70')
        part(sw,'F06_CoreTray','智能核心托板',lambda d:profile(d,'TRAY',rect(94,76,c=4),pattern(0,0,60),3),material='PA12 (design assumption)',dims='94 x 76 x 3')
        def housing(d):
            profile(d,'MOUNT_FLANGE',rect(54,54,c=4),pattern(0,0,44)+[(0,0,26)],4)
            profile(d,'ACTUATOR_ENVELOPE',44,[(0,0,26)],24,4)
        part(sw,'J01_Housing_ENV','关节定子包络与安装法兰',housing,rgb=(.10,.12,.15),dims='54 square flange; body diameter44 x24; bore26; 4 x diameter3.4 on44',note='Unselected integrated actuator envelope. No claim of motor torque, bearings, thermal or exact vendor interface.',kind='envelope')
        def rotor(d):
            profile(d,'JOURNAL',25.4,[(0,0,8.2)],31,4)
            profile(d,'OUTPUT_FLANGE',38,pcd(0,0)+[(0,0,8.2)],6.5,28.5)
        part(sw,'J02_Output_ENV','关节输出接口包络',rotor,rgb=(.72,.75,.80),dims='diameter25.4 journal; diameter38 flange; 4 x diameter3.4 PCD30; endZ35',note='Rotates in J01 with 0.3 mm radial envelope gap and 0.5 mm axial gap; this is not a designed bearing clearance.',kind='envelope')
        def yoke(d):
            profile(d,'ORTHOGONAL_WALL',rect(54,62,cy=-31,c=2),pattern(0,-35,44)+[(0,-35,26)],6,22,index=1)
            profile(d,'ROLL_INTERFACE',rect(54,54,c=3),pcd(0,0)+[(0,0,8.2)],5,0)
        part(sw,'J03_HipYoke','髋部正交连接座',yoke,dims='54 x55 x62; base5; side6; side axis at Z35',note='Two native extrusions on orthogonal datums; roll output PCD30 to pitch stator 44-square.')
        def link(d,length):
            poly=[(-18,20),(18,20),(20,18),(20,-length-18),(18,-length-20),(-18,-length-20),(-20,-length-18),(-20,18)]
            profile(d,'LINK',poly,pcd(0,0)+pattern(0,-length,44) if False else pcd(0,0)+pcd(0,-length)+[(0,0,8.2),(0,-length,8.2)],5)
        part(sw,'L01_UpperLink','大腿连杆',lambda d:link(d,145),dims='axis spacing145; width40; thickness5; end4 x diameter3.4 PCD30',note='Distal actuator uses adapter J04; support/side-load model pending.',rgb=(.28,.55,.64))
        part(sw,'L02_LowerLink','小腿连杆',lambda d:link(d,145),dims='axis spacing145; width40; thickness5; end4 x diameter3.4 PCD30',rgb=(.32,.59,.67))
        part(sw,'J04_Adapter','30圆周至44方孔转接板',lambda d:profile(d,'ADAPTER',rect(54,54,c=4),pcd(0,0)+pattern(0,0,44)+[(0,0,8.2)],4),dims='54 x54 x4; PCD30 and44-square',note='Two bolt groups require opposite assembly access.')
        part(sw,'L03_FootMount','足端连接板',lambda d:profile(d,'FOOT_ADAPTER',rect(42,48,c=6),pcd(0,0)+[(0,0,8.2)],8),dims='42 x48 x8; 4 x diameter3.4 PCD30')
        part(sw,'L04_FootPad','可换弹性足垫',lambda d:profile(d,'PAD',rect(46,52,c=10),(),12),material='TPU 85A prototype assumption',rgb=(.10,.11,.12),dims='46 x52 x12',note='Pad retained by bonded prototype interface; production mechanical retention pending.')
        def cargo(d):
            profile(d,'CARGO_FLOOR',rect(150,120,c=6),pattern(0,0,100),3)
            profile(d,'CARGO_WALL',rect(150,120,c=6),(),45,3,inner=rect(144,114,c=4))
        part(sw,'C01_CargoShell','储物舱壳体',cargo,material='PA12 prototype assumption',rgb=(.77,.82,.83),dims='150 x120 x48; inside144 x114 x45',note='300g target. Inner usable volume about0.73L before liner; mounting holes need seals if spill resistance required.')
        part(sw,'C02_Lid','储物舱盖',lambda d:profile(d,'LID',rect(154,124,c=7),[(x,55,3.4) for x in (-45,45)],3),material='PA12 prototype assumption',rgb=(.33,.57,.63),dims='154 x124 x3; hinge attachment centres90')
        part(sw,'C03_Tray','储物舱内托盘',lambda d:profile(d,'REMOVABLE_TRAY',rect(136,106,c=5),(),2),material='TPU prototype assumption',rgb=(.22,.25,.28),dims='136 x106 x2',note='Finger ingress and object packaging must be verified against selected gripper.')
        part(sw,'C04_HingeLeaf','舱盖铰链页',lambda d:(profile(d,'LEAF',rect(24,22,cy=-7),[(0,-12,3.4)],3),profile(d,'KNUCKLE',12,[(0,0,4.2)],10,3)),dims='leaf24 x22 x3; barrel OD12 bore4.2 x10',note='Hinge leaf concept; exact mounting angle and lid linkage not frozen.')
        part(sw,'A01_ArmLink','机械臂连杆',lambda d:link(d,120),dims='axis spacing120; width40; thickness5; PCD30',rgb=(.58,.67,.70))
        part(sw,'A02_GripperPalm','夹爪掌板',lambda d:profile(d,'PALM',rect(88,45,c=5),pcd(0,0)+[(-34,0,4.2),(34,0,4.2)],6),dims='88 x45 x6; finger pivot centres68')
        part(sw,'A03_Finger','可换夹爪手指',lambda d:profile(d,'FINGER',[(-8,10),(8,10),(8,-60),(0,-78),(-8,-78)],[(0,0,4.2),(0,-64,3.4)],5),material='PA12-CF prototype assumption',dims='length88; width16; thickness5; pivot4.2',note='Actuation tendon/synchronizer not yet designed; opening shown as concept only.',rgb=(.23,.29,.32))
        part(sw,'A04_FingerPad','夹爪柔性指垫',lambda d:profile(d,'PAD',rect(12,24,c=2),(),3),material='Silicone prototype assumption',rgb=(.09,.10,.12),dims='12 x24 x3')
        def head(d):
            profile(d,'HEAD_BASE',rect(76,68,c=8),pcd(0,0),4)
            profile(d,'HEAD_SHELL',rect(76,68,c=8),(),44,4,inner=rect(70,62,c=6))
        part(sw,'H01_HeadShell','视觉头部壳体',head,material='PA12 prototype assumption',rgb=(.84,.86,.86),dims='76 x68 x48; wall3',note='Front orientation set by assembly; camera internal envelope is provisional.')
        part(sw,'H02_Faceplate','视觉前面罩',lambda d:profile(d,'FACE',rect(76,68,c=8),[(-18,8,18),(18,8,18),(0,-17,5)],3),material='PA12 prototype assumption',rgb=(.12,.15,.18),dims='76 x68 x3; optical windows2 x18; microphone5')
        part(sw,'H03_Lens_ENV','相机镜头包络',lambda d:profile(d,'LENS',16,(),10),material='Camera envelope; mass unknown',rgb=(.12,.36,.44),dims='diameter16 x10',kind='envelope')
        part(sw,'T01_Tail','轻量尾部连杆',lambda d:profile(d,'TAIL',[(-15,18),(15,18),(15,-20),(7,-110),(-7,-110),(-15,-20)],pcd(0,0,r=10,d=3.4),5),material='PA12 prototype assumption',rgb=(.30,.57,.64),dims='128 long; width30→14; thickness5',note='Expression only; not a structural self-righting support.')
        part(sw,'E01_Battery_ENV','电池包络',lambda d:profile(d,'BATTERY_ENVELOPE',rect(132,62,c=3),(),34),material='Unselected battery; no material-based mass',rgb=(.18,.26,.37),dims='132 x62 x34',kind='envelope')
        part(sw,'E02_Compute_ENV','计算板包络',lambda d:profile(d,'COMPUTE_ENVELOPE',rect(86,62,c=2),(),21),material='Unselected compute; no material-based mass',rgb=(.12,.35,.23),dims='86 x62 x21',kind='envelope')
        def bolt(d,L):
            profile(d,'NOMINAL_M3_SHANK',3,(),L,-L)
            profile(d,'HEAD',5.5,(),3,0)
        for L in (10,16,65):part(sw,f'S01_M3x{L}','M3内六角螺钉简化实体',lambda d,L=L:bolt(d,L),material='Steel; grade to be selected',rgb=(.63,.65,.68),dims=f'M3 x{L}; head5.5 x3; GB/T70.1-2008 size family',note='Thread and socket simplified; exact length availability and current standard to be confirmed before purchase.',kind='standard_simplified')
        part(sw,'S02_M3Washer','M3平垫圈简化实体',lambda d:profile(d,'WASHER',7,[(0,0,3.2)],.5),material='Steel',rgb=(.65,.67,.70),dims='3.2 x7 x0.5; GB/T97.1-2002 family',kind='standard_simplified')
        part(sw,'S03_M3Nut','M3螺母简化实体',lambda d:profile(d,'NUT',[(3.175*math.cos(k*math.pi/3),3.175*math.sin(k*math.pi/3)) for k in range(6)],[(0,0,3)],2.4),material='Steel',rgb=(.62,.64,.67),dims='M3; AF5.5; thickness2.4 assumption',note='Non-helical representation. Applicable GB/T standard and nut style not yet frozen.',kind='standard_simplified')
        (ROOT/'data').mkdir(exist_ok=True)
        (ROOT/'data/parts_catalog.json').write_text(json.dumps(CATALOG,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CommandInProgress=False

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');run()
