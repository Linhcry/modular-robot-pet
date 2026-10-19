"""Derive lightweight, geometrically exact mounting members from the preserved factory STEP.

These are purchased-actuator reference representations, not new manufactured motor designs.
The internal rotor, gear set and electronics are deliberately omitted and the mass is not inferred.
"""
from sw_assembly import *


def describe(body):
    out=[]
    for face in body.GetFaces():
        face=cast(face,'IFace2');surface=cast(face.GetSurface(),'ISurface')
        if not surface.IsCylinder():continue
        p=list(surface.CylinderParams)
        if abs(p[6]-.001025)>.0000001:continue
        points=[]
        for edge in face.GetEdges():
            edge=cast(edge,'IEdge');curve=cast(edge.GetCurve(),'ICurve')
            if curve.IsCircle():points.append(list(curve.CircleParams)[:3])
            for v in (edge.GetStartVertex(),edge.GetEndVertex()):
                if v:points.append(list(cast(v,'IVertex').GetPoint()))
        out.append({'轴心及半径':p,'边界点_mm':[[round(v*1000,6) for v in a] for a in points]})
    return out


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.CommandInProgress=True
    src=ROOT/'vendor/motor_sources/AK45-10_厂家原始三维.SLDASM'
    d=cast(sw.OpenDoc6(str(src),2,1,'',0,0)[0],'IModelDoc2');assert d
    # Canonical frame: Z=0 rear mounting face, Z=43 output face; preserve factory angular zero.
    canonical=transform(sw,(0,0,30.5),(1,0,0,0,0,-1,0,1,0))
    groups={'V01_AK4510Stator':{'name':'AK45-10定子安装参考','members':{'112':'厂家后端盖','117':'厂家定子壳体','111':'厂家固定端环'},'bodies':[]},
            'V02_AK4510Output':{'name':'AK45-10输出法兰参考','members':{'101':'厂家输出法兰'},'bodies':[]}}
    report={'厂家装配':str(src),'坐标转换':'X=厂家X，Y=厂家Z，Z=30.5-厂家Y；毫米','说明':'保留选定外部结构的精确实体，省略内部传动、轴承、紧固件和电路。不可由该参考几何推算采购电机质量。','parts':[]}
    try:
        for obj in cast(d,'IAssemblyDoc').GetComponents(False):
            comp=cast(obj,'IComponent2');path=Path(comp.GetPathName());part=cast(comp.GetModelDoc2(),'IModelDoc2')
            if not part or part.GetType()!=1:continue
            for code,group in groups.items():
                for suffix,label in group['members'].items():
                    if path.stem!=f'AK45-10_厂家零件{suffix}':continue
                    for body in body_list(part):
                        copy=cast(body.Copy(),'IBody2');assert copy.ApplyTransform(comp.Transform2);assert copy.ApplyTransform(canonical)
                        group['bodies'].append((label,copy,str(path)))
        assert len(groups['V01_AK4510Stator']['bodies'])==3
        assert len(groups['V02_AK4510Output']['bodies'])==1
        sw.CloseDoc(d.GetTitle())
        cat=json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))
        for code,group in groups.items():
            part=newdoc(sw,'part');pd=cast(part,'IPartDoc');details=[]
            for label,body,path in group['bodies']:
                holes=describe(body)
                f=cast(pd.CreateFeatureFromBody3(body,False,C.swCreateFeatureBodyCheck),'IFeature');assert f,(label,'native body insertion failed')
                f.Name=label;details.append({'名称':label,'来源':path,'M2_5几何孔':holes})
            assert len(body_list(part))==len(group['bodies'])
            color(part,(.13,.16,.19) if code.startswith('V01') else (.68,.72,.75))
            notes='厂家STEP外部构件派生，孔位与安装面保真。省略内部传动、紧固件和电路；质量以完整AK45-10 KV75厂家260g为基准，不能把两个参考件各算一台电机。'
            dims='坐标Z=0为背面安装面，输出端Z=43；外径53；定子5×M2.5分度圆45；输出3×M2.5分度圆27；孔深须以实物螺纹有效深度最终确认。'
            for key,value in {'零件编号':code.split('_')[0],'零件名称':group['name'],'采购型号':'CubeMars AK45-10 KV75，非V3.0','来源':'厂家STEP几何派生；非自行设计制造件','设计说明':notes,'关键尺寸':dims}.items():part.AddCustomInfo3('',key,30,value)
            out=ROOT/'parts'/f"{code.split('_')[0]}_{group['name']}.SLDPRT";save(part,out);preview(part,group['name'])
            boxes=[list(b.GetBodyBox()) for b in body_list(part)];bbox=[min(b[i] for b in boxes)*1000 for i in range(3)]+[max(b[i+3] for b in boxes)*1000 for i in range(3)]
            row={'id':code,'name':group['name'],'kind':'purchased_reference','path':str(out),'material_assumption':'厂家采购组件；不得据简化几何计算总质量','key_dimensions_mm':dims,'notes':notes,'bbox_mm':bbox,'solid_count':len(boxes),'features':[{'name':f.Name,'type':f.GetTypeName2(),'error':f.GetErrorCode2()} for f in features(part) if f.GetTypeName2()=='Imported'],'purchase_group':'CubeMars AK45-10 KV75'}
            cat=[r for r in cat if r['id']!=code]+[row]
            report['parts'].append({'id':code,'path':str(out),'solid_count':len(boxes),'details':details})
            (ROOT/'data/parts_catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2),encoding='utf-8')
            sw.CloseDoc(part.GetTitle());print('派生并关闭',group['name'],len(boxes),flush=True)
        (ROOT/'validation/AK45-10轻量接口来源.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CommandInProgress=False
