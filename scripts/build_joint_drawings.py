from sw_drawings import *
import csv
from collections import Counter
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.CommandInProgress=True;rows={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))};results=[]
    requested={x for x in sys.argv[1:] if not x.startswith('--')}
    if '--background' in sys.argv:sw.FrameState=C.swWindowMinimized
    audit_path=ROOT/'validation/关节工程图检查.json'
    if audit_path.exists():results=json.loads(audit_path.read_text(encoding='utf-8'))
    try:
        for code in ('J05_AK4510StatorAdapter','J06_AK4510OutputAdapter','L01_UpperLink','L02_LowerLink','A01_ArmLink'):
            if requested and code not in requested:continue
            results=[r for r in results if r['id']!=code]
            results.append(make(sw,rows[code],True));(ROOT/'validation/关节工程图检查.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        row={'id':'ASM_Joint','name':'AK45-10大腿关节模块','path':str(ROOT/'assemblies/AK45-10大腿关节模块.SLDASM'),'bbox_mm':[-32,-169,-6,32,32,57.5],
             'key_dimensions_mm':'29个实例，57个配合；电机外径53、厚43；大腿轴距145；轴向距离配合已核对方向',
             'material_assumption':'电机按完整采购组件260g计；结构件材料为设计假设',
             'notes':'V01与V02合计代表一台AK45-10 KV75，非V3。抑制关节姿态角配合可释放输出转动。仅为一个关节模块；强度、温升及整机性能未验证。'}
        if not requested or 'ASM_Joint' in requested:
            results=[r for r in results if r['id']!='ASM_Joint']
            results.append(make(sw,row,True));(ROOT/'validation/关节工程图检查.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        audit=json.loads((ROOT/'validation/AK45-10关节装配审计.json').read_text(encoding='utf-8'));count=Counter(r['code'] for r in audit['components'])
        with (ROOT/'data/关节模块物料表.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f);writer.writerow(['图号','中文名称','模型实例数量','采购计数说明'])
            for code,n in count.items():writer.writerow([code.split('_')[0],rows[code]['name'],n,'V01+V02合计一台采购电机' if code.startswith(('V01','V02')) else '按数量备料；未采购'])
    finally:sw.CommandInProgress=False
