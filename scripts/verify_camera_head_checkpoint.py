from build_camera_carrier import *
import hashlib


def main():
    sw=connect();assert sw.GetDocumentCount()==0;sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True;d=None
    source=ROOT/'wip/触控头部_自动对焦相机_未验证检查点.SLDASM'
    out=ROOT/'assemblies/触控视觉头部_自动对焦相机空间候选.SLDASM'
    try:
        op=sw.OpenDoc6(str(source),2,1,'',0,0);assert op[0] and not op[1]
        d=cast(op[0],'IModelDoc2');d.ForceRebuild3(False)
        cs=[cast(o,'IComponent2') for o in cast(d,'IAssemblyDoc').GetComponents(True)]
        errors=[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]]
        assert len(cs)==27 and len(list(all_mates(d)))==58 and not errors,errors
        cam=next(c for c in cs if Path(c.GetPathName()).stem.startswith('V06_'))
        cm=cast(cam.GetModelDoc2(),'IModelDoc2');bs=body_list(cm);assert len(bs)==590
        boards=[]
        for b in bs:
            box=b.GetBodyBox();size=sorted((box[i+3]-box[i])*1000 for i in range(3))
            if .6<size[0]<.8 and 23.8<size[1]<23.9 and 24.9<size[2]<25.1:boards.append(b)
        assert len(boards)==1
        board=boards[0];axes=[];t=cam.Transform2.ArrayData
        for raw in board.GetFaces():
            surface=cast(cast(raw,'IFace2').GetSurface(),'ISurface')
            if not surface.IsCylinder():continue
            p=surface.CylinderParams
            if abs(p[6]*1000-1.1)>.001 or abs(abs(p[5])-1)>1e-6:continue
            world=[1000*(sum(t[j*3+i]*p[j] for j in range(3))+t[9+i]) for i in range(3)]
            if not any(math.dist(world[:2],a[:2])<.001 for a in axes):axes.append(world)
        expected=[(x,y+30) for x,y in CAM_HOLES];assert len(axes)==4
        deltas=[min(math.dist(a[:2],e) for e in expected) for a in axes];assert max(deltas)<.002
        clashes=interferences(d)
        report={'日期':'2026-09-08','装配':str(out),'组件数':27,'配合数':58,'配合错误':errors,'干涉':clashes,
                '相机保留实体数':len(bs),'相机板体Check2原始返回':board.Check2(),'相机安装孔轴_头部坐标_mm':axes,
                '相机孔轴到托架设计轴最大偏差_mm':max(deltas),
                '原生零件SHA256':{c.GetPathName():hashlib.sha256(Path(c.GetPathName()).read_bytes()).hexdigest() for c in cs},
                '边界':['相机及托架仅有基准定位配合，M2相机和M3托架完整紧固件尚未加入',
                        '官方STEP与PDF板厚不同；支承高度及实际夹紧尺寸须实物复核',
                        '名义刚性几何检查不证明光学入瞳、实拍视场、连续线缆行程、热或振动通过']}
        path=ROOT/'validation/自动对焦相机头部空间检查.json'
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        assert not clashes,clashes
        save(d,out);preview(d,out.stem)
        report['装配SHA256']=hashlib.sha256(out.read_bytes()).hexdigest()
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:report[k] for k in ['组件数','配合数','配合错误','干涉','相机保留实体数','相机孔轴到托架设计轴最大偏差_mm']},ensure_ascii=False),flush=True)
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized


if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
