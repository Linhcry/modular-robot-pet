"""Read exact PCB extrema and hole cylinders after manufacturer imports complete."""
from sw_core import *
import hashlib

def exact_box(b):
    low=[];high=[]
    for axis in range(3):
        vec=[0.,0.,0.];vec[axis]=1
        p=b.GetExtremePoint(*vec);assert p[0],p;high.append(p[axis+1]*1000)
        vec[axis]=-1;p=b.GetExtremePoint(*vec);assert p[0],p;low.append(p[axis+1]*1000)
    return low+high

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True;d=None;records=[]
    cat={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))}
    try:
        for code in ['V04_CM5Carrier','V05_CM5Core']:
            path=Path(cat[code]['path']);op=sw.OpenDoc6(str(path),1,1,'',0,0);assert op[1]==0;d=cast(op[0],'IModelDoc2')
            bs=body_list(d);candidates=[]
            for b in bs:
                box=b.GetBodyBox();size=sorted((box[i+3]-box[i])*1000 for i in range(3))
                if .9<size[0]<2.1 and 39.5<size[1]<40.5 and 54.5<size[2]<55.5:candidates.append(b)
            assert len(candidates)==1,(code,[(b.Name,b.GetBodyBox()) for b in candidates])
            pcb=candidates[0];box=exact_box(pcb);dims=[box[i+3]-box[i] for i in range(3)];thin=min(range(3),key=lambda i:dims[i]);holes=[]
            for raw in pcb.GetFaces():
                f=cast(raw,'IFace2');surface=cast(f.GetSurface(),'ISurface')
                if not surface.IsCylinder():continue
                p=surface.CylinderParams
                if .8<p[6]*1000<2.1 and abs(abs(p[3+thin])-1)<1e-6:
                    row={'轴线上点_mm':[v*1000 for v in p[:3]],'轴方向':list(p[3:6]),'半径_mm':p[6]*1000,'面积_mm2':f.GetArea()*1e6}
                    if not any(math.dist(row['轴线上点_mm'],x['轴线上点_mm'])<1e-4 and abs(row['半径_mm']-x['半径_mm'])<1e-6 for x in holes):holes.append(row)
            records.append({'编号':code,'文件':str(path),'SHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'实体数':len(bs),'PCB实体':pcb.Name,'PCB精确极值_mm':box,'PCB精确各轴尺寸_mm':dims,'PCB厚度轴':thin,'D1_6至D4_2且垂直PCB的圆柱孔':holes,'限制':'厂家几何实测；圆柱孔径不是螺纹规格，板边/铜层禁压区和连接器完整性须另行验证'})
            if code=='V05_CM5Core':records[-1]['厚度判读']='1.0762mm是选中大面积板体实体的厚度。官方STEP含DIELECTRIC产品定义，单一实体不能代替完整PCB叠层；夹紧厚度仍按厂家版本及手册1.24mm±10%核验。'
            sw.CloseDoc(d.GetTitle());d=None
        out=ROOT/'validation/CM5核心板与底板精确接口.json';out.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(records,ensure_ascii=False,indent=2))
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
