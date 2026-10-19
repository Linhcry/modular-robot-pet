from build_integrated_cargo_deck import *

def world(comp,point):
    a=list(comp.Transform2.ArrayData)
    return [a[9+j]*1000+sum(point[i]*a[3*i+j] for i in range(3)) for j in range(3)]

def check_axis(comp,radius,point,axis,xy):
    cylinder_at(comp,radius,point,axis)
    w=world(comp,point);a=list(comp.Transform2.ArrayData)
    assert abs(abs(a[3*axis+2])-1)<1e-6
    assert max(abs(w[j]-xy[j]) for j in (0,1))<1e-4
    return {'零件':Path(comp.GetPathName()).name,'局部孔轴点_mm':point,'世界孔轴XY_mm':w[:2],'直径_mm':radius*2}

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    path=ROOT/'assemblies/储物舱_导轨锁止与承载板.SLDASM';d=cast(sw.OpenDoc6(str(path),2,1,'',0,0)[0],'IModelDoc2');assert d
    try:
        d.ShowConfiguration2('装入锁定');d.ForceRebuild3(False)
        cs=[cast(c,'IComponent2') for c in cast(d,'IAssemblyDoc').GetComponents(True)]
        def group(prefix):return [c for c in cs if Path(c.GetPathName()).name.startswith(prefix)]
        def at(prefix,xy):return next(c for c in group(prefix) if max(abs(world(c,(0,0,0))[j]-xy[j]) for j in (0,1))<1e-4)
        checks=[]
        for x,y in LOCK_HOLES:
            for p in ('F13_','Q06_','Q07_'):checks.append(check_axis(group(p)[0],1.7,(x,y,0),2,(x,y)))
            checks.append(check_axis(at('S01_', (x,y)),1.5,(0,0,0),2,(x,y)))
        for y in (-45,45):
            rail=at('Q01_',(-65,y))
            for x in (-50,0,50):
                checks.append(check_axis(group('F13_')[0],1.7,(x,y,0),2,(x,y)))
                checks.append(check_axis(at('Q09_',(x,y)),1.7,(0,0,0),2,(x,y)))
                checks.append(check_axis(rail,1.7,(0,0,x+65),1,(x,y)))
                checks.append(check_axis(at('S01_',(x,y)),1.5,(0,0,0),2,(x,y)))
        errors=[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]];assert not errors
        catalog={r['id']:r for r in json.loads(CAT_PATH.read_text(encoding='utf-8'))}
        masses={}
        for prefix in ('F13_','Q09_'):
            c=group(prefix)[0];volume=sum(b.GetMassProperties(1)[3] for b in body_list(cast(c.GetModelDoc2(),'IModelDoc2')))
            masses[prefix]={'体积_mm3':volume*1e9,'质量_g_按2700kg_m3':volume*2700*1000,'装入数量':len(group(prefix))}
        result={'当前配置':'装入锁定','实际安装孔与螺钉轴核对':checks,'顶层实例数':len(cs),'总实例含子件':len(cast(d,'IAssemblyDoc').GetComponents(False)),'顶层配合数':len(list(all_mates(d))),'配合错误':errors,'新件质量':masses,
                '名义紧固链_mm':{'导轨':{'螺钉':'M3x16','头下Z':10,'螺母下表面Z':-2.9,'伸出':3.1,'沉孔D':6.2,'头D':5.5,'上垫圈':'无；标准OD7垫圈不能装入D6.2沉孔'},'锁座':{'螺钉':'M3x16','头下Z':8.5,'螺母下表面Z':-2.9,'伸出':4.6}},
                '局限':['孔轴审核不等于接触承载或预紧力验证','尚未套入外壳，不代表整机可以正常取出储物舱','导轨垫块间跨度50mm，承载与刚度仍须核对','标准件仍为尺寸简化件；大工程师来源与可采购型号未冻结']}
        (ROOT/'validation/储物舱承载对接孔轴复核.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False),flush=True)
    finally:sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
