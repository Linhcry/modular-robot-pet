from sw_drawings import *

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized
    sw.DocumentVisible(True,1);sw.DocumentVisible(True,3);sw.CommandInProgress=True
    rows=json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))
    try:
        for prefix in ('H10','H11'):
            if len(sys.argv)>1 and prefix not in sys.argv[1:]:continue
            row=next(r for r in rows if r['id'].startswith(prefix+'_')).copy()
            row.update(drawing_scale=5 if prefix=='H11' else .85,drawing_iso_scale=5 if prefix=='H11' else .75)
            result=make(sw,row,True)
            p=ROOT/'validation/长臂螺母杯工程图检查.json'
            old=json.loads(p.read_text(encoding='utf-8')) if p.exists() else []
            p.write_text(json.dumps([r for r in old if r['id']!=row['id']]+[result],ensure_ascii=False,indent=2),encoding='utf-8')
    finally:
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
