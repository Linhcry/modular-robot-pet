"""One native part, read-only; compare mass accuracy and export a separate AP214 candidate."""
from sw_core import *
import hashlib,re


def main():
    sw=connect();assert sw.GetDocumentCount()==0,'Run in an empty background SW session'
    sw.Visible=True;sw.FrameState=C.swWindowMinimized;sw.DocumentVisible(True,1)
    sw.CommandInProgress=True;d=None
    source=ROOT/'parts/H10_宽槽螺母杯定位曲面头壳.SLDPRT'
    original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    old_ap=sw.GetUserPreferenceIntegerValue(C.swStepAP)
    try:
        require_memory('只读打开单件头壳')
        r=sw.OpenDoc6(str(source),1,C.swOpenDocOptions_Silent|C.swOpenDocOptions_ReadOnly,'',0,0)
        assert r[0] is not None and r[1]==0,r
        d=cast(r[0],'IModelDoc2');d.ClearSelection2(True);bs=body_list(d);assert len(bs)==1
        report={'原生SHA256':original_hash,'原生体积_GetMassProperties_mm3':bs[0].GetMassProperties(1)[3]*1e9,
                '实体Check2原始返回':bs[0].Check2(),'质量精度对比':[],'无三维曲线边数':0}
        for edge in bs[0].GetEdges():
            if cast(edge,'IEdge').GetCurve() is None:report['无三维曲线边数']+=1
        prop=cast(cast(d.Extension,'IModelDocExtension').CreateMassProperty2(),'IMassProperty2');prop.UseSystemUnits=True
        for label,level in [('低',C.swMassPropertyAccuracyLevel_Lower),('中',C.swMassPropertyAccuracyLevel_Medium),('高',C.swMassPropertyAccuracyLevel_Higher)]:
            require_memory('单件质量属性精度:'+label)
            prop.AccuracyLevel=level;recalculated=prop.Recalculate()
            report['质量精度对比'].append({'精度':label,'级别':level,'重算返回':recalculated,'体积_mm3':prop.Volume*1e9})
        out=ROOT/'wip/STEP修复候选/H10_宽槽头壳_原生AP214.STEP'
        require_memory('单件AP214导出')
        sw.SetUserPreferenceIntegerValue(C.swStepAP,214);save(d,out)
        report['AP214候选']={'路径':str(out),'SHA256':hashlib.sha256(out.read_bytes()).hexdigest(),
                            '缺失曲线引用数':len(re.findall(r'EDGE_CURVE\s*\([^;]*?,\s*\$\s*,',out.read_text(encoding='latin1')))}
        report['边界']='只读源零件的诊断和另存导出；须独立回读、闭合性及接口检查后再替换正式STEP。'
        (ROOT/'validation/原生头壳高精度体积与AP214检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False,indent=2))
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.SetUserPreferenceIntegerValue(C.swStepAP,old_ap);sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
        assert hashlib.sha256(source.read_bytes()).hexdigest()==original_hash,'Native source unexpectedly changed'


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
