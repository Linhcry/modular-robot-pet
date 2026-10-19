"""Detect missing STEP curve references and incomplete transfers, without SW."""
from occt_head_path_audit import *
import re, io
from OCP.IFSelect import IFSelect_ItemsByEntity
from OCP.TopAbs import TopAbs_FACE


def face_count(shape):
    ex=TopExp_Explorer(shape,TopAbs_FACE);n=0
    while ex.More():n+=1;ex.Next()
    return n


def main():
    results=[]
    for code in ('H04','H05','H06','H07','H08','H09','H10','H11'):
        gate('逐个检查导出:'+code)
        path=next((ROOT/'exports/step').glob(code+'_*'))
        text=path.read_text(encoding='latin1')
        missing=[{'实体号':int(m[1]),'原始定义':m[2].strip()}
                 for m in re.finditer(r'#(\d+)\s*=\s*(EDGE_CURVE\s*\([^;]*?,\s*\$\s*,[^;]*\))\s*;',text)]
        with tempfile.TemporaryDirectory(prefix='pet-step-audit-') as folder:
            p=Path(folder)/'part.step';shutil.copyfile(path,p)
            reader=STEPControl_Reader();status=reader.ReadFile(str(p));assert status==IFSelect_RetDone
            count=reader.TransferRoots();shape=reader.OneShape()
            load_log=io.BytesIO();transfer_log=io.BytesIO()
            reader.PrintCheckLoad(load_log,False,IFSelect_ItemsByEntity)
            reader.PrintCheckTransfer(transfer_log,False,IFSelect_ItemsByEntity)
        body_list=solids(shape);total_faces=face_count(shape);solid_faces=sum(face_count(s) for s in body_list)
        usable=not missing and count>0 and len(body_list)==1 and total_faces==solid_faces and BRepCheck_Analyzer(shape).IsValid()
        record={'编号':code,'文件':str(path),'SHA256':hashlib.sha256(path.read_bytes()).hexdigest(),
                '缺少曲线定义的边':missing,'读取根数':count,'实体数':len(body_list),'总面数':total_faces,
                '实体内面数':solid_faces,'实体外面数':total_faces-solid_faces,'可用于本轮实体求交':usable,
                '载入日志':load_log.getvalue().decode('utf-8',errors='replace'),
                '转换日志':transfer_log.getvalue().decode('utf-8',errors='replace')}
        if usable:record['有效实体体积_mm3']=volume(shape)
        results.append(record)
        del reader,shape,body_list;gc.collect()
    report={'阶段':'导出兼容性审计完成；含待修复文件','检查器':'OCCT 7.9.3；未启动SolidWorks',
            '文件':results,'结论边界':'输入STEP缺少曲线定义可直接由文件文本确认；实体丢面是当前OCCT读取结果。不能据此直接认定原生SLDPRT损坏，也不能使用不完整转换体做无干涉结论。',
            '本进程内存':win32process.GetProcessMemoryInfo(win32api.GetCurrentProcess())}
    (ROOT/'validation/头部STEP导出完整性检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps([{'编号':r['编号'],'缺失曲线边数':len(r['缺少曲线定义的边']),'实体外面数':r['实体外面数'],'可用于实体求交':r['可用于本轮实体求交']} for r in results],ensure_ascii=False,indent=2))
    print('PeakWorkingSetMiB',report['本进程内存']['PeakWorkingSetSize']/1024**2)


if __name__=='__main__':
    import sys;sys.stdout.reconfigure(encoding='utf-8');main()
