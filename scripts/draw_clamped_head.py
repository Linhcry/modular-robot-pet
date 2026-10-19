from sw_drawings import *

def activate_configuration(d,name):
    cm=cast(d.ConfigurationManager,'IConfigurationManager')
    if cast(cm.ActiveConfiguration,'IConfiguration').Name!=name:
        d.ShowConfiguration2(name)
    assert cast(cm.ActiveConfiguration,'IConfiguration').Name==name

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True;d=None
    path=ROOT/'assemblies/触控视觉头部_承架紧固候选.SLDASM'
    try:
        d=cast(sw.OpenDoc6(str(path),2,1,'',0,0)[0],'IModelDoc2');cm=cast(d.ConfigurationManager,'IConfigurationManager');baseline=cast(cm.ActiveConfiguration,'IConfiguration').Name;cfg='面框拆下_承架紧固'
        if cfg not in d.GetConfigurationNames():assert cm.AddConfiguration2(cfg,'装配工具进入时的状态','',0,'','',True)
        activate_configuration(d,cfg)
        for obj in cast(d,'IAssemblyDoc').GetComponents(True):
            c=cast(obj,'IComponent2')
            if Path(c.GetPathName()).stem.split('_')[0] in ('H05','H07'):c.SetSuppression2(0)
        d.ForceRebuild3(False)
        assert sum(cast(o,'IComponent2').IsSuppressed() for o in cast(d,'IAssemblyDoc').GetComponents(True))==2
        activate_configuration(d,baseline)
        assert not any(cast(o,'IComponent2').IsSuppressed() for o in cast(d,'IAssemblyDoc').GetComponents(True))
        save(d,path);sw.CloseDoc(d.GetTitle());d=None
        row={'id':'ASM_HeadClamped','name':'触控视觉头部承架紧固候选','path':str(path),'bbox_mm':[-55,-51,0,55,51,62.2],'drawing_scale':.85,'drawing_iso_scale':.85,'front_configuration':cfg,'material_assumption':'PA12与6061-T6、黑色硅胶、钢制连接件及厂家屏幕','key_dimensions_mm':'承架孔距78×56；4组M3×10，螺母外露2.1；玻璃、面框和柔性圈齐平','notes':'21组件44配合；四处D5工具杆通道已检查。螺母防掉落与扳手路径、屏幕/面框紧固、相机及控制板仍待完善。'}
        r=make(sw,row,True);p=ROOT/'validation/触控头部工程图检查.json';old=json.loads(p.read_text(encoding='utf-8'));p.write_text(json.dumps([x for x in old if x['id']!=r['id']]+[r],ensure_ascii=False,indent=2),encoding='utf-8')
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
