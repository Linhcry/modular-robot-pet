from sw_drawings import *

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    cat={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))}
    sleeve=cat['F07_CompressionSleeve'].copy()
    sleeve.update(drawing_scale=1.5,drawing_iso_scale=1.5,key_dimensions_mm='外径6；孔径3.4；名义长度49；当前夹紧候选装8件',notes='隔套两端支承侧梁翼缘，避免预紧压瘪槽梁；长度需随翼缘净距配合核定。端部去毛刺；公差与预紧未制造释放。')
    frame={'id':'ASM_ClampedBody','name':'机身框架贯穿夹紧候选','path':str(ROOT/'assemblies/机身框架_贯穿夹紧候选.SLDASM'),'bbox_mm':[-170,-112,0,170,112,101.6],'drawing_scale':.43,'key_dimensions_mm':'46个实例；8组贯穿连接；隔套49；夹紧厚59.5；M3×65伸出螺母3.1','material_assumption':'6061-T6与PA12；紧固件钢，等级待选','notes':'135个基准面配合；当前静态无实体干涉。螺钉和螺母为尺寸简化候选，商品规格待核。未含髋隔板及全机承载验证。'}
    try:
        results=[make(sw,r,True) for r in (sleeve,frame)]
        (ROOT/'validation/机身夹紧工程图检查.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
