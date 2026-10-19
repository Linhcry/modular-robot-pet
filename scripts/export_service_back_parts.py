from sw_core import *
import hashlib

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True;out=[]
    rows={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))};requested=set(sys.argv[1:])
    try:
        for code in ('F13_CargoSupportedDeck','Q09_RailPad','B04_MainBack','B05_ServiceBack','Q10_BackStrap'):
            if requested and code.split('_')[0] not in requested:continue
            row=rows[code];d=cast(sw.OpenDoc6(row['path'],1,1,'',0,0)[0],'IModelDoc2');assert d
            try:
                props=cast(cast(d.Extension,'IModelDocExtension').CustomPropertyManager(''),'ICustomPropertyManager')
                for key,value in {'零件编号':row['id'],'零件名称':row['name'],'材料假设':row['material_assumption'],'关键尺寸':row['key_dimensions_mm'],'设计说明':row['notes']}.items():props.Add3(key,C.swCustomInfoText,value,C.swCustomPropertyReplaceValue)
                save(d,row['path'])
                d.ForceRebuild3(False);bs=body_list(d);errors=[f.Name for f in features(d) if f.GetErrorCode2()[0]];assert len(bs)==1 and not errors
                volume=sum(b.GetMassProperties(1)[3] for b in bs)*1e9;step=ROOT/'exports/step'/(Path(row['path']).stem+'.STEP');save(d,step)
                out.append({'编号':code,'中文名称':row['name'],'实体数':1,'重建错误':errors,'体积_mm3':volume,'质量_g_密度假设':volume*(.00101 if code.startswith('B0') else .0027),'原生文件':row['path'],'原生SHA256':hashlib.sha256(Path(row['path']).read_bytes()).hexdigest(),'STEP':str(step)})
            finally:sw.CloseDoc(d.GetTitle())
        audit=root_audit=ROOT/'validation/本轮五个新件最终复核.json'
        if requested and audit.exists():out=[r for r in json.loads(audit.read_text(encoding='utf-8')) if r['编号'] not in {x['编号'] for x in out}]+out
        audit.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print('FINAL_NEW_PARTS',len(out),'OPEN_DOCUMENTS',sw.GetDocumentCount(),flush=True)
    finally:sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
