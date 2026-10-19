"""Candidate-only reconstruction of omitted isoparametric edges from STEP surfaces.

No native geometry or source STEP is overwritten. Native round-trip remains required.
"""
from occt_head_path_audit import *
import re, collections, io
from OCP.StepToGeom import StepToGeom
from OCP.GeomToStep import GeomToStep_MakeBoundedCurve
from OCP.Geom import Geom_TrimmedCurve
from OCP.GeomConvert import GeomConvert
from OCP.GeomAPI import GeomAPI_ProjectPointOnSurf
from OCP.STEPControl import STEPControl_Writer
from OCP.IFSelect import IFSelect_ItemsByEntity


def main():
    code='H10'
    source=next((ROOT/'exports/step').glob(code+'_*'))
    text=source.read_text(encoding='latin1')
    entities=dict(re.findall(r'#(\d+)\s*=\s*(.*?);',text,re.S));parents=collections.defaultdict(list)
    for key,value in entities.items():
        for ref in set(re.findall(r'#(\d+)',value)):parents[ref].append(key)
    missing=[key for key,value in entities.items() if re.match(r'EDGE_CURVE\s*\([^;]*?,\s*\$\s*,',value)]
    assert len(missing)==2,missing
    def vertex_point(vertex):
        point_id=re.findall(r'#(\d+)',entities[vertex])[0]
        numbers=re.search(r'\(\s*[^,]*,\s*\((.*?)\)',entities[point_id],re.S)[1]
        return gp_Pnt(*(float(v) for v in numbers.split(',')))
    result=[]
    with tempfile.TemporaryDirectory(prefix='pet-step-seam-') as folder:
        input_path=Path(folder)/'input.step';shutil.copyfile(source,input_path)
        reader=STEPControl_Reader();assert reader.ReadFile(str(input_path))==IFSelect_RetDone
        model=reader.StepModel()
        original_count=model.NbEntities()
        # STEP reader numbers entities in physical record order; the SW file
        # occasionally swaps adjacent #labels, and IdentLabel is not populated.
        assert original_count==len(entities)
        by_label={int(label):index for index,label in enumerate(entities,1)}
        replacements={}
        for edge_id in missing:
            gate('重建缺失拼接边'+edge_id)
            layer=[edge_id]
            for _ in range(4):layer=list({parent for key in layer for parent in parents[key]})
            faces=[key for key in layer if entities[key].startswith('ADVANCED_FACE')]
            assert len(faces)==2,(edge_id,faces)
            surface_ids=[re.findall(r'#(\d+)',entities[f])[-1] for f in sorted(faces)]
            surfaces=[StepToGeom.MakeSurface_s(model.Value(by_label[int(n)])) for n in surface_ids]
            refs=re.findall(r'#(\d+)',entities[edge_id]);a,b=map(vertex_point,refs[:2])
            curve=None;detail=[]
            for surface_id,surface in zip(surface_ids,surfaces):
                projs=[GeomAPI_ProjectPointOnSurf(point,surface) for point in (a,b)]
                uv=[p.LowerDistanceParameters() for p in projs]
                distances=[p.LowerDistance() for p in projs]
                assert max(distances)<.0001,('endpoint off surface',surface_id,distances)
                u1,u2,_,_=surface.Bounds()
                u=min((u1,u2),key=lambda x:abs(x-uv[0][0])+abs(x-uv[1][0]))
                assert all(abs(point[0]-u)<1e-6 for point in uv),('not an isoparametric boundary',uv)
                assert uv[1][1]>uv[0][1],('unexpected parameter direction',uv)
                candidate=Geom_TrimmedCurve(surface.UIso(u),uv[0][1],uv[1][1])
                detail.append({'曲面实体号':surface_id,'恒定U':u,'端点UV':uv,'端点距曲面_mm':distances})
                if curve is None:curve=candidate
            residuals=[]
            for index in range(101):
                t=curve.FirstParameter()+(curve.LastParameter()-curve.FirstParameter())*index/100
                point=curve.Value(t)
                residuals.append(max(GeomAPI_ProjectPointOnSurf(point,s).LowerDistance() for s in surfaces))
            assert max(residuals)<.0001,('edge not on both surfaces',edge_id,max(residuals))
            replacement=GeomToStep_MakeBoundedCurve(GeomConvert.CurveToBSplineCurve_s(curve)).Value()
            model.AddWithRefs(replacement)
            edge=model.Value(by_label[int(edge_id)]);assert edge.EdgeGeometry() is None
            assert edge.SameSense(),'unexpected edge direction'
            edge.SetEdgeGeometry(replacement)
            assert edge.EdgeGeometry() is not None
            # Drop only this corrected entity's original read-error content;
            # otherwise the writer re-emits its cached '$' definition.
            model.ClearReportEntity(by_label[int(edge_id)])
            replacements[edge_id]=by_label[int(edge_id)]
            result.append({'缺失边实体号':edge_id,'相邻曲面':detail,'检查样本数':101,'对两侧曲面最大距离_mm':max(residuals),
                           '修复曲线端点偏差_mm':[curve.Value(curve.FirstParameter()).Distance(a),curve.Value(curve.LastParameter()).Distance(b)]})
        out=ROOT/'wip/STEP修复候选'/(source.stem+'_保留原始实体号.STEP');out.parent.mkdir(parents=True,exist_ok=True)
        temporary=Path(folder)/'reconstructed.step'
        writer=STEPControl_Writer(reader.WS(),False);assert writer.Write(str(temporary))==IFSelect_RetDone
        # The standard writer renumbers original entities. Keep original bytes
        # for all existing geometry and append only the new curve definitions.
        serialized=dict(re.findall(r'#(\d+)\s*=\s*(.*?);',temporary.read_text(encoding='latin1'),re.S))
        added={k:v for k,v in serialized.items() if int(k)>original_count}
        assert all(int(k)<=original_count for k in entities)
        assert all(ref in added for value in added.values() for ref in re.findall(r'#(\d+)',value)), 'new curve unexpectedly references renumbered old entities'
        patched=text
        for edge_id,writer_edge_number in replacements.items():
            curve_id=int(re.findall(r'#(\d+)',serialized[str(writer_edge_number)])[-1])
            assert str(curve_id) in added
            old=entities[edge_id];new=old.replace('$','#'+str(curve_id));assert old.count('$')==1
            pattern=re.compile(r'(#'+edge_id+r'\s*=\s*)'+re.escape(old)+r';')
            patched,n=pattern.subn(lambda m:m[1]+new+';',patched);assert n==1
        end=patched.rfind('ENDSEC;');assert end>0
        patched=patched[:end]+''.join('#'+k+' = '+v+';\n' for k,v in added.items())+patched[end:]
        out.write_text(patched,encoding='latin1')
    shape=read_step(out);actual=volume(shape)
    native=next(r for r in json.loads((ROOT/'validation/长臂螺母杯零件检查.json').read_text(encoding='utf-8')) if r['编号'].startswith(code))
    report={'状态':'闭合性通过，原生体积一致性未通过；仅修复候选','原STEP':str(source),'原STEP_SHA256':hashlib.sha256(source.read_bytes()).hexdigest(),
            '候选STEP':str(out),'候选STEP_SHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'重建边':result,
            '闭合有效实体数':len(solids(shape)),'重建STEP体积_mm3':actual,'原生记录体积_mm3':native['体积_mm3'],
            '体积差_mm3':actual-native['体积_mm3'],'本进程内存':win32process.GetProcessMemoryInfo(win32api.GetCurrentProcess()),
            '边界':'以已有相邻曲面的恒U边界重建遗漏的曲线定义；不替换原生文件。端点和曲面贴合为数值验证，尚未在SolidWorks回读、核查全部接口或完成总成干涉。'}
    (ROOT/'validation/头壳STEP等参边修复候选检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'候选':str(out),'重建边数':len(result),'闭合有效实体数':len(solids(shape)),
                      'STEP体积_mm3':actual,'体积差_mm3':report['体积差_mm3']},ensure_ascii=False,indent=2))
    assert abs(report['体积差_mm3'])<.1,'candidate volume differs from native record'


if __name__=='__main__':
    import sys;sys.stdout.reconfigure(encoding='utf-8');main()
