from sw_drawings import *

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    cat={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))}
    selected={s for s in sys.argv[1:] if not s.startswith('--')}
    path=ROOT/'validation/后台设计工程图检查.json';results=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    items=[cat[code].copy() for code in ('F10_LightBelly','F11_LightDeck','Q05_ShortShoe','L01_UpperLink')]
    for row in items:
        if row['id']=='Q05_ShortShoe':row.update(drawing_scale=4.,drawing_iso_scale=2.5)
    items.append({'id':'ASM_BodyFit','name':'机身壳体与框架空间候选','path':str(ROOT/'assemblies/机身壳体与框架_空间候选.SLDASM'),'bbox_mm':[-170,-112,0,170,112,101.6],'drawing_scale':.43,'key_dimensions_mm':'名义主体最大轮廓约340×224×101.6；6个实例；15个基准面配合','material_assumption':'铝合金承载件与PA12护壳；均为材料假设','notes':'已检查当前静态空间装配无实体干涉。紧固件、横梁、关节、储物舱、头尾未加入本装配；不是整机装配或制造释放图。'})
    try:
        for row in items:
            if selected and row['id'] not in selected:continue
            print('开始工程图',row['id'],flush=True)
            results=[r for r in results if r['id']!=row['id']]
            results.append(make(sw,row,True))
            path.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CommandInProgress=False
