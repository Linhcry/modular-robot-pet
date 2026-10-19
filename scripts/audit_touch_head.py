from build_touch_head import *
import hashlib

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    rows={r['id']:r for r in json.loads(CAT_PATH.read_text(encoding='utf-8'))};parts=[];doc=None
    try:
        for code,_,_,_,_ in PARTS:
            r=rows[code];doc=cast(sw.OpenDoc6(r['path'],1,1,'',0,0)[0],'IModelDoc2');doc.ForceRebuild3(False);bs=body_list(doc)
            volume=sum(b.GetMassProperties(1)[3] for b in bs)*1e9;assert len(bs)==1 and volume>1
            errors=[f.Name for f in features(doc) if f.GetErrorCode2()[0]];assert not errors
            props=cast(cast(doc.Extension,'IModelDocExtension').CustomPropertyManager(''),'ICustomPropertyManager');assert r['name'] in props.Get6('零件名称',False)
            parts.append({'编号':code,'实体数':len(bs),'体积_mm3':volume,'重建错误':errors,'中文名称':r['name'],'原生SHA256':hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()});sw.CloseDoc(doc.GetTitle());doc=None
        path=ROOT/'assemblies/触控视觉头部_空间与安装候选.SLDASM';op=sw.OpenDoc6(str(path),2,1,'',0,0);assert op[1]==0,op[1:];doc=cast(op[0],'IModelDoc2');doc.ForceRebuild3(False)
        comps={Path(c.GetPathName()).stem.split('_')[0]:c for c in [cast(o,'IComponent2') for o in cast(doc,'IAssemblyDoc').GetComponents(True)]};assert len(comps)==5
        records=[]
        def axes(code,radius):
            c=comps[code];m=cast(c.GetModelDoc2(),'IModelDoc2');arr=c.Transform2.ArrayData;out=[]
            for b in body_list(m):
                for raw in b.GetFaces():
                    s=cast(cast(raw,'IFace2').GetSurface(),'ISurface')
                    if not s.IsCylinder():continue
                    p=s.CylinderParams
                    if abs(p[6]*1000-radius)>.001:continue
                    xyz=[sum(p[k]*arr[3*k+j] for k in range(3))*1000+arr[9+j]*1000 for j in range(3)]
                    out.append(xyz)
            return out
        a=axes('H06',1.45);vendor=axes('V03',.88)
        for x,y in SCREEN_HOLES:
            ea=min(math.hypot(p[0]-x,p[1]-y) for p in a);ev=min(math.hypot(p[0]-x,p[1]-y) for p in vendor)
            assert max(ea,ev)<1e-4;records.append({'连接':'屏幕螺柱与承架','目标轴_mm':[x,y],'承架偏差_mm':ea,'厂家螺柱偏差_mm':ev})
        for ca,cb,r,points,label in [('H04','H06',1.7,MOUNT_HOLES,'承架与头壳'),('H04','H05',1.45,BEZEL_HOLES,'面框与头壳')]:
            aa=axes(ca,r);bb=axes(cb,r)
            for x,y in points:
                e1=min(math.hypot(p[0]-x,p[1]-y) for p in aa);e2=min(math.hypot(p[0]-x,p[1]-y) for p in bb);assert max(e1,e2)<1e-4
                records.append({'连接':label,'目标轴_mm':[x,y],'第一零件偏差_mm':e1,'第二零件偏差_mm':e2})
        clashes=interferences(doc);errors=[f.Name for f in all_mates(doc) if f.GetErrorCode2()[0]];assert not clashes and not errors
        front={}
        for code in ('H05','H07','V03'):
            c=comps[code];m=cast(c.GetModelDoc2(),'IModelDoc2');arr=c.Transform2.ArrayData;planes=[]
            for b in body_list(m):
                for raw in b.GetFaces():
                    s=cast(cast(raw,'IFace2').GetSurface(),'ISurface')
                    if s.IsPlane() and abs(abs(s.PlaneParams[2])-1)<1e-6:
                        p=s.PlaneParams;planes.append((sum(p[3+k]*arr[3*k+2] for k in range(3))+arr[11])*1000)
            front[code]=max(planes)
        assert max(front.values())-min(front.values())<1e-5,front
        stops=[];dimension=cast(doc.Parameter('D1@齐平柔性密封圈_Z'),'IDimension');nominal=dimension.SystemValue
        try:
            for delta in (-.1,.1):
                assert dimension.SetSystemValue3(nominal+delta/1000,1,None)==0;doc.ForceRebuild3(False)
                contacts=interferences(doc)
                stop=[p for p in contacts if any('H07_' in n or '齐平柔性密封圈' in n for n in p['components']) and any('H05_' in n or '触控与相机面框' in n for n in p['components'])]
                assert stop,('seal has axial escape/play',delta,contacts)
                for contact in stop:contact['classification']='故意越位产生的预期防脱限位干涉'
                stops.append({'故意轴向越位_mm':delta,'预期面框限位接触':stop,'意义':'刚性名义几何中存在限位；不证明柔性材料拔出力或薄唇强度'})
        finally:
            assert dimension.SetSystemValue3(nominal,1,None)==0;doc.ForceRebuild3(False)
        assert not interferences(doc),'nominal assembly not restored'
        result={'日期':'2026-09-08','重新打开检查':True,'独立零件':parts,'组件数':len(comps),'配合数':len(list(all_mates(doc))),'配合错误':errors,'实际孔轴连接':records,'齐平面实际Z_mm':front,'干涉':clashes,'柔性圈轴向限位反例检查':stops,'模型范围':'四件自制件与厂家屏幕；柔性圈为装配态名义形状；不包括紧固件、相机、计算板、线缆或整机运动'}
        (ROOT/'validation/触控头部最终孔轴复核.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
    finally:
        if doc:sw.CloseDoc(doc.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
