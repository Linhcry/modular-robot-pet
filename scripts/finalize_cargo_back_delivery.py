from sw_core import *
import hashlib

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized
    cat={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))};properties=[]
    for code in ('B04_MainBack','B05_ServiceBack'):
        row=cat[code];d=cast(sw.OpenDoc6(row['path'],1,1,'',0,0)[0],'IModelDoc2');assert d
        try:
            props=cast(cast(d.Extension,'IModelDocExtension').CustomPropertyManager(''),'ICustomPropertyManager')
            a=props.Get6('零件编号',False);b=props.Get6('零件名称',False);assert row['id'] in a and row['name'] in b,(a,b)
            properties.append({'编号':code,'中文属性已核对':True})
        finally:sw.CloseDoc(d.GetTitle())
    assert sw.GetDocumentCount()==0
    review=ROOT/'validation/承载与分体背盖图纸交付复核.json';a=json.loads(review.read_text(encoding='utf-8'))
    hashes=json.loads((ROOT/'validation/最终未改页已审阅哈希.json').read_text(encoding='utf-8'))
    for n,value in hashes.items():assert hashlib.sha256((ROOT/'previews/drawings'/f'承载与分体背盖_最终_{n}.png').read_bytes()).hexdigest()==value
    assert hashlib.sha256(Path(a['合册']).read_bytes()).hexdigest()==a['SHA256']
    drawings=json.loads((ROOT/'validation/储物舱承载对接工程图检查.json').read_text(encoding='utf-8'));assert len(drawings)==7
    for row in drawings:assert Path(row['drawing']).exists()
    parts=json.loads((ROOT/'validation/本轮五个新件最终复核.json').read_text(encoding='utf-8'));assert len(parts)==5
    for row in parts:
        assert Path(row['STEP']).exists() and hashlib.sha256(Path(row['原生文件']).read_bytes()).hexdigest()==row['原生SHA256']
    a.update({'逐页人工视觉检查':'七页全部已查看；第5/6页最终重排后复看，其余五页最终PNG与已审阅版本哈希一致','已修正':['压板宽度尺寸移至轮廓外侧','背盖检查说明同步结果，避免句号单独换行'],'原生零件图数量':5,'原生装配图数量':2,'新件数量':5,'每件原生与STEP已检查':True,'复制零件属性':properties,'打开的SolidWorks文档数':sw.GetDocumentCount()})
    review.write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')
    log=ROOT/'docs/08_后台建模工作记录.md';text=log.read_text(encoding='utf-8');heading='## 2026-09-08 储物承载与分体背盖'
    if heading not in text:
        log.write_text(text+'\n\n'+heading+'\n\n新增F13支承上板、Q09导轨垫块、B04曲面主背盖、B05可拆曲面后背盖和Q10连接压板，均为独立中文SLDPRT，另导出STEP。完整储物舱与导轨锁座总成顶层47实例、138配合；套入真实护壳后发现旧背盖阻挡，已经采用曲面分体背盖解决。最终维护总成顶层22实例、64个配合特征，含子件118实例，11种离散姿态无额外实体干涉，并在重新打开后核对实际位置。\n\n距离配合的FlipDimension在本机环境影响其他配置：现用两个互斥方向配合，避免后盖跨过基准面后导致闭合配置漂移。检查包含压板紧固件的抑制状态、真实舱盖/舱体/后盖位置及12处压板安装轴；导轨锁座另核对40处孔轴。\n\n五张零件图与两张装配图已保存为SLDDRW，七页PDF已逐页视觉检查。最后0个打开文档。详细设计见13_储物舱承载对接与分体背盖.md。\n\n透明观察窗要求已更新：两块主窗，第三块可选，单块面积适当放大、固定点少且可接近；仍未按未选驱动的位置在外壳上切窗。GB/T7134当前与即将实施版本状态已记录。\n\n下一步仍需最终驱动与大工程师模型、整机减重、上板弯扭支承、背盖螺母防掉落及工具空间、窗口面板/边框、腿根/头尾/机械臂与全机装配。没有把几何无干涉称为强度通过，也没有把未选舵机的算术减重计入全机质量。\n',encoding='utf-8')
    print(json.dumps({'PDF':a['合册'],'SHA256':a['SHA256'],'页数':a['页数'],'新件':len(parts),'图纸':len(drawings),'打开文档数':0},ensure_ascii=False,indent=2))
