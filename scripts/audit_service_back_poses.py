from build_integrated_cargo_deck import *
from audit_integrated_cargo_deck import check_axis

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    p=ROOT/'assemblies/分体曲面背盖与储物舱_维护候选.SLDASM';d=cast(sw.OpenDoc6(str(p),2,1,'',0,0)[0],'IModelDoc2');assert d
    try:
        rows=json.loads((ROOT/'validation/分体背盖与储物舱维护检查.json').read_text(encoding='utf-8'));actuals=[]
        for row in rows:
            d.ShowConfiguration2(row['配置']);d.ForceRebuild3(False)
            cs=[cast(c,'IComponent2') for c in cast(d,'IAssemblyDoc').GetComponents(False)]
            def find(prefix):return next(c for c in cs if Path(c.GetPathName()).name.startswith(prefix))
            body=[v*1000 for v in find('C01_').Transform2.ArrayData[9:12]]
            lid=[v*1000 for v in find('C02_').Transform2.ArrayData[9:12]]
            shift=next((v for v in (25,80,160) if row['配置'].endswith('退出'+str(v))),0)
            back=find('B05_').Transform2.ArrayData[11]*1000;assert abs(back-(row['后盖抬高_mm']-6.2))<1e-4,(row['配置'],'rear shell',back)
            opening='90' in row['配置'];target_body=[-shift,0,18.2];target_lid=[-shift,71 if opening else 0,128.2 if opening else 69.2]
            assert max(abs(v-w) for v,w in zip(body,target_body))<1e-4,(row['配置'],body,target_body)
            assert max(abs(v-w) for v,w in zip(lid,target_lid))<1e-4,(row['配置'],lid,target_lid)
            actuals.append({'配置':row['配置'],'真实舱体原点_mm':body,'真实舱盖原点_mm':lid,'真实后盖Z_mm':back,'与目标一致':True})
        d.ShowConfiguration2('常用_装入锁定');d.ForceRebuild3(False)
        top=[cast(c,'IComponent2') for c in cast(d,'IAssemblyDoc').GetComponents(True)];axes=[]
        def group(prefix):return [c for c in top if Path(c.GetPathName()).name.startswith(prefix)]
        for prefix,x in [('B04_',-64),('B05_',-90)]:
            c=group(prefix)[0]
            for y in (-78,78):axes.append(check_axis(c,1.7,(x,y,32),2,(x,y)))
        for c in group('Q10_'):
            y=c.Transform2.ArrayData[10]*1000
            for x in (-90,-64):axes.append(check_axis(c,1.7,(x+77,0,0),2,(x,y)))
        for c in group('S01_'):
            xy=[v*1000 for v in c.Transform2.ArrayData[9:11]];axes.append(check_axis(c,1.5,(0,0,0),2,xy))
        errors=[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]];assert not errors
        output={'姿态真实变换':actuals,'压板安装孔与螺钉轴':axes,'顶层实例':len(top),'总实例含子件':len(cast(d,'IAssemblyDoc').GetComponents(False)),'顶层配合数':len(list(all_mates(d))),'配合错误':errors,'局限':'分体背盖和舱体空间验证；未包括侧梁、全身关节、电子走线及批头包络。'}
        (ROOT/'validation/分体背盖最终几何复核.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(output,ensure_ascii=False),flush=True)
    finally:sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
