"""后台检查壳体与框架安装空间。基准面配合不代替最终紧固连接。"""
from sw_assembly import *
from build_cargo_assembly import all_mates
from audit_cargo_motion import interferences,z_up_preview

def datum_mate(d,base,c,index,offset,label):
    d.ClearSelection2(True)
    for i,component in enumerate((base,c)):
        doc=cast(component.GetModelDoc2(),'IModelDoc2')
        local=[f for f in features(doc) if f.GetTypeName2()=='RefPlane'][index]
        f=cast(component.FeatureByName(local.Name),'IFeature')
        assert f and f.Select2(i>0,1)
    result=cast(d,'IAssemblyDoc').AddMate5(5 if offset else 0,2,False,abs(offset)/1000,0,0,0,0,0,0,0,False,False,0,0)
    d.ClearSelection2(True)
    assert result[0] and result[1]==C.swAddMateError_NoError,(label,result)
    name_last_mate(d,label)

def run():
    sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    rows={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))}
    d=newdoc(sw,'asm');records=[]
    try:
        plan=[('B01_LowerBody','圆润机身下护壳',(0,0,0),IDENTITY),
              ('B02_UpperBody','拱形机身背盖',(0,0,65.6),IDENTITY),
              ('F10_LightBelly','镂空下承载板',(0,0,15.3),IDENTITY),
              ('F12_ShortSideRail','左侧承载槽梁',(0,87,17.8),IDENTITY),
              ('F12_ShortSideRail','右侧承载槽梁',(0,-87,17.8),(-1,0,0,0,-1,0,0,0,1)),
              ('F11_LightDeck','双承载带上板',(0,0,71.8),IDENTITY)]
        base=None
        for code,name,xyz,rot in plan:
            c=add(sw,d,rows[code]['path'],name,xyz,rot)
            if base is None:base=c
            else:
                for index,axis in ((0,2),(1,1),(2,0)):
                    label=name+'_基准定位_'+('XYZ'[axis])
                    datum_mate(d,base,c,index,xyz[axis],label)
                    d.ForceRebuild3(False)
                    actual=list(c.Transform2.ArrayData)
                    if xyz[axis] and abs(actual[9+axis]*1000-xyz[axis])>1e-4:
                        f=next(f for f in all_mates(d) if f.Name==label)
                        definition=cast(f.GetDefinition(),'IDistanceMateFeatureData')
                        definition.FlipDimension=not definition.FlipDimension
                        assert f.ModifyDefinition(definition,d,None);d.ForceRebuild3(False)
            records.append({'编号':code,'名称':name,'component':c,'目标原点_mm':xyz,'目标方向':rot})
        d.ForceRebuild3(False)
        for row in records:
            c=row.pop('component');a=list(c.Transform2.ArrayData)
            row['实际原点_mm']=[v*1000 for v in a[9:12]]
            row['原点误差_mm']=max(abs(x-y) for x,y in zip(row['实际原点_mm'],row['目标原点_mm']))
            row['方向误差']=max(abs(x-y) for x,y in zip(a[:9],row['目标方向']))
            assert row['原点误差_mm']<1e-4 and row['方向误差']<1e-6,row
        mates=[{'名称':f.Name,'类型':f.GetTypeName2(),'错误':f.GetErrorCode2()} for f in all_mates(d)]
        clashes=interferences(d)
        data={'阶段':'空间装配候选；真实基准面配合；紧固件、横梁、载荷和关节运动未完成','零件实例':records,'配合':mates,'干涉':clashes}
        (ROOT/'validation/机身壳体与框架空间检查.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        save(d,ROOT/'assemblies/机身壳体与框架_空间候选.SLDASM')
        try:
            z_up_preview(sw,d,'机身壳体与框架_空间候选')
            data['预览导出API返回成功']=True
        except Exception as e:data['预览导出错误']=str(e)
        (ROOT/'validation/机身壳体与框架空间检查.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'实例数':len(records),'配合数':len(mates),'配合错误':[r for r in mates if r['错误'][0]],'干涉':clashes},ensure_ascii=False,indent=2),flush=True)
    finally:
        sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');run()
