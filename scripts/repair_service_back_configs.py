"""Use separate signed datum mates: FlipDimension is shared across configurations here."""
from build_integrated_cargo_deck import *
from build_body_fit_assembly import datum_mate

def repair(sw,d):
    rows=json.loads((ROOT/'validation/分体背盖与储物舱维护检查.json').read_text(encoding='utf-8'))
    def fresh():return [cast(c,'IComponent2') for c in cast(d,'IAssemblyDoc').GetComponents(True)]
    def find(prefix):return next(c for c in fresh() if Path(c.GetPathName()).name.startswith(prefix))
    def feat(label):return next(f for f in all_mates(d) if f.Name==label)
    minus='可拆曲面后背盖_Z';plus='可拆曲面后背盖_Z_上方维护位置'
    d.ShowConfiguration2('常用_装入锁定')
    if any(f.Name==plus for f in all_mates(d)):feat(plus).SetSuppression2(0,1,None)
    f=feat(minus);assert f.SetSuppression2(1,1,None);cast(d.Parameter('D1@'+minus),'IDimension').SetSystemValue3(.0062,1,None);d.ForceRebuild3(False)
    if find('B05_').Transform2.ArrayData[11]>0:
        definition=cast(f.GetDefinition(),'IDistanceMateFeatureData');definition.FlipDimension=not definition.FlipDimension;assert f.ModifyDefinition(definition,d,None);d.ForceRebuild3(False)
    assert abs(find('B05_').Transform2.ArrayData[11]+.0062)<1e-7
    if not any(f.Name==plus for f in all_mates(d)):
        assert feat(minus).SetSuppression2(0,1,None)
        c=find('B05_');c.Transform2=transform(sw,(0,0,8.8))
        datum_mate(d,find('储物舱_导轨锁止'),c,0,8.8,plus);d.ForceRebuild3(False)
        if find('B05_').Transform2.ArrayData[11]<0:
            f=feat(plus);definition=cast(f.GetDefinition(),'IDistanceMateFeatureData');definition.FlipDimension=not definition.FlipDimension;assert f.ModifyDefinition(definition,d,None);d.ForceRebuild3(False)
        assert abs(find('B05_').Transform2.ArrayData[11]-.0088)<1e-7
    for row in rows:
        d.ShowConfiguration2(row['配置']);target=row['后盖抬高_mm']-6.2
        active,inactive=(minus,plus) if target<0 else (plus,minus)
        assert feat(inactive).SetSuppression2(0,1,None);assert feat(active).SetSuppression2(1,1,None)
        assert cast(d.Parameter('D1@'+active),'IDimension').SetSystemValue3(abs(target)/1000,1,None)==0
        for c in fresh():
            if Path(c.GetPathName()).name.startswith(('Q10_','S01_','S02_','S03_')):c.SetSuppression2(0 if row['压板及其紧固件已拆'] else 2)
        find('储物舱_导轨锁止').ReferencedConfiguration=row['储物子装配配置'];d.ForceRebuild3(False)
    # A fresh pass after all edits proves configuration persistence, not just immediate transforms.
    for row in rows:
        d.ShowConfiguration2(row['配置']);d.ForceRebuild3(False)
        target=row['后盖抬高_mm']-6.2;actual=find('B05_').Transform2.ArrayData[11]*1000;assert abs(actual-target)<1e-4,(row['配置'],actual,target)
        for c in fresh():
            if Path(c.GetPathName()).name.startswith(('Q10_','S01_','S02_','S03_')):assert bool(c.IsSuppressed())==row['压板及其紧固件已拆'],(row['配置'],c.Name2,c.IsSuppressed())
        clashes=interferences(d)
        for cl in clashes:
            ns=' '.join(cl['components'])
            if 'Q07_' in ns and 'Q08_' in ns and abs(cl['volume_mm3']-math.pi*(9-6.25)*8)<.05:cl['classification']='M6公称杆与底孔的预期简化交叠'
        row.update({'后盖实际Z_mm':actual,'干涉':clashes,'跨配置重新切换验证':True,'配合错误':[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]]})
        assert not row['配合错误'] and not any(c['classification']=='需修复的实体干涉' for c in clashes),row
        print('CONFIG_PERSISTENCE',row['配置'],actual,flush=True)
    (ROOT/'validation/分体背盖与储物舱维护检查.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    d.ShowConfiguration2('常用_装入锁定');d.ForceRebuild3(False)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    p=ROOT/'assemblies/分体曲面背盖与储物舱_维护候选.SLDASM';d=cast(sw.OpenDoc6(str(p),2,1,'',0,0)[0],'IModelDoc2');assert d
    try:repair(sw,d);save(d,p);z_up_preview(sw,d,'分体曲面背盖与储物舱_维护候选')
    finally:sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
