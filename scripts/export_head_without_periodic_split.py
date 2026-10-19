"""Test native STEP periodic-surface export without modifying source geometry."""
from sw_core import *
import hashlib,re


def main():
    sw=connect();assert sw.GetDocumentCount()==0
    sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True;d=None
    source=ROOT/'parts/H10_宽槽螺母杯定位曲面头壳.SLDPRT'
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    old_split=sw.GetUserPreferenceToggle(C.swStepExportSplitPeriodic)
    old_ap=sw.GetUserPreferenceIntegerValue(C.swStepAP)
    report={'原生SHA256':digest,'原设置':{'拆分周期面':old_split,'AP':old_ap},'导出':[]}
    try:
        d=cast(sw.OpenDoc6(str(source),1,3,'',0,0)[0],'IModelDoc2');assert d
        for split in (False,True):
            sw.SetUserPreferenceToggle(C.swStepExportSplitPeriodic,split)
            sw.SetUserPreferenceIntegerValue(C.swStepAP,214)
            actual=sw.GetUserPreferenceToggle(C.swStepExportSplitPeriodic);assert actual==split
            out=ROOT/'wip/STEP修复候选'/('H10_原生AP214_'+('拆分周期面' if split else '保留周期面')+'.STEP')
            save(d,out);content=out.read_text(encoding='latin1')
            record={'拆分周期面':split,'路径':str(out),'SHA256':hashlib.sha256(out.read_bytes()).hexdigest(),
                    '缺失曲线边数':len(re.findall(r'EDGE_CURVE\s*\([^;]*?,\s*\$\s*,',content)),
                    'STEP面数':len(re.findall(r'=\s*ADVANCED_FACE\s*\(',content))}
            report['导出'].append(record);print(json.dumps(record,ensure_ascii=False),flush=True)
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.SetUserPreferenceToggle(C.swStepExportSplitPeriodic,old_split);sw.SetUserPreferenceIntegerValue(C.swStepAP,old_ap)
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
        assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
        (ROOT/'validation/头壳周期面拆分导出诊断.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
