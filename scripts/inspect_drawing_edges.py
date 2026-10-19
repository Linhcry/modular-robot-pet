from sw_core import *
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();rows=json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'));out={}
    for code in ('C01','C02','C03','C04','C05','C06','Q02'):
        row=next(r for r in rows if r['id'].startswith(code+'_'));d=cast(sw.OpenDoc6(row['path'],1,1,'',0,0)[0],'IModelDoc2');circs=[]
        for b in body_list(d):
            for e in b.GetEdges():
                e=cast(e,'IEdge');c=cast(e.GetCurve(),'ICurve')
                if c.IsCircle():circs.append([round(v*1000,5) if i<3 or i==6 else round(v,5) for i,v in enumerate(c.CircleParams)])
        out[code]=circs;sw.CloseDoc(d.GetTitle())
    (ROOT/'validation/工程图圆边定位.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False))
