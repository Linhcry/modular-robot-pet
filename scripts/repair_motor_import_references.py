from sw_core import *

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();assert sw.GetDocumentCount()==0,'Close CAD documents before reference repair.'
    records=json.loads((ROOT/'vendor/motor_sources/AK45-10_原生组件清单.json').read_text(encoding='utf-8'))
    by_name={Path(r['original_title']).stem if Path(r['original_title']).suffix.upper() in ('.SLDPRT','.SLDASM') else r['original_title']:r['file'] for r in records}
    # This source leaf was saved separately during the direct-SaveAs diagnostic.
    by_name['________']=str(ROOT/'vendor/motor_sources/AK45-10_原生组件/AK45-10_厂家零件001.SLDPRT')
    root=ROOT/'vendor/motor_sources/AK45-10_厂家原始三维.SLDASM'
    parents=[r['file'] for r in records if r['type']==2]+[str(root)]
    logs=[]
    for parent in parents:
        deps=sw.GetDocumentDependencies2(parent,False,False,False) or []
        for name,old in zip(deps[::2],deps[1::2]):
            if Path(old).exists():continue
            assert name in by_name,(parent,name)
            new=by_name[name];assert Path(new).exists()
            okay=sw.ReplaceReferencedDocument(parent,old,new)
            if not okay:okay=sw.ReplaceReferencedDocument(parent,old.replace('\\\\','\\'),new)
            print('引用重定向',Path(parent).name,name,okay,flush=True)
            assert okay,(parent,old,new)
            logs.append({'assembly':parent,'old_reference':old,'new_reference':new})
    result=sw.OpenDoc6(str(root),2,1,'',0,0);print('REOPEN_CHECK',result[1:],flush=True);assert result[1]==0
    d=cast(result[0],'IModelDoc2');a=cast(d,'IAssemblyDoc');a.ResolveAllLightWeightComponents(True)
    cs=[cast(c,'IComponent2') for c in a.GetComponents(False)]
    missing=[c.Name2 for c in cs if c.GetModelDoc2() is None];print('ALL_COMPONENTS',len(cs),'MISSING',missing,flush=True);assert not missing
    preview(d,'AK45-10_厂家原始三维');sw.CloseDoc(d.GetTitle())
    (ROOT/'validation/厂家原生引用修复记录.json').write_text(json.dumps({'replacements':logs,'component_instances':len(cs),'missing':missing},ensure_ascii=False,indent=2),encoding='utf-8')
