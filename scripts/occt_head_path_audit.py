"""Low-memory STEP audit. Native SW mates/drawings still require SW validation."""
from pathlib import Path
import json, math, hashlib, tempfile, shutil, gc
import win32api, win32process
from sw_memory import require_memory
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_FACE
from OCP.TopTools import TopTools_ListOfShape
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism
from OCP.gp import gp_Trsf, gp_Ax1, gp_Pnt, gp_Dir, gp_Vec

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'validation/长臂螺母杯_STEP独立安装路径检查.json'


def gate(stage):
    require_memory('轻量STEP检查:'+stage,physical_gib=2,commit_gib=4)
    assert win32process.GetProcessMemoryInfo(win32api.GetCurrentProcess())['PagefileUsage']<1024**3,'audit process exceeds 1 GiB private memory'


def volume(shape):
    prop=GProp_GProps();BRepGProp.VolumeProperties_s(shape,prop,1e-8,True,False)
    return prop.Mass()


def solids(shape):
    out=[];ex=TopExp_Explorer(shape,TopAbs_SOLID)
    while ex.More():out.append(ex.Current());ex.Next()
    return out


def box(shape):
    b=Bnd_Box();BRepBndLib.AddOptimal_s(shape,b,False,False)
    return list(b.Get())


def read_step(path):
    gate('加载'+path.stem)
    with tempfile.TemporaryDirectory(prefix='pet-brep-') as folder:
        target=Path(folder)/'part.step';shutil.copyfile(path,target)
        reader=STEPControl_Reader();assert reader.ReadFile(str(target))==IFSelect_RetDone
        assert reader.TransferRoots()>0;shape=reader.OneShape()
    assert BRepCheck_Analyzer(shape).IsValid(),path
    assert len(solids(shape))==1,path
    def faces(s):
        ex=TopExp_Explorer(s,TopAbs_FACE);count=0
        while ex.More():count+=1;ex.Next()
        return count
    assert faces(shape)==sum(faces(s) for s in solids(shape)),('STEP contains faces outside solids; do not use as closed geometry',path)
    return shape


def place(shape,xyz,angle=0):
    t=gp_Trsf();t.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(0,0,1)),math.radians(angle))
    t.SetTranslationPart(gp_Vec(*xyz))
    return BRepBuilderAPI_Transform(shape,t,True).Shape()


def overlap(a,b):
    gate('单对实体求交')
    args=TopTools_ListOfShape();args.Append(a)
    tools=TopTools_ListOfShape();tools.Append(b)
    op=BRepAlgoAPI_Common();op.SetArguments(args);op.SetTools(tools)
    op.SetNonDestructive(True);op.SetRunParallel(False);op.Build()
    assert op.IsDone(),'Boolean operation failed'
    result=op.Shape();assert BRepCheck_Analyzer(result).IsValid(),'Invalid Boolean result'
    v=volume(result)
    assert v> -1e-6,('negative common volume',v)
    if v<1e-5:return None
    return {'体积_mm3':v,'区域包围盒_mm':[box(s) for s in solids(result)],'内核检查':'IsDone与结果拓扑检查；当前绑定未暴露警告查询'}


def nut(radius=3.175,height=2.4):
    polygon=BRepBuilderAPI_MakePolygon()
    for k in range(6):polygon.Add(gp_Pnt(radius*math.cos(k*math.pi/3),radius*math.sin(k*math.pi/3),0))
    polygon.Close();face=BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
    full=BRepPrimAPI_MakePrism(face,gp_Vec(0,0,height)).Shape()
    return BRepAlgoAPI_Cut(full,BRepPrimAPI_MakeCylinder(1.5,height).Shape()).Shape()


def main(candidate_path=None):
    global REPORT
    if candidate_path:REPORT=ROOT/'validation/长臂螺母杯_修复STEP候选路径检查.json'
    records=json.loads((ROOT/'validation/长臂螺母杯零件检查.json').read_text(encoding='utf-8'))
    shapes={};sources=[]
    for code in ('H10','H11'):
        r=next(r for r in records if r['编号'].startswith(code+'_'));native=Path(r['文件'])
        p=Path(candidate_path) if code=='H10' and candidate_path else ROOT/'exports/step'/(native.stem+'.STEP')
        s=read_step(p);actual=volume(s)
        equivalent=abs(actual-r['体积_mm3'])<.02
        if not (candidate_path and code=='H10'):assert equivalent,(code,'STEP volume mismatch',actual,r['体积_mm3'])
        sources.append({'零件':code,'STEP':str(p),'STEP_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),
                        '原生SHA256':hashlib.sha256(native.read_bytes()).hexdigest(),'原生记录体积_mm3':r['体积_mm3'],
                        'STEP独立体积_mm3':actual,'原生体积一致门限通过':equivalent,'实体数':len(solids(s)),'拓扑有效':True,'包围盒_mm':box(s)})
        shapes[code]=s
    shell,cup=shapes['H10'],shapes['H11']
    nominal_nut=nut();small_nut=nut(5.32/math.sqrt(3),2.15)
    washer=BRepAlgoAPI_Cut(BRepPrimAPI_MakeCylinder(3.5,.5).Shape(),BRepPrimAPI_MakeCylinder(1.6,.5).Shape()).Shape()
    for s in (nominal_nut,small_nut,washer):assert BRepCheck_Analyzer(s).IsValid()
    # Calibrate both positive and negative intersections before relying on empty results.
    cube=BRepPrimAPI_MakeCylinder(1,1).Shape()
    assert abs(overlap(cube,cube)['体积_mm3']-math.pi)<1e-6
    assert overlap(cube,place(cube,(10,0,0))) is None
    report={'阶段':'进行中','内核':'cadquery-ocp-novtk 7.9.3.1.1 / OCCT 7.9.3',
            '输入范围':'修复STEP候选，原生体积等价未通过；结果不得标为原生总成验证' if candidate_path else '原STEP与原生体积已交叉检查',
            '依据':sources,'紧固件来源':'按build_parts.py重建相同名义简化包络；另建AF5.32/厚2.15极小螺母。未读取原生紧固件，不含牙型/倒角/供应商公差证明。',
            '离散路径':[],'限位反例':[],'失败':[],
            '边界':['STEP独立几何校验不能代替SolidWorks装配配合、工程图或实体试验。',
                    '只检查离散路径和名义刚性形状；卡钩越障区必须弹性挠曲，保持力和应力未通过。',
                    '需要先拆下屏幕、承架及面框；完整电子、线缆与整机未纳入。']}
    def checkpoint():
        report['本进程内存']=win32process.GetProcessMemoryInfo(win32api.GetCurrentProcess())
        REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    try:
        for x in (-39,39):
            for y in (-28,28):
                route=[(0,0,z,'通过前侧开口') for z in (64,56,50,44,38,30)]
                route += [(x*f,y*f,30,'环肩后横移') for f in (.25,.5,.75,1)]
                route += [(x,y,z,'轴向插入') for z in (33,34,35,36,37,37.6)]
                for px,py,pz,phase in route:
                    hits=[]
                    for label,s,dz in [('杯',cup,0),('松放螺母',nominal_nut,5.6),('松放垫圈',washer,8)]:
                        hit=overlap(place(s,(px,py,pz+dz)),shell)
                        if hit:hits.append({'零件':label,**hit})
                    expected=phase=='轴向插入' and 34.1<pz<37.6
                    valid=True
                    for hit in hits:
                        valid &= expected and hit['零件']=='杯'
                        for b in hit['区域包围盒_mm']:
                            valid &= min(abs(b[0]-px),abs(b[3]-px))>5.3 and max(abs(b[1]-py),abs(b[4]-py))<1.5 and b[2]>41.9 and b[5]<46.2
                    row={'目标孔_mm':[x,y],'杯原点_mm':[px,py,pz],'阶段':phase,'交叠':hits,'仅预期卡钩挠曲区':bool(valid)}
                    report['离散路径'].append(row)
                    if not valid:report['失败'].append(row)
                for dz in (-.6,.1):
                    hit=overlap(place(cup,(x,y,37.6+dz)),shell)
                    row={'目标孔_mm':[x,y],'杯轴向越位_mm':dz,'限位交叠':hit}
                    report['限位反例'].append(row)
                    if not hit:report['失败'].append(row)
                for angle in (-8,8):
                    for label,s,z in [('名义螺母',nominal_nut,43.8),('螺母杯',cup,37.6)]:
                        hit=overlap(place(s,(x,y,z),angle),place(cup,(x,y,37.6)) if label=='名义螺母' else shell)
                        row={'目标孔_mm':[x,y],'旋转对象':label,'越位_deg':angle,'限位交叠':hit}
                        report['限位反例'].append(row)
                        if not hit:report['失败'].append(row)
                # Small real-size family nut is allowed greater angular play; 8 degrees is not a robust test.
                for angle in (8,12):
                    hit=overlap(place(small_nut,(x,y,44.05),angle),place(cup,(x,y,37.6)))
                    row={'目标孔_mm':[x,y],'最小包络螺母旋转_deg':angle,'交叠':hit,'预期有交叠':angle==12}
                    report['限位反例'].append(row)
                    if bool(hit)!=(angle==12):report['失败'].append(row)
                checkpoint();gc.collect();print('已完成孔位',x,y,'累计异常',len(report['失败']),flush=True)
        report['阶段']='完成离散名义几何检查';checkpoint()
        print(json.dumps({'路径数':len(report['离散路径']),'反例数':len(report['限位反例']),'异常':report['失败'],
                          '峰值工作集_MiB':report['本进程内存']['PeakWorkingSetSize']/1024**2},ensure_ascii=False,indent=2))
        assert not report['失败'],'Unexpected intersection or missing restraint; inspect report'
    except Exception as error:
        report['中止原因']=repr(error);checkpoint();raise


if __name__=='__main__':
    import sys;sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv)>1:
        assert len(sys.argv)==3 and sys.argv[1]=='--candidate-step'
        main(sys.argv[2])
    else:main()
