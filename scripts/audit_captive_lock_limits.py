from build_body_fit_assembly import *
from sw_assembly import cylinder_at

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    path=ROOT/'assemblies/储物舱防脱锁止_装入检查.SLDASM';d=cast(sw.OpenDoc6(str(path),2,1,'',0,0)[0],'IModelDoc2');checks=[]
    try:
        for name,lift,shift in [('验证_锁定时强制退出1mm',0,-1),('验证_越过防脱肩0_2mm',9.2,0)]:
            d.ShowConfiguration2('销升0_舱退0');cm=cast(d.ConfigurationManager,'IConfigurationManager')
            if name not in d.GetConfigurationNames():cm.AddConfiguration2(name,'故意越限，用于验证阻挡几何','',0,'','',True)
            d.ShowConfiguration2(name)
            for part,axis,value in [('防脱螺旋销','Z',lift),('储物舱壳体_装入位置','X',shift)]:
                label=part+'_'+axis;f=next(f for f in all_mates(d) if f.Name==label);assert f.SetSuppression2(1,1,None)
                assert cast(d.Parameter('D1@'+label),'IDimension').SetSystemValue3(abs(value)/1000,1,None)==0
            d.ForceRebuild3(False);clashes=interferences(d)
            current={Path(cast(c,'IComponent2').GetPathName()).name.split('_')[0]:cast(c,'IComponent2') for c in cast(d,'IAssemblyDoc').GetComponents(False)}
            assert abs(current['Q08'].Transform2.ArrayData[11]*1000-lift)<1e-4
            assert abs(current['C01'].Transform2.ArrayData[9]*1000-shift)<1e-4
            found=[x for x in clashes if 'Q08_' in ' '.join(x['components']) and ('C01_' if shift else 'Q07_') in ' '.join(x['components'])]
            assert found and (shift or found[0]['volume_mm3']>math.pi*(9-6.25)*8+1),clashes
            for x in found:x['classification']='故意越限配置中的预期机械阻挡'
            checks.append({'工况':name,'有意越限相交':found,'结论':'检测到预期的机械阻挡实体；不是承载强度验证'})
        d.ShowConfiguration2('销升0_舱退0');d.ForceRebuild3(False);save(d,path)
        current={Path(cast(c,'IComponent2').GetPathName()).name.split('_')[0]:cast(c,'IComponent2') for c in cast(d,'IAssemblyDoc').GetComponents(False)}
        axes=[]
        for code in ('Q06','Q07'):
            for x in (75,91):
                for y in (-21,21):
                    cylinder_at(current[code],1.7,(x,y,0),2);axes.append({'零件':code,'实际孔轴XY_mm':[x,y],'直径_mm':3.4})
        cylinder_at(current['C01'],2.1,(83,0,0),2);cylinder_at(current['Q08'],2,(0,0,0),2)
        mate_errors=[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]];assert not mate_errors
        (ROOT/'validation/防脱锁止总成最终复核.json').write_text(json.dumps({'实际组件数':len(cast(d,'IAssemblyDoc').GetComponents(False)),'真实配合数':len(list(all_mates(d))),'配合错误':mate_errors,'桥脚与底座孔轴':axes,'舱耳与销尖圆柱面':'已核对，装入时世界XY同为83,0','保存配置':'销升0_舱退0'},ensure_ascii=False,indent=2),encoding='utf-8')
        (ROOT/'validation/防脱销阻挡几何验证.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(checks,ensure_ascii=False))
    finally:sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False
