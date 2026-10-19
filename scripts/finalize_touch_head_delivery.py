"""Run only after visually reviewing all five final rendered pages."""
from build_touch_head import *
import hashlib

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized
    audit=json.loads((ROOT/'validation/触控头部最终孔轴复核.json').read_text(encoding='utf-8'));assert audit['组件数']==5 and audit['配合数']==12 and not audit['配合错误'] and not audit['干涉']
    assert len(audit['实际孔轴连接'])==12 and len(audit['独立零件'])==4
    drawings=json.loads((ROOT/'validation/触控头部工程图检查.json').read_text(encoding='utf-8'));assert len(drawings)==6
    for d in drawings:assert Path(d['drawing']).exists()
    cat={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))}
    for p in audit['独立零件']:
        path=Path(cat[p['编号']]['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==p['原生SHA256'];assert (ROOT/'exports/step'/(path.stem+'.STEP')).exists()
    review_path=ROOT/'validation/触控头部图纸交付复核.json';r=json.loads(review_path.read_text(encoding='utf-8'));assert r['页数']==5 and hashlib.sha256(Path(r['合册']).read_bytes()).hexdigest()==r['SHA256']
    clamped=ROOT/'assemblies/触控视觉头部_承架紧固候选.SLDASM'
    d=None;configs=[]
    try:
        d=cast(sw.OpenDoc6(str(clamped),2,1,'',0,0)[0],'IModelDoc2')
        for name,count in [('默认',0),('面框拆下_承架紧固',2),('默认',0)]:
            cm=cast(d.ConfigurationManager,'IConfigurationManager')
            if cast(cm.ActiveConfiguration,'IConfiguration').Name!=name:d.ShowConfiguration2(name)
            assert cast(cm.ActiveConfiguration,'IConfiguration').Name==name
            d.ForceRebuild3(False)
            cs=[cast(o,'IComponent2') for o in cast(d,'IAssemblyDoc').GetComponents(True)]
            suppressed=[Path(c.GetPathName()).stem for c in cs if c.IsSuppressed()]
            assert len(cs)==21 and len(suppressed)==count
            if count:assert {p.split('_')[0] for p in suppressed}=={'H05','H07'}
            mates=list(all_mates(d));errors=[f.Name for f in mates if f.GetErrorCode2()[0]]
            assert len(mates)==44 and not errors,(name,errors)
            clashes=interferences(d);assert not clashes,(name,clashes)
            configs.append({'配置':name,'组件数':len(cs),'抑制零件':suppressed,'配合数':len(mates),'配合错误':errors,'干涉':clashes})
    finally:
        if d:sw.CloseDoc(d.GetTitle())
    assert sw.GetDocumentCount()==0,('remaining SW documents',sw.GetDocumentCount())
    r.update({'逐页视觉检查':'五页最终PNG均已查看；装配主视图拆下面框、其他视图完整；78mm孔距正确，中文标注无裁切及重叠','已核对原生零件':4,'本合册原生工程图':5,'工程图库原生图数':6,'承架紧固总成配置复查':configs,'承架紧固总成SHA256':hashlib.sha256(clamped.read_bytes()).hexdigest(),'打开SolidWorks文档数':0,'齐平面实际Z_mm':audit['齐平面实际Z_mm'],'页面SHA256':{Path(p).name:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in r['页面渲染']}})
    review_path.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    log=ROOT/'docs/08_后台建模工作记录.md';previous=log.read_text(encoding='utf-8');heading='## 2026-09-08 触控头部齐平嵌入'
    if heading not in previous:
        log.write_text(previous+'\n\n'+heading+'\n\n新增H04曲面头壳、H05齐平面框、H06屏幕承架和隐藏走线槽、H07柔性密封圈；保留V03厂家2.8寸触控屏的10个实体。用户要求无缝嵌入后，取消0.8mm凹入，改为玻璃/面框/柔性圈前面同Z62.2。柔性圈背部承边被0.6mm薄唇和槽肩捕获，需试样验证弹性装配、公差、薄唇耐久，不作为模具制造图。\n\n五组件、12个真实基准配合；重开后12组孔轴复核通过，名义装配无实体干涉，三个齐平面实测一致。四张独立零件图和一张装配图保存为SLDDRW；五页合册完成逐页视觉检查。每件完成后保存关闭，最后0个打开文档。\n\nSM105BL-C001厂家规格书已下载并阅读尺寸/曲线。5.3kg目标含载荷、R1.5传动的三局部姿态与电动摆动区预筛通过；10kg敏感性中髋俯仰/膝额定不足。仍不能冻结驱动：大工程师模型、整机减重、带轮与轴承、制动回生/热与噪声待补。CM5-NANO-A厂家STEP已下载但SW导入失败，本轮未获得底板原生模型。\n\n接续：屏幕螺柱M2.5名称与内孔几何口径核对、头部全部紧固件/工具路径、相机真实接口和视场、CM5散热及接插件、颈部线缆与负载、透明观察窗、全机动作/质量与强度复核。详细记录见14和15号文档。\n',encoding='utf-8')
    print(json.dumps({'交付PDF':r['合册'],'页数':5,'配合数':44,'独立零件':4,'齐平面':r['齐平面实际Z_mm'],'打开文档':0},ensure_ascii=False,indent=2))
