from build_real_joint_assembly import *
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.CommandInProgress=True
    path=ROOT/'assemblies/AK45-10大腿关节模块.SLDASM';d=cast(sw.GetOpenDocumentByName(str(path)),'IModelDoc2')
    if not d:d=cast(sw.OpenDoc6(str(path),2,1,'',0,0)[0],'IModelDoc2')
    try:
        f=next(f for f in all_mates(d) if f.Name=='电机输出端面位置43');definition=cast(f.GetDefinition(),'IDistanceMateFeatureData')
        cs=[cast(c,'IComponent2') for c in cast(d,'IAssemblyDoc').GetComponents(False)]
        rotor=next(c for c in cs if Path(c.GetPathName()).name.startswith('V02_'))
        if abs(rotor.Transform2.ArrayData[11])>.000001:
            print('修正距离配合方向',definition.FlipDimension,flush=True);definition.FlipDimension=not definition.FlipDimension
            assert f.ModifyDefinition(definition,d,None);d.ForceRebuild3(False)
        data=json.loads((ROOT/'validation/AK45-10关节装配审计.json').read_text(encoding='utf-8'));rows={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))}
        for row in data['components']:
            matching=[c for c in cs if Path(c.GetPathName())==Path(rows[row['code']]['path'])]
            c=min(matching,key=lambda c:sum((v*1000-w)**2 for v,w in zip(c.Transform2.ArrayData[9:12],row['expected_xyz_mm'])))
            row['actual_xyz_mm']=[v*1000 for v in c.Transform2.ArrayData[9:12]];row['max_origin_error_mm']=max(abs(v-w) for v,w in zip(row['actual_xyz_mm'],row['expected_xyz_mm']));row['fixed']=bool(c.IsFixed())
        data['mates']=[{'name':f.Name,'type':f.GetTypeName2(),'error':f.GetErrorCode2()} for f in all_mates(d)]
        (ROOT/'validation/AK45-10关节装配审计.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        assert max(r['max_origin_error_mm'] for r in data['components'])<.001,[(r['name'],r['max_origin_error_mm']) for r in data['components'] if r['max_origin_error_mm']>.001]
        assert not [m for m in data['mates'] if m['error'][0]!=0]
        save(d,path);preview(d,'AK45-10大腿关节模块');print('轴向定位复核通过',len(data['components']),len(data['mates']),flush=True)
    finally:sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False
