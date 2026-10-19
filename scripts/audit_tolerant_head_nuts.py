from build_tolerant_head_nuts import *
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
        for code in ['H10_ClearanceHeadShell','H11_LongArmNutCup','S03_M3Nut','S02_M3Washer']:
            require_memory('安装路径加载单件:'+code)
            p=Path(cat[code]['path']);d=cast(sw.OpenDoc6(str(p),1,1,'',0,0)[0],'IModelDoc2');bs=body_list(d);assert len(bs)==1;bodies[code]=cast(bs[0].Copy(),'IBody2');hashes[code]=hashlib.sha256(p.read_bytes()).hexdigest();sw.CloseDoc(d.GetTitle());d=None
        shell=bodies['H10_ClearanceHeadShell'];cup=bodies['H11_LongArmNutCup'];nut=bodies['S03_M3Nut'];washer=bodies['S02_M3Washer']
        for x,y in MOUNT_HOLES:
            route=[(0,0,z,'穿过前侧中央开口') for z in (64,56,50,44,38,30)]
            route.extend((x*f,y*f,30,'在环肩后方横移') for f in (.25,.5,.75,1))
            route.extend((x,y,z,'沿定位座轴线装入') for z in (33,34,35,36,37,37.6))
            for px,py,pz,phase in route:
                hits=[]
                for code,b,offset in [('螺母杯',cup,0),('松放螺母',nut,5.6),('松放钢垫圈',washer,8.0)]:
                    hit=overlap(place(sw,b,(px,py,pz+offset)),shell)
                    if hit:hits.append({'零件':code,**hit})
                expected=phase=='沿定位座轴线装入' and 34.1<pz<37.6
                if hits:
                    assert expected and all(h['零件']=='螺母杯' for h in hits),(x,y,px,py,pz,hits)
                    for hit in hits:
                        for box in hit['区域包围盒_mm']:
                            assert min(abs(box[0]-px),abs(box[3]-px))>5.3 and max(abs(box[1]-py),abs(box[4]-py))<1.5 and box[2]>41.9 and box[5]<46.2,('non-hook interference',box)
                paths.append({'目标孔_mm':[x,y],'杯底原点_mm':[px,py,pz],'阶段':phase,'交叠':hits,'解释':'仅卡钩越过定位座侧壁时的预期弹性挠曲区；未模拟变形形状/应力' if hits else '名义刚性几何无交叠'})
            # Bounded geometry checks: a retained cup and nut cannot translate/rotate freely.
            for dz in (-.6,.1):
                hit=overlap(place(sw,cup,(x,y,CAP_Z+dz)),shell);assert hit,(x,y,'axial retention absent',dz)
                faults.append({'目标孔_mm':[x,y],'故意杯轴向越位_mm':dz,'预期限位交叠':hit})
            for angle in (-8,8):
                hit=overlap(place(sw,nut,(x,y,43.8),rotation(angle)),place(sw,cup,(x,y,CAP_Z)));assert hit,(x,y,'nut rotation unrestrained',angle)
                faults.append({'目标孔_mm':[x,y],'故意螺母旋转_deg':angle,'预期防转交叠':hit})
                hit=overlap(place(sw,cup,(x,y,CAP_Z),rotation(angle)),shell);assert hit,(x,y,'cup rotation unrestrained',angle)
                faults.append({'目标孔_mm':[x,y],'故意杯旋转_deg':angle,'预期定位槽防转交叠':hit})
        report={'来源原生SHA256':hashes,'阶段':'H10/H11单件安装路径与几何止挡；未验证完整头部装配',
                '安装前提':'面框、屏幕、承架未安装；杯携带松放螺母和钢垫圈经前开口进入。',
                '离散安装路径':paths,'几何反例检查':faults,
                '名义尺寸':{'直径间隙_mm':.6,'杯底卸载间隙_mm':.6,'卡钩径向扣合量_mm':1.0,'卡槽轴向总间隙_mm':1.0},
                '边界':['离散刚性布尔检查；卡钩通过时只识别预期弹性区域，未模拟变形和应力',
                        '反例使用当前最大包络M3螺母；不能作为所有公差实购螺母的防转验证',
                        '保持力、打印误差、装入力、疲劳和工具释放均未验证',
                        '所有路径需屏幕与承架未装；未宣称整机可直接拆装']}
        (ROOT/'validation/长臂螺母杯安装路径检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'路径样本数':len(paths),'卡钩预期挠曲样本':sum(bool(r['交叠']) for r in paths),'限位反例数':len(faults)},ensure_ascii=False,indent=2))
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
