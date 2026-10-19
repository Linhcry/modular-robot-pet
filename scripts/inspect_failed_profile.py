from sw_core import *
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8');s=connect();d=cast(s.GetDocuments()[0],'IModelDoc2')
f=[f for f in features(d) if f.GetTypeName2()=='ProfileFeature'][-1]
sk=cast(f.GetSpecificFeature2(),'ISketch');segments=sk.GetSketchSegments() or []
print('SEGMENTS',len(segments),'CONTOURS',len(sk.GetSketchContours() or []),flush=True)
counts=Counter();details=[]
for obj in segments:
    sg=cast(obj,'ISketchSegment');typ=sg.GetType()
    if typ==0:
        q=cast(obj,'ISketchLine');a=cast(q.GetStartPoint2(),'ISketchPoint');b=cast(q.GetEndPoint2(),'ISketchPoint')
        pts=[(a.X,a.Y,a.Z),(b.X,b.Y,b.Z)]
    elif typ==1:
        q=cast(obj,'ISketchArc');a=cast(q.GetStartPoint2(),'ISketchPoint');b=cast(q.GetEndPoint2(),'ISketchPoint')
        pts=[(a.X,a.Y,a.Z),(b.X,b.Y,b.Z)]
        if max(abs(x-y) for x,y in zip(*pts))<1e-7:continue
    else:continue
    pp=[tuple(round(v*1000,5) for v in p) for p in pts]
    counts.update(pp);details.append({'type':typ,'ends_mm':pp})
print('ODD ENDPOINTS',[(k,v) for k,v in counts.items() if v%2],flush=True)
(ROOT/'validation/减重板失败草图诊断.json').write_text(json.dumps({'segments':details,'endpoint_counts':[{'point':k,'count':v} for k,v in counts.items()]},ensure_ascii=False,indent=2),encoding='utf-8')
