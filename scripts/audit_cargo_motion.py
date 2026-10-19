from build_cargo_assembly import *

def interferences(d):
    manager=cast(cast(d,'IAssemblyDoc').InterferenceDetectionManager,'IInterferenceDetectionMgr')
    manager.TreatCoincidenceAsInterference=False
    manager.IncludeMultibodyPartInterferences=False
    manager.IgnoreHiddenBodies=False
    manager.MakeInterferingPartsTransparent=False
    manager.UseTransform=True
    result=[]
    try:
        for obj in manager.GetInterferences() or []:
            obj=cast(obj,'IInterference');cs=[cast(c,'IComponent2') for c in obj.Components];names=[c.Name2 for c in cs]
            codes={Path(c.GetPathName()).name.split('_')[0] for c in cs}
            vol=obj.Volume*1e9
            threaded=('S01' in codes and bool(codes & {'Q02','Q05','C02'}) and vol<16)
            result.append({'components':names,'volume_mm3':vol,'classification':'螺纹公称杆与攻丝底孔的预期简化交叠' if threaded else '需修复的实体干涉'})
        return result
    finally:manager.Done()

def z_up_preview(sw,d,name):
    d.ShowNamedView2('*等轴测',7)
    view=cast(d.ActiveView,'IModelView')
    a=math.sqrt(.5);b=1/math.sqrt(6);c=1/math.sqrt(3)
    view.Orientation3=transform(sw,rot=(a,-b,c,a,b,-c,0,2*b,c))
    d.ViewZoomtofit2();d.GraphicsRedraw2()
    out=ROOT/'previews'/f'{name}.bmp';assert d.SaveBMP(str(out),1400,1000)

def run(short=False):
    sw=connect();sw.CommandInProgress=True
    stem='储物舱模块_四短滑靴候选' if short else '储物舱模块'
    path=ROOT/'assemblies'/f'{stem}.SLDASM';d=cast(sw.OpenDoc6(str(path),2,1,'',0,0)[0],'IModelDoc2')
    assert d
    pose=next(f for f in all_mates(d) if f.Name=='舱盖姿态角_可调')
    dim=cast(d.Parameter('D1@'+pose.Name),'IDimension');assert dim
    ass=cast(d,'IAssemblyDoc');lid=next(cast(c,'IComponent2') for c in ass.GetComponents(False) if Path(cast(c,'IComponent2').GetPathName()).name.startswith('C02_'))
    cm=cast(d.ConfigurationManager,'IConfigurationManager');base=cast(cm.ActiveConfiguration,'IConfiguration').Name
    print('DIM_START',dim.SystemValue,'CONFIG',base,flush=True)
    logs=[]
    try:
        for deg in (0,15,30,45,60,75,90):
            name='舱盖闭合' if deg==0 else f'舱盖开启{deg}度'
            if name not in d.GetConfigurationNames():
                d.ShowConfiguration2(base)
                assert cm.AddConfiguration2(name,'实体干涉检查姿态','',0,'','',True)
            d.ShowConfiguration2(name)
            assert cast(cm.ActiveConfiguration,'IConfiguration').Name==name
            pose=next(f for f in all_mates(d) if f.Name=='舱盖姿态角_可调')
            dim=cast(d.Parameter('D1@'+pose.Name),'IDimension')
            a=-math.radians(deg);co=math.cos(a);si=math.sin(a)
            xyz=(0,65-65*co-6*si,45-65*si+6*co)
            assert pose.SetSuppression2(1,1,None)
            assert dim.SetSystemValue3(math.radians(deg),1,None)==0
            d.ForceRebuild3(False)
            lid=next(cast(c,'IComponent2') for c in ass.GetComponents(False) if Path(cast(c,'IComponent2').GetPathName()).name.startswith('C02_'))
            actual=[v*1000 for v in lid.Transform2.ArrayData[9:12]]
            err=max(abs(v-w) for v,w in zip(actual,xyz))
            clashes=interferences(d)
            log={'angle_deg':deg,'configuration':name,'target_origin_mm':xyz,'actual_origin_mm':actual,'origin_error_mm':err,'interferences':clashes,'mate_errors':[{'name':f.Name,'error':f.GetErrorCode2()} for f in all_mates(d) if f.GetErrorCode2()[0]!=0]}
            logs.append(log)
            print('POSE',deg,'error_mm',err,'clashes',len(clashes),'unexpected',sum(c['classification']=='需修复的实体干涉' for c in clashes),flush=True)
            audit_name='短滑靴储物舱开启干涉检查.json' if short else '储物舱开启干涉检查.json'
            (ROOT/'validation'/audit_name).write_text(json.dumps(logs,ensure_ascii=False,indent=2),encoding='utf-8')
            assert err<1e-4,(deg,'angle mate did not solve to the expected hinge motion',err)
            if deg in (0,45,90):z_up_preview(sw,d,f'{stem}_开启{deg}度')
        d.ShowConfiguration2('舱盖闭合');save(d,path)
    finally:
        sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if '--background' in sys.argv:connect().FrameState=C.swWindowMinimized
    run(short='--short' in sys.argv)
