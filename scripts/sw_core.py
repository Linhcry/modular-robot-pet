from __future__ import annotations
import json, math, sys, time
from pathlib import Path
import pythoncom
import win32com.client as wc
from win32com.client import VARIANT, gencache
from sw_memory import require_memory, MemoryBudgetExceeded

ROOT = Path(__file__).resolve().parents[1]
SW_HOME = Path(r'D:\Program Files\SOLIDWORKS Corp\SOLIDWORKS')
TEMPLATES = Path(r'C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2026\templates')
pythoncom.CoInitialize()
LIB = gencache.EnsureModuleForTypelibInterface(pythoncom.LoadTypeLib(str(SW_HOME/'sldworks.tlb')),bForDemand=0)
C = gencache.EnsureModuleForTypelibInterface(pythoncom.LoadTypeLib(str(SW_HOME/'swconst.tlb')),bForDemand=0).constants
NULL = None

def cast(obj, name):
    if obj is None:return None
    cls=getattr(LIB,name)
    return cls(obj._oleobj_.QueryInterface(cls.CLSID,pythoncom.IID_IDispatch))

def connect():
    require_memory('连接SolidWorks以开始建模')
    return cast(wc.GetActiveObject('SldWorks.Application'),'ISldWorks')

def newdoc(sw,kind):
    require_memory('新建文档:'+kind)
    name={'part':'gb_part.prtdot','asm':'gb_assembly.asmdot','drawing':'gb_a3.drwdot'}[kind]
    d=cast(sw.NewDocument(str(TEMPLATES/name),0,0.,0.),'IModelDoc2')
    assert d is not None, f'NewDocument failed: {name}'
    return d

def features(d):
    f=d.FirstFeature()
    while f:
        f=cast(f,'IFeature');yield f;f=f.GetNextFeature()

def plane(d,index=0):
    ps=[f for f in features(d) if f.GetTypeName2()=='RefPlane']
    assert len(ps)>=3
    d.ClearSelection2(True);assert ps[index].Select2(False,0)
    return ps[index]

def sketch(d,name,draw,index=0):
    plane(d,index)
    sm=cast(d.SketchManager,'ISketchManager');sm.InsertSketch(True)
    sm.AddToDB=True
    try:draw(sm)
    finally:sm.AddToDB=False
    active=cast(sm.ActiveSketch,'ISketch')
    d.ClearSelection2(True)
    result=sm.FullyDefineSketch(True,True,1023,True,1,NULL,1,NULL,0,0)
    sm.InsertSketch(True)
    f=[x for x in features(d) if x.GetTypeName2()=='ProfileFeature'][-1];f.Name=name
    d.ClearSelection2(True);assert f.Select2(False,0)
    return f,result

def extrude(d,name,depth,z=0,merge=True):
    fm=cast(d.FeatureManager,'IFeatureManager')
    f=fm.FeatureExtrusion2(True,False,False,0,0,depth/1000,0,False,False,False,False,0,0,False,False,False,False,merge,True,True,3 if z else 0,abs(z)/1000,z<0)
    assert f is not None, 'Extrusion failed '+name
    f=cast(f,'IFeature');f.Name=name;return f

def body_list(d):
    return [cast(b,'IBody2') for b in (cast(d,'IPartDoc').GetBodies2(0,True) or [])]

def chamfer_top(d,width=.3):
    bodies=body_list(d)
    assert bodies
    box=bodies[0].GetBodyBox();z=box[5]
    edges=[]
    for e in bodies[0].GetEdges() or []:
        e=cast(e,'IEdge')
        v1=e.GetStartVertex();v2=e.GetEndVertex()
        if v1 and v2:
            a=cast(v1,'IVertex').GetPoint();b=cast(v2,'IVertex').GetPoint()
            if abs(a[2]-z)<1e-7 and abs(b[2]-z)<1e-7:edges.append(e)
    d.ClearSelection2(True)
    for i,e in enumerate(edges):assert cast(e,'IEntity').Select4(i>0,NULL)
    if not edges:return None
    f=cast(d.FeatureManager,'IFeatureManager').InsertFeatureChamfer(0,1,width/1000,math.pi/4,0,0,0,0)
    if f:cast(f,'IFeature').Name='EDGE_C'+str(width)
    d.ClearSelection2(True)
    return f

def save(d,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    d.ClearSelection2(True)
    if d.GetType()!=3:
        for flag in (5,6,19,196):d.SetUserPreferenceToggle(flag,False)
    d.ForceRebuild3(False)
    r=cast(d.Extension,'IModelDocExtension').SaveAs(str(path),0,1,NULL,0,0)
    print('SAVE',path.name,r,flush=True)
    assert r[0] and r[1]==0 and path.exists(),f'Save failed: {path}, {r}'
    return r

def color(d,rgb):
    d.MaterialPropertyValues=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,(*rgb,.35,.7,.25,.2,0.,0.))

def preview(d,name):
    d.ShowNamedView2('*Isometric',7);d.ViewZoomtofit2();d.GraphicsRedraw2()
    p=ROOT/'previews'/f'{name}.bmp';p.parent.mkdir(exist_ok=True,parents=True)
    return d.SaveBMP(str(p),1400,1000)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sw=connect();print('CONNECTED',sw.RevisionNumber(),sw.GetDocumentCount(),flush=True)
    d=newdoc(sw,'part')
    def draw(sm):
        sm.CreateCornerRectangle(-.032,-.020,0,.032,.020,0)
        sm.CreateCircleByRadius(0,0,0,.004)
        for x in [-.023,.023]:
            for y in [-.012,.012]:sm.CreateCircleByRadius(x,y,0,.0017)
    f,status=sketch(d,'BASE_PROFILE',draw)
    print('SKETCH_FULL_DEFINE',status,flush=True)
    extrude(d,'THICKNESS_6',6)
    print('BODY_COUNT',len(body_list(d)),flush=True)
    print('CHAMFER',bool(chamfer_top(d)),flush=True)
    color(d,(.32,.48,.58))
    save(d,ROOT/'validation'/'interface_coupon.SLDPRT')
    preview(d,'interface_coupon')
    print('FEATURES',[(f.Name,f.GetTypeName2()) for f in features(d)],flush=True)
