from sw_core import *
import shutil,hashlib

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect()
    source=ROOT/'vendor/motor_sources/AK45-10_厂家三维/AK45-10.STEP'
    target=ROOT/'tmp/AK45_10.step';target.parent.mkdir(exist_ok=True);shutil.copyfile(source,target)
    keys=[C.swDefaultTemplatePart,C.swDefaultTemplateAssembly]
    before={k:sw.GetUserPreferenceStringValue(k) for k in keys}
    flags={k:sw.GetUserPreferenceToggle(k) for k in (C.swAlwaysUseDefaultTemplates,C.swMultiCAD_Enable3DInterconnect)}
    try:
        sw.SetUserPreferenceStringValue(keys[0],str(TEMPLATES/'gb_part.prtdot'))
        sw.SetUserPreferenceStringValue(keys[1],str(TEMPLATES/'gb_assembly.asmdot'))
        sw.SetUserPreferenceToggle(C.swAlwaysUseDefaultTemplates,True)
        sw.SetUserPreferenceToggle(C.swMultiCAD_Enable3DInterconnect,False)
        data=cast(sw.GetImportFileData(str(target)),'IImportStepData');data.MapConfigurationData=False
        print('IMPORT_BEGIN_WITH_TEMPLATES',flush=True)
        result=sw.LoadFile4(str(target),'r',data,0);print('IMPORT_RESULT',result,flush=True)
        d=cast(result[0],'IModelDoc2')
        if d:
            saved={};records=[];directory=ROOT/'vendor/motor_sources/AK45-10_原生组件';directory.mkdir(exist_ok=True)
            def save_children(parent):
                for raw in cast(parent,'IAssemblyDoc').GetComponents(True):
                    comp=cast(raw,'IComponent2');model=cast(comp.GetModelDoc2(),'IModelDoc2');assert model,comp.Name2
                    original_title=model.GetTitle()
                    if original_title in saved:continue
                    if model.GetType()==2:save_children(model)
                    number=len(records)+1;kind='组件' if model.GetType()==2 else '零件'
                    suffix='.SLDASM' if model.GetType()==2 else '.SLDPRT'
                    childpath=directory/f'AK45-10_厂家{kind}{number:03d}{suffix}'
                    model.AddCustomInfo3('','厂家来源构件名称',30,original_title)
                    child_result=cast(model.Extension,'IModelDocExtension').SaveAs(str(childpath),0,1,None,0,0)
                    assert child_result[0] and child_result[1]==0,(original_title,child_result)
                    records.append({'original_title':original_title,'file':str(childpath),'type':model.GetType()})
                    saved[original_title]=str(childpath);saved[model.GetTitle()]=str(childpath)
            if d.GetType()==2:save_children(d)
            suffix='.SLDASM' if d.GetType()==2 else '.SLDPRT'
            out=ROOT/'vendor/motor_sources'/('AK45-10_厂家原始三维'+suffix)
            save(d,out);preview(d,'AK45-10_厂家原始三维')
            print('IMPORTED_TYPE',d.GetType(),'FEATURES',[(f.Name,f.GetTypeName2()) for f in features(d)],flush=True)
            sw.CloseDoc(d.GetTitle())
            (ROOT/'vendor/motor_sources/AK45-10_原生组件清单.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
            check=sw.OpenDoc6(str(out),2 if suffix=='.SLDASM' else 1,1,'',0,0);print('REOPEN_CHECK',check[1:],flush=True)
            assert check[1]==0,('manufacturer reference has missing components',check[1:])
            sw.CloseDoc(cast(check[0],'IModelDoc2').GetTitle())
    finally:
        for k,v in before.items():sw.SetUserPreferenceStringValue(k,v)
        for k,v in flags.items():sw.SetUserPreferenceToggle(k,v)
