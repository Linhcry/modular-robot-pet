from sw_core import *

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.CommandInProgress=True
    d=cast(sw.OpenDoc6(str(ROOT/'vendor/motor_sources/AK45-10_厂家原始三维.SLDASM'),2,1,'',0,0)[0],'IModelDoc2')
    result=[]
    try:
        for obj in cast(d,'IAssemblyDoc').GetComponents(False):
            c=cast(obj,'IComponent2');part=cast(c.GetModelDoc2(),'IModelDoc2')
            if not part or part.GetType()!=1:continue
            row={'name':c.Name2,'path':c.GetPathName(),'transform':list(c.Transform2.ArrayData),'assembly_bbox_mm':[v*1000 for v in c.GetBox(False,False)],'cylinders':[],'planes':[],'solid_count':len(body_list(part))}
            for body in body_list(part):
                for face in body.GetFaces():
                    face=cast(face,'IFace2');surf=cast(face.GetSurface(),'ISurface')
                    if surf.IsCylinder():row['cylinders'].append({'params':list(surf.CylinderParams),'area_mm2':face.GetArea()*1e6})
                    if surf.IsPlane():row['planes'].append({'params':list(surf.PlaneParams),'area_mm2':face.GetArea()*1e6})
            result.append(row)
            print(c.Name2,'bbox',[round(v,2) for v in row['assembly_bbox_mm']],'cylinders',len(row['cylinders']),flush=True)
        (ROOT/'validation/AK45-10厂家接口提取.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False
