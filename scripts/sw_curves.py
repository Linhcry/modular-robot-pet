from sw_core import *

def line(sm,a,b):return sm.CreateLine(a[0]/1000,a[1]/1000,0,b[0]/1000,b[1]/1000,0)
def arc(sm,a,b,m):return sm.Create3PointArc(a[0]/1000,a[1]/1000,0,b[0]/1000,b[1]/1000,0,m[0]/1000,m[1]/1000,0)
def roundrect(sm,w,h,r,cx=0,cy=0):
    x,y=cx-w/2,cy-h/2;k=math.sqrt(.5)
    line(sm,(x+r,y),(x+w-r,y));arc(sm,(x+w-r,y),(x+w,y+r),(x+w-r+r*k,y+r-r*k))
    line(sm,(x+w,y+r),(x+w,y+h-r));arc(sm,(x+w,y+h-r),(x+w-r,y+h),(x+w-r+r*k,y+h-r+r*k))
    line(sm,(x+w-r,y+h),(x+r,y+h));arc(sm,(x+r,y+h),(x,y+h-r),(x+r-r*k,y+h-r+r*k))
    line(sm,(x,y+h-r),(x,y+r));arc(sm,(x,y+r),(x+r,y),(x+r-r*k,y+r-r*k))

def section(d,name,z,draw):
    p=plane(d,0)
    if z:
        ref=cast(d.FeatureManager,'IFeatureManager').InsertRefPlane(8,z/1000,0,0,0,0)
        assert ref
        f=[x for x in features(d) if x.GetTypeName2()=='RefPlane'][-1]
        f.Name=name+'_基准面';d.ClearSelection2(True);f.Select2(False,0)
    sm=cast(d.SketchManager,'ISketchManager');sm.InsertSketch(True);sm.AddToDB=True
    try:draw(sm)
    finally:sm.AddToDB=False
    sm.FullyDefineSketch(True,True,1023,True,1,None,1,None,0,0)
    sm.InsertSketch(True)
    f=[x for x in features(d) if x.GetTypeName2()=='ProfileFeature'][-1];f.Name=name+'_草图'
    d.ClearSelection2(True);return f

def loft(d,name,sections):
    fs=[section(d,f'{name}_截面{i+1}',z,draw) for i,(z,draw) in enumerate(sections)]
    d.ClearSelection2(True)
    for i,f in enumerate(fs):assert f.Select2(i>0,1)
    f=cast(cast(d.FeatureManager,'IFeatureManager').InsertProtrusionBlend2(False,True,False,1,0,0,1,1,True,True,False,0,0,0,True,True,True,0),'IFeature')
    assert f,'Loft failed '+name;f.Name=name;d.ClearSelection2(True);return f

def ellipse(w,h):return lambda sm:sm.CreateEllipse(0,0,0,w/2000,0,0,0,h/2000,0)

def shell_open_end(d,z,thickness=3):
    found=[]
    for b in body_list(d):
        for face in b.GetFaces():
            face=cast(face,'IFace2');s=cast(face.GetSurface(),'ISurface')
            if s.IsPlane() and abs(s.PlaneParams[5]-z/1000)<1e-6:found.append(face)
    assert found,('shell end plane',z)
    d.ClearSelection2(True)
    assert cast(max(found,key=lambda f:f.GetArea()),'IEntity').Select4(False,None)
    before=[f.Name for f in features(d)]
    result=d.InsertFeatureShell(thickness/1000,False)
    fs=[f for f in features(d) if f.Name not in before]
    assert fs,('Shell feature absent',result)
    fs[-1].Name='等壁厚抽壳_'+str(thickness)+'mm'
    print('SHELL',result,fs[-1].GetErrorCode2(),flush=True)
    d.ClearSelection2(True)

def cut(d,name,depth=100,z=0,both=False):
    f=cast(cast(d.FeatureManager,'IFeatureManager').FeatureCut3(True,False,True,1 if both else 0,0,depth/1000,0,False,False,False,False,0,0,False,False,False,False,False,True,True,False,False,False,3 if z else 0,abs(z)/1000,z<0),'IFeature')
    assert f,'Cut failed '+name;f.Name=name;return f

def fillet_outer_end(d,z,r):
    edges=[]
    for b in body_list(d):
        for e in b.GetEdges():
            e=cast(e,'IEdge');v=e.GetStartVertex();w=e.GetEndVertex()
            if v and w and all(abs(cast(vv,'IVertex').GetPoint()[2]-z/1000)<1e-6 for vv in (v,w)):edges.append(e)
    d.ClearSelection2(True)
    for i,e in enumerate(edges):cast(e,'IEntity').Select4(i>0,None)
    if not edges:return None
    f=cast(cast(d.FeatureManager,'IFeatureManager').FeatureFillet3(3,r/1000,0,0,0,0,0,None,None,None,None,None,None,None),'IFeature')
    if f:f.Name='外观圆角_R'+str(r)
    d.ClearSelection2(True);return f

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();d=newdoc(sw,'part')
    loft(d,'视觉头壳_连续曲面',[(0,ellipse(70,60)),(12,ellipse(88,74)),(38,ellipse(82,68)),(50,ellipse(70,56))])
    shell_open_end(d,50,3)
    color(d,(.83,.88,.88));save(d,ROOT/'validation/曲面头壳试件.SLDPRT');preview(d,'曲面头壳试件')
