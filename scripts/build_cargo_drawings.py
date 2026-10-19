from sw_drawings import *
from collections import Counter
import csv

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.CommandInProgress=True
    cat=json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'));rows={r['id']:r for r in cat}
    audit=json.loads((ROOT/'validation/储物舱装配审计.json').read_text(encoding='utf-8'))
    count=Counter(r['code'] for r in audit['components'])
    with (ROOT/'data/储物舱物料表.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['序号','零件编号','中文名称','数量','类别','文件'])
        for i,(code,qty) in enumerate(sorted(count.items()),1):
            r=rows[code];kind={'custom':'自制件','standard_simplified':'国标尺寸简化件','purchased_reference':'采购件参考','envelope':'待选型包络'}.get(r['kind'],r['kind']);writer.writerow([i,code.split('_')[0],r['name'],qty,kind,r['path']])
    log_path=ROOT/'validation/储物舱工程图检查.json'
    results={r['id']:r for r in json.loads(log_path.read_text(encoding='utf-8'))} if log_path.exists() else {}
    try:
        desired=set(sys.argv[1:])
        for code in ('C01_CargoShell','C02_Lid','C03_Tray','C04_HingeLeaf','C05_MovingHinge','C06_HingePin','Q02_Shoe'):
            if desired and code.split('_')[0] not in desired:continue
            results[code]=make(sw,rows[code],True)
            log_path.write_text(json.dumps(list(results.values()),ensure_ascii=False,indent=2),encoding='utf-8')
        path=ROOT/'assemblies/储物舱模块.SLDASM'
        row={'id':'ASM_Cargo','name':'储物舱模块','path':str(path),'bbox_mm':[-77,-62,-12.7,92,69,65],
             'key_dimensions_mm':'闭合装配包络约169×131×77.7；舱体150×120×48；开启角0~90度',
             'material_assumption':'各零件材料详见物料表，均为设计假设',
             'notes':'47个实例，92个配合。铰链同心，单侧轴向间隙0.5。0至90度每15度检查：配合无错误，无非预期实体干涉。M3螺纹以公称杆和底孔简化。详见储物舱物料表.csv。'}
        if not desired or 'ASM' in desired:results[row['id']]=make(sw,row,True)
        log_path.write_text(json.dumps(list(results.values()),ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CommandInProgress=False
