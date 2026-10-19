from build_captive_head_nuts import *
import hashlib

def rotation(deg):
    a=math.radians(deg);c,s=math.cos(a),math.sin(a);return (c,s,0,-s,c,0,0,0,1)

def place(sw,b,xyz,rot=IDENTITY):
    b=cast(b.Copy(),'IBody2');assert b.ApplyTransform(transform(sw,xyz,rot));return b

def overlap(a,b):
    require_memory('螺母杯单对实体布尔检查')
    r=cast(a.Copy(),'IBody2').Operations2(C.SWBODYINTERSECT,cast(b.Copy(),'IBody2'),0);assert r[1] in (0,5,6,1067),r[1]
    solids=[cast(o,'IBody2') for o in (r[0] or [])];vol=sum(o.GetMassProperties(1)[3] for o in solids)*1e9
    return {'体积_mm3':vol,'区域包围盒_mm':[[v*1000 for v in o.GetBodyBox()] for o in solids]} if vol>1e-5 else None

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True;d=None
    cat={r['id']:r for r in json.loads(CAT_PATH.read_text(encoding='utf-8'))};bodies={};hashes={};paths=[];faults=[]
    try:
        for code in ['H08_CaptiveHeadShell','H09_CaptiveNutCup','S03_M3Nut','S02_M3Washer']:
            require_memory('安装路径加载单件:'+code)
            p=Path(cat[code]['path']);d=cast(sw.OpenDoc6(str(p),1,1,'',0,0)[0],'IModelDoc2');bs=body_list(d);assert len(bs)==1;bodies[code]=cast(bs[0].Copy(),'IBody2');hashes[code]=hashlib.sha256(p.read_bytes()).hexdigest();sw.CloseDoc(d.GetTitle());d=None
        shell=bodies['H08_CaptiveHeadShell'];cup=bodies['H09_CaptiveNutCup'];nut=bodies['S03_M3Nut'];washer=bodies['S02_M3Washer']
        for x,y in MOUNT_HOLES:
            route=[(0,0,z,'穿过前侧中央开口') for z in (64,56,50,44,38,30)]
            route.extend((x*f,y*f,30,'在环肩后方横移') for f in (.25,.5,.75,1))
            route.extend((x,y,z,'沿定位座轴线装入') for z in (33,35,36,37,38,39,39.6))
            for px,py,pz,phase in route:
                hits=[]
                for code,b,offset in [('螺母杯',cup,0),('松放螺母',nut,4),('松放钢垫圈',washer,6.4)]:
                    hit=overlap(place(sw,b,(px,py,pz+offset)),shell)
                    if hit:hits.append({'零件':code,**hit})
                expected=phase=='沿定位座轴线装入' and 36<pz<39.6
                if hits:
                    assert expected and all(h['零件']=='螺母杯' for h in hits),(x,y,px,py,pz,hits)
                    for hit in hits:
                        for box in hit['区域包围盒_mm']:
                            assert min(abs(box[0]-px),abs(box[3]-px))>4.9 and max(abs(box[1]-py),abs(box[4]-py))<1.5 and box[2]>41.9 and box[5]<45.9,('non-hook interference',box)
                paths.append({'目标孔_mm':[x,y],'杯底原点_mm':[px,py,pz],'阶段':phase,'交叠':hits,'解释':'仅卡钩越过定位座侧壁时的预期弹性挠曲区；未模拟变形形状/应力' if hits else '名义刚性几何无交叠'})
            # Bounded geometry checks: a retained cup and nut cannot translate/rotate freely.
            for dz in (-.25,.1):
                hit=overlap(place(sw,cup,(x,y,CAP_Z+dz)),shell);assert hit,(x,y,'axial retention absent',dz)
                faults.append({'目标孔_mm':[x,y],'故意杯轴向越位_mm':dz,'预期限位交叠':hit})
            for angle in (-8,8):
                hit=overlap(place(sw,nut,(x,y,43.8),rotation(angle)),place(sw,cup,(x,y,CAP_Z)));assert hit,(x,y,'nut rotation unrestrained',angle)
                faults.append({'目标孔_mm':[x,y],'故意螺母旋转_deg':angle,'预期防转交叠':hit})
                hit=overlap(place(sw,cup,(x,y,CAP_Z),rotation(angle)),shell);assert hit,(x,y,'cup rotation unrestrained',angle)
                faults.append({'目标孔_mm':[x,y],'故意杯旋转_deg':angle,'预期定位槽防转交叠':hit})
        require_memory('完整头部重开与干涉检查',physical_gib=5,commit_gib=8)
        path=ROOT/'assemblies/触控视觉头部_螺母防落候选.SLDASM';d=cast(sw.OpenDoc6(str(path),2,1,'',0,0)[0],'IModelDoc2');d.ForceRebuild3(False)
        cs=[cast(o,'IComponent2') for o in cast(d,'IAssemblyDoc').GetComponents(True)];mates=list(all_mates(d));errs=[f.Name for f in mates if f.GetErrorCode2()[0]];clashes=interferences(d)
        assert len(cs)==25 and len(mates)==52 and not errs and not clashes
        report={'日期':'2026-09-08','来源原生SHA256':hashes,'重开装配验证':{'组件数':25,'配合数':52,'配合错误':errs,'干涉':clashes},'安装前提':'屏幕、承架及面框未装，杯携带松放螺母及垫圈由前开口进入；拧紧后螺母/垫圈上移0.2mm。','离散安装路径':paths,'几何反例检查':faults,'杯壁名义最薄_mm':4.2-5.7/math.sqrt(3),'弹性臂量级预筛':{'预留径向挠曲_mm':.4,'臂厚_mm':.6,'根部至卡钩肩有效长度_mm':4.2,'简化端载梁外纤维应变':1.5*.4*.6/4.2**2,'意义':'只给形变数量级；未计根部圆角、打印各向异性与大变形，不构成材料/疲劳通过'},'边界':['路径为离散刚性样本；预期卡钩穿越区需要真实弹性变形，尚非连续柔性装配仿真','防掉落/防转结论仅证明名义几何存在止挡，未证明保持力、装入力、打印公差或拆装寿命','拧紧力矩、PA12环肩压溃/蠕变与卡槽反力仍需验证','拆卸时必须从内部释放两侧卡臂；实际工具操作和人手空间未验证','与完整电子、颈部、整机姿态及线缆的干涉仍未覆盖']}
        (ROOT/'validation/头部螺母杯安装路径与限位检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'重开装配验证':report['重开装配验证'],'路径样本数':len(paths),'卡钩预期挠曲样本':sum(bool(r['交叠']) for r in paths),'限位反例数':len(faults),'杯最小壁厚_mm':report['杯壁名义最薄_mm']},ensure_ascii=False,indent=2))
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
