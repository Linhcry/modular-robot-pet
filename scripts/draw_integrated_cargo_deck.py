from sw_drawings import *

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    rows={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))};result=[];requested=set(sys.argv[1:])
    try:
        for code in ('F13_CargoSupportedDeck','Q09_RailPad','B04_MainBack','B05_ServiceBack','Q10_BackStrap'):
            if requested and code.split('_')[0] not in requested:continue
            r=rows[code].copy();r['drawing_scale']=.6 if code.startswith('F13') else .5 if code.startswith('B0') else 2. if code.startswith('Q09') else 1.5;r['drawing_iso_scale']=r['drawing_scale']
            result.append(make(sw,r,True))
        r={'id':'ASM_IntegratedCargoDeck','name':'储物舱导轨锁止与承载板','path':str(ROOT/'assemblies/储物舱_导轨锁止与承载板.SLDASM'),'bbox_mm':[-110,-95,-7.5,110,95,86],'drawing_scale':.6,'drawing_iso_scale':.6,'material_assumption':'6061-T6与PA12，销及紧固件为钢','key_dimensions_mm':'上板220×190×2；导轨垫高3；舱底Z18.2；销提升9后向负X退出','notes':'含完整储物舱、导轨与防脱结构；离散配置已检查。尚未纳入机身外壳的取出路径及承载验证；紧固件为公称简化件。'}
        if not requested or 'ASM_Deck' in requested:result.append(make(sw,r,True))
        r={'id':'ASM_SplitServiceBack','name':'分体曲面背盖与储物舱维护候选','path':str(ROOT/'assemblies/分体曲面背盖与储物舱_维护候选.SLDASM'),'bbox_mm':[-166,-112,-71.8,170,112,86],'drawing_scale':.42,'drawing_iso_scale':.42,'material_assumption':'6061-T6与PA12，销及紧固件为钢','key_dimensions_mm':'前后背盖接缝0.6；2块圆角连接压板；4组M3×16连接件','notes':'日常开舱盖；拆舱须先卸两压板并移开后盖。图为几何维护候选；工具空间、螺母防掉落和外壳最终固定仍待完善。'}
        if not requested or 'ASM_Back' in requested:result.append(make(sw,r,True))
        audit=ROOT/'validation/储物舱承载对接工程图检查.json'
        if requested and audit.exists():result=[r for r in json.loads(audit.read_text(encoding='utf-8')) if r['id'] not in {x['id'] for x in result}]+result
        audit.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
