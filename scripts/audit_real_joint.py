from build_real_joint_assembly import *


def clashes(d):
    manager=cast(cast(d,'IAssemblyDoc').InterferenceDetectionManager,'IInterferenceDetectionMgr')
    manager.TreatCoincidenceAsInterference=False;manager.IncludeMultibodyPartInterferences=False;manager.IgnoreHiddenBodies=False;manager.UseTransform=True
    out=[]
    try:
        for obj in manager.GetInterferences() or []:
            obj=cast(obj,'IInterference');cs=[cast(c,'IComponent2') for c in obj.Components]
            codes={Path(c.GetPathName()).name.split('_')[0] for c in cs};volume=obj.Volume*1e9
            expected=(codes=={'S04','V01'} and 7<volume<8) or (codes=={'S04','V02'} and 7<volume<8.2) or (codes=={'S01','J06'} and 9<volume<11)
            out.append({'部件':[c.Name2 for c in cs],'编号':sorted(codes),'体积_mm3':volume,'分类':'预期螺纹简化交叠' if expected else '非预期实体干涉'})
        return out
    finally:manager.Done()


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.CommandInProgress=True
    path=ROOT/'assemblies/AK45-10大腿关节模块.SLDASM';d=cast(sw.OpenDoc6(str(path),2,1,'',0,0)[0],'IModelDoc2');assert d
    cm=cast(d.ConfigurationManager,'IConfigurationManager');base=cast(cm.ActiveConfiguration,'IConfiguration').Name;logs=[]
    try:
        for degree in (0,30,60,90,120,150):
            name=f'关节检查{degree}度'
            if name not in d.GetConfigurationNames():
                d.ShowConfiguration2(base);assert cm.AddConfiguration2(name,'配合求解与实体干涉检查','',0,'','',True)
            d.ShowConfiguration2(name);pose=next(f for f in all_mates(d) if f.Name=='关节姿态角_可调');dim=cast(d.Parameter('D1@'+pose.Name),'IDimension')
            assert dim.SetSystemValue3(math.radians(degree),1,None)==0;d.ForceRebuild3(False)
            cs=[cast(c,'IComponent2') for c in cast(d,'IAssemblyDoc').GetComponents(False)]
            rotor=next(c for c in cs if Path(c.GetPathName()).name.startswith('V02_'));link=next(c for c in cs if Path(c.GetPathName()).name.startswith('L01_'))
            a=list(rotor.Transform2.ArrayData);b=list(link.Transform2.ArrayData);signed_angle=math.degrees(math.atan2(a[1],a[0]))
            errors=[{'name':f.Name,'error':f.GetErrorCode2()} for f in all_mates(d) if f.GetErrorCode2()[0]!=0]
            contacts=clashes(d);log={'配置':name,'角度配合设定_deg':degree,'输出实际角_deg':signed_angle,'连杆与输出姿态差':max(abs(x-y) for x,y in zip(a[:9],b[:9])),'连杆末端轴心_mm':[-145*b[3]+b[9]*1000,-145*b[4]+b[10]*1000,-145*b[5]+b[11]*1000],'配合错误':errors,'干涉':contacts}
            logs.append(log);(ROOT/'validation/AK45-10关节转动干涉检查.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2),encoding='utf-8')
            print(name,'实际角',signed_angle,'配合错误',len(errors),'交叠',len(contacts),'非预期',sum(c['分类']=='非预期实体干涉' for c in contacts),flush=True)
            assert abs(abs(signed_angle)-degree)<.001 and not errors and log['连杆与输出姿态差']<.00001
            if degree in (0,60,120):preview(d,'AK45-10大腿关节_'+name)
        d.ShowConfiguration2('关节检查0度');save(d,path)
    finally:sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False
