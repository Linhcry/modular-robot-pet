"""Read a repaired candidate in SW without replacing the native source."""
from sw_core import *
import hashlib, shutil, tempfile


def body_record(b):
    cylinders=[]
    for f in b.GetFaces():
        s=cast(cast(f,'IFace2').GetSurface(),'ISurface')
        if s.IsCylinder():cylinders.append(list(s.CylinderParams))
    return {'体积_mm3':b.GetMassProperties(1)[3]*1e9,'Check2原始返回':b.Check2(),
            '面数':len(b.GetFaces()),'边数':len(b.GetEdges()),'圆柱面参数_m':cylinders,
            '极值_mm':[[v*1000 for v in b.GetExtremePoint(*vec)[1:]] for vec in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]]}


def main():
    sw=connect();assert sw.GetDocumentCount()==0
    sw.Visible=True;sw.FrameState=C.swWindowMinimized;sw.DocumentVisible(True,1);sw.CommandInProgress=True;d=None
    src=ROOT/'parts/H10_宽槽螺母杯定位曲面头壳.SLDPRT'
    candidate=ROOT/'wip/STEP修复候选/H10_宽槽螺母杯定位曲面头壳_保留原始实体号.STEP'
    if len(sys.argv)>1:candidate=Path(sys.argv[1]).resolve()
    report_name='头壳保留周期面STEP原生回读诊断' if '保留周期面' in candidate.stem else '头壳修复STEP原生回读诊断'
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (src,candidate)}
    flags={k:sw.GetUserPreferenceToggle(k) for k in (C.swAlwaysUseDefaultTemplates,C.swMultiCAD_Enable3DInterconnect,C.swImportAutoRunImportDiagnostics,C.swImportAutoRunImportDiagnosticsPersist,C.swImportNeutralRunDiagnostics)}
    old_template=sw.GetUserPreferenceStringValue(C.swDefaultTemplatePart)
    old_mapping=sw.GetUserPreferenceIntegerValue(C.swImportNeutralAssemblyStructureMapping)
    report={'输入SHA256':hashes,'边界':'独立候选回读；不覆盖原生源或正式STEP。布尔原始错误码须单独解释。'}
    try:
        r=sw.OpenDoc6(str(src),1,3,'',0,0);assert r[0] and not r[1]
        d=cast(r[0],'IModelDoc2');native=cast(body_list(d)[0].Copy(),'IBody2')
        report['原生']=body_record(native);sw.CloseDoc(d.GetTitle());d=None
        sw.SetUserPreferenceStringValue(C.swDefaultTemplatePart,str(TEMPLATES/'gb_part.prtdot'))
        sw.SetUserPreferenceToggle(C.swAlwaysUseDefaultTemplates,True)
        for k in flags:
            if k!=C.swAlwaysUseDefaultTemplates:sw.SetUserPreferenceToggle(k,False)
        sw.SetUserPreferenceIntegerValue(C.swImportNeutralAssemblyStructureMapping,C.swImportNeutralAssemblyStructureMapping_MultibodyPart)
        with tempfile.TemporaryDirectory(prefix='pet-head-roundtrip-') as folder:
            p=Path(folder)/'head_repaired.step';shutil.copyfile(candidate,p)
            data=cast(sw.GetImportFileData(str(p)),'IImportStepData');data.MapConfigurationData=False
            print('开始回读单件修复STEP候选',flush=True)
            r=sw.LoadFile4(str(p),'r',data,0);report['导入错误码']=r[1];assert r[0],r
            d=cast(r[0],'IModelDoc2');assert d.GetType()==1
            bs=body_list(d);report['回读实体数']=len(bs)
            assert len(bs)==1
            imported=bs[0];report['回读']=body_record(imported)
            report['同内核体积差_mm3']=report['回读']['体积_mm3']-report['原生']['体积_mm3']
            report['双向差集']=[]
            for label,a,b in [('原生减回读',native,imported),('回读减原生',imported,native)]:
                r=cast(a.Copy(),'IBody2').Operations2(C.SWBODYCUT,cast(b.Copy(),'IBody2'),0)
                bodies=[cast(x,'IBody2') for x in (r[0] or [])]
                report['双向差集'].append({'方向':label,'内核原始返回':r[1],'结果实体数':len(bodies),
                                           '体积_mm3':sum(x.GetMassProperties(1)[3]*1e9 for x in bodies)})
            report['双向差集有效']=all(r['内核原始返回'] in (C.swBodyOperationNoError,C.swBodyOperationEmptyBody,C.swBodyOperationDisjointBodies,C.swBodyOperationNoIntersect) for r in report['双向差集'])
            report['原生等价验证通过']=report['双向差集有效'] and abs(report['同内核体积差_mm3'])<.1 and all(r['体积_mm3']<.1 for r in report['双向差集'])
            report['布尔说明']='1058为swBodyOperationBooleanFail；失败时空结果不能解读为零差异。'
            out=ROOT/'wip/STEP修复候选'/(report_name+'.SLDPRT');save(d,out)
            sw.CloseDoc(d.GetTitle());d=None
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        for k,v in flags.items():sw.SetUserPreferenceToggle(k,v)
        sw.SetUserPreferenceStringValue(C.swDefaultTemplatePart,old_template)
        sw.SetUserPreferenceIntegerValue(C.swImportNeutralAssemblyStructureMapping,old_mapping)
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
        assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
        (ROOT/'validation'/(report_name+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k not in ('原生','回读','输入SHA256')},ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
