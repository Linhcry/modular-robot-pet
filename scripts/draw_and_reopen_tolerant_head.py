"""Create service configuration/drawing, then verify saved native assembly."""
from draw_clamped_head import activate_configuration
from sw_drawings import *
from build_touch_head import all_mates, interferences
import hashlib


def main():
    sw=connect();assert sw.GetDocumentCount()==0
    sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True;d=None
    path=ROOT/'assemblies/触控视觉头部_长臂螺母防落候选.SLDASM'
    cfg='面框拆下_长臂螺母杯'
    try:
        d=cast(sw.OpenDoc6(str(path),2,1,'',0,0)[0],'IModelDoc2')
        cm=cast(d.ConfigurationManager,'IConfigurationManager');baseline=cast(cm.ActiveConfiguration,'IConfiguration').Name
        if cfg not in d.GetConfigurationNames():assert cm.AddConfiguration2(cfg,'面框与柔性圈拆下，查看承架紧固','',0,'','',True)
        activate_configuration(d,cfg)
        for obj in cast(d,'IAssemblyDoc').GetComponents(True):
            c=cast(obj,'IComponent2')
            if Path(c.GetPathName()).stem.split('_')[0] in ('H05','H07'):c.SetSuppression2(0)
        d.ForceRebuild3(False);activate_configuration(d,baseline)
        assert not any(cast(o,'IComponent2').IsSuppressed() for o in cast(d,'IAssemblyDoc').GetComponents(True))
        save(d,path);sw.CloseDoc(d.GetTitle());d=None
        row={'id':'ASM_HeadLongArm','name':'触控视觉头部长臂螺母防落候选','path':str(path),
             'bbox_mm':[-55,-51,0,55,51,62.2],'drawing_scale':.85,'drawing_iso_scale':.85,'front_configuration':cfg,
             'material_assumption':'PA12、6061-T6、硅胶、钢制连接件及厂家屏幕',
             'key_dimensions_mm':'承架孔距78×56；4组M3×10；杯原点Z37.6；杯底卸载间隙0.6',
             'notes':'25组件52配合。卡扣保持力、疲劳和制造公差待验证；屏幕及面框完整紧固、相机和控制板待完善。'}
        drawing=make(sw,row,True)
        d=cast(sw.OpenDoc6(str(path),2,1,'',0,0)[0],'IModelDoc2');configs=[]
        for name in (baseline,cfg,baseline):
            activate_configuration(d,name);d.ForceRebuild3(False)
            cs=[cast(o,'IComponent2') for o in cast(d,'IAssemblyDoc').GetComponents(True)]
            suppressed=[Path(c.GetPathName()).stem for c in cs if c.IsSuppressed()]
            errors=[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]]
            assert len(cs)==25 and len(list(all_mates(d)))==52 and not errors
            assert {s.split('_')[0] for s in suppressed}==({'H05','H07'} if name==cfg else set())
            # Geometry has not changed since the initial full-assembly check; verify saved baseline once.
            clashes=interferences(d) if not configs else None
            if clashes is not None:assert not clashes
            configs.append({'配置':name,'组件数':len(cs),'配合数':52,'抑制零件':suppressed,'配合错误':errors,'本次重开干涉':clashes})
        report={'原生装配':str(path),'原生装配SHA256':hashlib.sha256(path.read_bytes()).hexdigest(),
                '重开配置检查':configs,'原生工程图':drawing,'视觉检查':'待渲染查看，不等同于制造放行'}
        (ROOT/'validation/长臂头部装配图与重开检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'配置检查次数':len(configs),'组件数':25,'配合数':52,'工程图':drawing['drawing']},ensure_ascii=False),flush=True)
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized


if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
