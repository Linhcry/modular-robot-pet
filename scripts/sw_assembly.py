from sw_core import *

def mm_array(values):
    return VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,values)

IDENTITY=(1,0,0,0,1,0,0,0,1)
def transform(sw,xyz=(0,0,0),rot=IDENTITY):
    # SolidWorks uses basis vectors as rows in its 16-element transform array.
    return cast(sw.GetMathUtility(),'IMathUtility').CreateTransform(mm_array((*rot,*(v/1000 for v in xyz),1,0,0,0)))

def add(sw,d,path,name,xyz=(0,0,0),rot=IDENTITY):
    require_memory('新增装配组件:'+name)
    path=Path(path)
    # The referenced document must already be loaded for AddComponent5.
    if not sw.GetOpenDocumentByName(str(path)):
        sw.OpenDoc6(str(path),2 if path.suffix.upper()=='.SLDASM' else 1,1,'',0,0)
    active=cast(sw.ActiveDoc,'IModelDoc2')
    if active is None or active.GetTitle()!=d.GetTitle():sw.ActivateDoc3(d.GetTitle(),True,0,0)
    a=cast(d,'IAssemblyDoc')
    c=cast(a.AddComponent5(str(path),0,'',False,'',0.,0.,0.),'IComponent2')
    assert c is not None, f'AddComponent failed {path}'
    before_names=sw.GetUserPreferenceToggle(C.swExtRefUpdateCompNames)
    sw.SetUserPreferenceToggle(C.swExtRefUpdateCompNames,False)
    try:
        d.ClearSelection2(True);c.Select4(False,None,False);c.Name2=name
        assert c.Name2.startswith(name),('component rename failed',name,c.Name2)
    finally:
        d.ClearSelection2(True);sw.SetUserPreferenceToggle(C.swExtRefUpdateCompNames,before_names)
    c.Transform2=transform(sw,xyz,rot)
    # Close only the separate component window; the assembly retains its loaded reference.
    ref=cast(c.GetModelDoc2(),'IModelDoc2')
    if ref and ref.GetTitle()!=d.GetTitle():sw.CloseDoc(ref.GetTitle())
    return c

def select_components(d,cs):
    d.ClearSelection2(True)
    sd=cast(cast(d.SelectionManager,'ISelectionMgr').CreateSelectData(),'ISelectData');sd.Mark=1
    for i,c in enumerate(cs):assert c.Select4(i>0,sd,False)

def lock(d,base,other,name):
    select_components(d,[base,other])
    result=cast(d,'IAssemblyDoc').AddMate5(16,2,False,0,0,0,0,0,0,0,0,False,False,0,0)
    d.ClearSelection2(True)
    print('刚性配合',name,'状态',result[1],flush=True)
    assert result[0] is not None and result[1]==C.swAddMateError_NoError,(name,result)
    # AddMate returns Mate2; the corresponding feature is the last mate subfeature.
    name_last_mate(d,name)
    return result

def name_last_mate(d,name):
    groups=[f for f in features(d) if f.GetTypeName2()=='MateGroup']
    if not groups:return
    f=groups[-1].GetFirstSubFeature();last=None
    while f:
        f=cast(f,'IFeature');last=f;f=f.GetNextSubFeature()
    if last:
        try:last.Name=name
        except Exception:pass

def cylinder_face(comp,radius):
    doc=cast(comp.GetModelDoc2(),'IModelDoc2')
    matches=[]
    for b in body_list(doc):
        for f in b.GetFaces():
            f=cast(f,'IFace2');s=cast(f.GetSurface(),'ISurface')
            if s.IsCylinder() and abs(s.CylinderParams[6]-radius/1000)<1e-7:
                matches.append(f)
    assert matches, (comp.Name2,radius)
    f=max(matches,key=lambda x:x.GetArea())
    return cast(comp.GetCorrespondingEntity(cast(f,'IEntity')),'IEntity')

def flat_face(comp,z,normal_axis=2):
    doc=cast(comp.GetModelDoc2(),'IModelDoc2');matches=[]
    for b in body_list(doc):
        for f in b.GetFaces():
            f=cast(f,'IFace2');s=cast(f.GetSurface(),'ISurface')
            if s.IsPlane():
                p=s.PlaneParams
                if abs(abs(p[normal_axis])-1)<1e-6 and abs(p[normal_axis+3]-z/1000)<1e-6:matches.append(f)
    assert matches,(comp.Name2,z)
    return cast(comp.GetCorrespondingEntity(cast(max(matches,key=lambda x:x.GetArea()),'IEntity')),'IEntity')

def mate_entities(d,a,b,kind,name,distance=0,angle=0,align=2,lock_rotation=False):
    d.ClearSelection2(True)
    sd=cast(cast(d.SelectionManager,'ISelectionMgr').CreateSelectData(),'ISelectData');sd.Mark=1
    assert a.Select4(False,sd);assert b.Select4(True,sd)
    result=cast(d,'IAssemblyDoc').AddMate5(kind,align,False,distance/1000,distance/1000,distance/1000,0,0,angle,angle,angle,False,lock_rotation,0,0)
    d.ClearSelection2(True)
    print('几何配合',name,'状态',result[1],flush=True)
    assert result[0] is not None and result[1]==C.swAddMateError_NoError,(name,result)
    name_last_mate(d,name)
    return result

def cylinder_at(comp,radius,point=(0,0,0),axis=2):
    """Select a cylindrical face by local radius and axis position, never face index."""
    doc=cast(comp.GetModelDoc2(),'IModelDoc2');matches=[]
    for body in body_list(doc):
        for face in body.GetFaces():
            face=cast(face,'IFace2');s=cast(face.GetSurface(),'ISurface')
            if not s.IsCylinder():continue
            p=s.CylinderParams
            if abs(p[6]-radius/1000)>1e-7 or abs(abs(p[3+axis])-1)>1e-6:continue
            if all(abs(p[i]-point[i]/1000)<1e-6 for i in range(3) if i!=axis):matches.append(face)
    assert matches,('cylinder_at',comp.Name2,radius,point,axis)
    return cast(comp.GetCorrespondingEntity(cast(max(matches,key=lambda f:f.GetArea()),'IEntity')),'IEntity')

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sw=connect();d=newdoc(sw,'asm')
    path=ROOT/'validation/interface_coupon.SLDPRT'
    a=add(sw,d,path,'BASE')
    b=add(sw,d,path,'ROTATING_PLATE',(0,0,7))
    print('FIXED',a.IsFixed(),b.IsFixed(),flush=True)
    mate_entities(d,cylinder_face(a,4),cylinder_face(b,4),1,'COAXIAL')
    mate_entities(d,flat_face(a,6),flat_face(b,0),5,'AXIAL_GAP',distance=1)
    save(d,ROOT/'validation/hinge_coupon.SLDASM')
    preview(d,'hinge_coupon')
