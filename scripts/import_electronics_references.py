"""Preserve manufacturer STEP geometry as Chinese named native reference parts."""
from sw_core import *
import hashlib,shutil

SOURCES=[('V03_DsiScreen','微雪2点8寸触控屏厂家参考','2.8寸DSI触控屏_厂家三维/2.8inch DSI LCD/2_8inch-dsi-lcd_asm.stp'),('V04_CM5Carrier','微雪CM5迷你底板A厂家参考','CM5迷你底板A_厂家三维/CM5-NANO-A.step'),('V05_CM5Core','树莓派CM5核心板官方参考','CM5核心板_官方三维/CM5R5-3dsteps.step')]

def inspect(body):
    row={'名称':body.Name,'包围盒_mm':[v*1000 for v in body.GetBodyBox()],'圆柱面':[],'平面':[]}
    if max(row['包围盒_mm'][j+3]-row['包围盒_mm'][j] for j in range(3))<18:
        row['接口提取']='小元件仅保留实体与包围盒';return row
    for raw in body.GetFaces():
        f=cast(raw,'IFace2');s=cast(f.GetSurface(),'ISurface')
        if s.IsCylinder():row['圆柱面'].append({'参数_m':list(s.CylinderParams),'面积_mm2':f.GetArea()*1e6})
        if s.IsPlane():row['平面'].append({'参数':list(s.PlaneParams),'面积_mm2':f.GetArea()*1e6})
    return row

def main():
    sw=connect();sw.FrameState=C.swWindowMinimized;sw.Visible=True;sw.FrameState=C.swWindowMinimized
    sw.DocumentVisible(True,1);sw.DocumentVisible(True,2);sw.CommandInProgress=True
    keys=[C.swDefaultTemplatePart,C.swDefaultTemplateAssembly];before={k:sw.GetUserPreferenceStringValue(k) for k in keys}
    flags={k:sw.GetUserPreferenceToggle(k) for k in (C.swAlwaysUseDefaultTemplates,C.swMultiCAD_Enable3DInterconnect,C.swImportAutoRunImportDiagnostics,C.swImportAutoRunImportDiagnosticsPersist,C.swImportNeutralRunDiagnostics)}
    mapping=sw.GetUserPreferenceIntegerValue(C.swImportNeutralAssemblyStructureMapping)
    (ROOT/'validation/电子模型导入前首选项.json').write_text(json.dumps({'字符串':before,'开关':flags,'装配映射':mapping},indent=2),encoding='utf-8')
    catfile=ROOT/'data/parts_catalog.json';cat=json.loads(catfile.read_text(encoding='utf-8'));reportfile=ROOT/'validation/电子模块厂家几何提取.json';report=json.loads(reportfile.read_text(encoding='utf-8')) if reportfile.exists() else []
    try:
        sw.SetUserPreferenceStringValue(keys[0],str(TEMPLATES/'gb_part.prtdot'));sw.SetUserPreferenceStringValue(keys[1],str(TEMPLATES/'gb_assembly.asmdot'))
        sw.SetUserPreferenceToggle(C.swAlwaysUseDefaultTemplates,True);sw.SetUserPreferenceToggle(C.swMultiCAD_Enable3DInterconnect,False)
        for key in (C.swImportAutoRunImportDiagnostics,C.swImportAutoRunImportDiagnosticsPersist,C.swImportNeutralRunDiagnostics):sw.SetUserPreferenceToggle(key,False)
        sw.SetUserPreferenceIntegerValue(C.swImportNeutralAssemblyStructureMapping,C.swImportNeutralAssemblyStructureMapping_MultibodyPart)
        for code,name,rel in SOURCES:
            if len(sys.argv)>1 and code.split('_')[0] not in sys.argv[1:]:continue
            require_memory('厂家复杂模型加载:'+code,physical_gib=6,commit_gib=10)
            source=ROOT/'vendor/electronics_sources'/rel
            import_path=ROOT/'tmp'/(code.split('_')[0]+'.step');shutil.copyfile(source,import_path)
            out=ROOT/'parts'/f'{code.split("_")[0]}_{name}.SLDPRT'
            if out.exists():
                d=cast(sw.OpenDoc6(str(out),1,1,'',0,0)[0],'IModelDoc2')
            else:
                data=cast(sw.GetImportFileData(str(import_path)),'IImportStepData');data.MapConfigurationData=False
                active=cast(sw.ActiveDoc,'IModelDoc2')
                if active and Path(active.GetTitle()).stem.lower() in (source.stem.lower(),import_path.stem.lower()):
                    d=active;print('接续已加载厂家模型',d.GetTitle(),flush=True)
                else:
                    print('开始导入',name,flush=True);res=sw.LoadFile4(str(import_path),'r',data,0);d=cast(res[0],'IModelDoc2');assert d,(name,res)
                copies=[]
                if d.GetType()==2:
                    for raw in cast(d,'IAssemblyDoc').GetComponents(False):
                        c=cast(raw,'IComponent2');m=cast(c.GetModelDoc2(),'IModelDoc2')
                        if not m or m.GetType()!=1:continue
                        for b in body_list(m):
                            b2=cast(b.Copy(),'IBody2');assert b2.ApplyTransform(c.Transform2);copies.append(b2)
                else:copies=[cast(b.Copy(),'IBody2') for b in body_list(d)]
                assert copies,'no solid bodies imported'
                sw.CloseDoc(d.GetTitle());d=newdoc(sw,'part');pd=cast(d,'IPartDoc')
                for i,b in enumerate(copies):
                    if i%25==0:require_memory('厂家实体转换:'+str(i),physical_gib=6,commit_gib=10)
                    f=cast(pd.CreateFeatureFromBody3(b,False,C.swCreateFeatureBodyCheck),'IFeature');assert f;f.Name=f'厂家实体_{i+1:03d}'
                    if (i+1)%25==0 or i+1==len(copies):print('原生实体转换',name,i+1,'/',len(copies),flush=True)
                for k,v in {'零件编号':code,'零件名称':name,'来源':str(source),'设计说明':'厂家STEP实体复制；保留原始坐标。采购件参考，非自制零件；几何不包含安装公差、线缆弯曲与热设计保证。'}.items():d.AddCustomInfo3('',k,30,v)
                save(d,out)
            bs=body_list(d);details=[inspect(b) for b in bs];boxes=[b.GetBodyBox() for b in bs]
            bbox=[min(b[i] for b in boxes)*1000 for i in range(3)]+[max(b[i+3] for b in boxes)*1000 for i in range(3)]
            preview(d,name)
            record={'编号':code,'文件':str(out),'来源':str(source),'来源SHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'实体数':len(bs),'包围盒_mm':bbox,'实体':details}
            report=[r for r in report if r['编号']!=code]+[record]
            cat=[r for r in cat if r['id']!=code]+[{'id':code,'name':name,'kind':'purchased_reference','path':str(out),'solid_count':len(bs),'bbox_mm':bbox,'material_assumption':'厂家采购电子组件；不可据此参考几何推算总质量','key_dimensions_mm':'厂家原始坐标；详见接口提取审计','notes':'未采购。原厂STEP派生，非大工程师模型。'}]
            catfile.write_text(json.dumps(cat,ensure_ascii=False,indent=2),encoding='utf-8')
            (ROOT/'validation/电子模块厂家几何提取.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
            sw.CloseDoc(d.GetTitle());print('已保存关闭',name,'实体',len(bs),'包围盒',bbox,flush=True)
    finally:
        for k,v in before.items():sw.SetUserPreferenceStringValue(k,v)
        for k,v in flags.items():sw.SetUserPreferenceToggle(k,v)
        sw.SetUserPreferenceIntegerValue(C.swImportNeutralAssemblyStructureMapping,mapping)
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
