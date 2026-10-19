from sw_core import *

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();d=cast(sw.ActiveDoc,'IModelDoc2')
    assert d and d.GetType()==2 and d.GetTitle().startswith('AK45_10'), 'Only resume the in-memory manufacturer import.'
    saved={};records=[];directory=ROOT/'vendor/motor_sources/AK45-10_原生组件';directory.mkdir(exist_ok=True)
    def visit(parent):
        for raw in cast(parent,'IAssemblyDoc').GetComponents(True):
            comp=cast(raw,'IComponent2');model=cast(comp.GetModelDoc2(),'IModelDoc2');assert model,comp.Name2
            original=model.GetTitle()
            if original in saved:continue
            kind=model.GetType()
            if kind==2:visit(model)
            number=100+len(records);label='组件' if kind==2 else '零件';suffix='.SLDASM' if kind==2 else '.SLDPRT'
            out=directory/f'AK45-10_厂家{label}{number:03d}{suffix}'
            result=cast(model.Extension,'IModelDocExtension').SaveAs(str(out),0,1,None,0,0)
            assert result[0] and result[1]==0,(original,result)
            print('厂家引用已保存',out.name,flush=True)
            records.append({'original_title':original,'file':str(out),'type':kind})
            saved[original]=str(out);saved[model.GetTitle()]=str(out)
            sw.CloseDoc(model.GetTitle())
    visit(d)
    out=ROOT/'vendor/motor_sources/AK45-10_厂家原始三维.SLDASM'
    result=cast(d.Extension,'IModelDocExtension').SaveAs(str(out),0,5,None,0,0);print('ROOT_SAVE',result,flush=True);assert result[0] and result[1]==0
    sw.CloseDoc(d.GetTitle())
    (ROOT/'vendor/motor_sources/AK45-10_原生组件清单.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    result=sw.OpenDoc6(str(out),2,1,'',0,0);print('REOPEN_CHECK',result[1:],flush=True);assert result[1]==0
    d=cast(result[0],'IModelDoc2');cs=[cast(c,'IComponent2') for c in cast(d,'IAssemblyDoc').GetComponents(False)]
    missing=[c.Name2 for c in cs if c.GetModelDoc2() is None];print('COMPONENTS',len(cs),'MISSING',missing,flush=True);assert not missing
    sw.CloseDoc(d.GetTitle())
