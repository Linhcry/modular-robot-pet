"""H10/H11 assembly with geometric mates and saved incremental checkpoints."""
from assemble_captive_head_nuts import common
from build_tolerant_head_nuts import *
import hashlib


def main(camera=False):
    sw=connect();assert sw.GetDocumentCount()==0,'Close only our prior CAD task before assembly'
    sw.Visible=True;sw.FrameState=C.swWindowMinimized
    sw.DocumentVisible(True,1);sw.DocumentVisible(True,2);sw.CommandInProgress=True;d=None
    rows={r['id']:r for r in json.loads(CAT_PATH.read_text(encoding='utf-8'))}
    out=ROOT/'assemblies/触控视觉头部_长臂螺母防落候选.SLDASM'
    checkpoint=ROOT/'wip/触控头部_长臂螺母防落_未验证检查点.SLDASM'
    if camera:
        rows['H06_ScreenBracket']=rows['H12_CameraScreenBracket']
        out=ROOT/'assemblies/触控视觉头部_自动对焦相机空间候选.SLDASM'
        checkpoint=ROOT/'wip/触控头部_自动对焦相机_未验证检查点.SLDASM'
    transforms=[]
    try:
        d=newdoc(sw,'asm')
        shell=add(sw,d,rows['H10_ClearanceHeadShell']['path'],'宽槽螺母杯定位曲面头壳')
        common(sw,d,shell,rows);save(d,checkpoint)
        cs=[cast(o,'IComponent2') for o in cast(d,'IAssemblyDoc').GetComponents(True)]
        bracket=next(c for c in cs if Path(c.GetPathName()).stem.startswith('H12_' if camera else 'H06_'))
        def put(code,name,xyz):return add(sw,d,rows[code]['path'],name,xyz)
        def coax(a,ar,b,br,point,name):mate_entities(d,cylinder_at(a,ar),cylinder_at(b,br,point),1,name,lock_rotation=True)
        def contact(a,az,b,bz,name):mate_entities(d,flat_face(a,az),flat_face(b,bz),0,name)
        for x,y in MOUNT_HOLES:
            tag=f'{x}_{y}'
            top=put('S02_M3Washer','承架上垫圈_'+tag,(x,y,51.2))
            coax(top,1.6,bracket,1.7,(x,y,0),'上垫圈同轴_'+tag);contact(top,0,bracket,2,'上垫圈承压面_'+tag)
            bolt=put('S01_M3x10','承架M3x10螺钉_'+tag,(x,y,51.7))
            coax(bolt,1.5,bracket,1.7,(x,y,0),'承架螺钉同轴_'+tag);contact(bolt,0,top,.5,'螺钉头承压面_'+tag)
            bottom=put('S02_M3Washer','环肩下垫圈_'+tag,(x,y,46.2))
            coax(bottom,1.6,shell,1.7,(x,y,46.7),'下垫圈同轴_'+tag);contact(bottom,.5,shell,46.7,'下垫圈承压面_'+tag)
            nut=put('S03_M3Nut','环肩M3螺母_'+tag,(x,y,43.8))
            coax(nut,1.5,shell,1.7,(x,y,46.7),'螺母同轴_'+tag);contact(nut,2.4,bottom,0,'螺母承压面_'+tag)
            cup=put('H11_LongArmNutCup','长臂卡扣螺母杯_'+tag,(x,y,CAP_Z))
            coax(cup,1.9,shell,1.7,(x,y,46.7),'螺母杯与螺钉共轴_'+tag);contact(cup,4.5,shell,42.1,'四点止挡贴合_'+tag)
            d.ForceRebuild3(False)
            for c,z in [(top,51.2),(bolt,51.7),(bottom,46.2),(nut,43.8),(cup,CAP_Z)]:
                actual=[c.Transform2.ArrayData[9+i]*1000 for i in range(3)]
                delta=max(abs(a-b) for a,b in zip(actual,(x,y,z)))
                assert delta<1e-4,(c.Name2,actual)
                transforms.append({'组件':c.Name2,'目标_mm':[x,y,z],'实测_mm':actual,'最大偏差_mm':delta})
            save(d,checkpoint);print('GROUP_DONE',tag,flush=True)
        if camera:
            from build_camera_carrier import CAM_ROT,CAM_XYZ,CARRIER_XYZ
            for code,name,xyz,rot in [('H13_CameraCarrier','四点绝缘相机托架',CARRIER_XYZ,IDENTITY),('V06_CameraModule3','官方自动对焦相机',CAM_XYZ,CAM_ROT)]:
                c=add(sw,d,rows[code]['path'],name,xyz,rot);mate_pose(d,shell,c,xyz,rot,name)
            save(d,checkpoint)
        require_memory('头部组件干涉检查',physical_gib=5,commit_gib=8)
        errors=[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]]
        clashes=interferences(d)
        components=[cast(o,'IComponent2') for o in cast(d,'IAssemblyDoc').GetComponents(True)]
        sources={c.GetPathName():hashlib.sha256(Path(c.GetPathName()).read_bytes()).hexdigest() for c in components}
        report={'日期':'2026-09-08','装配':str(out),'组件数':len(components),'配合数':len(list(all_mates(d))),
                '配合错误':errors,'干涉':clashes,'紧固组件定位':transforms,'原生零件SHA256':sources,
                '装配逻辑':'螺母杯与螺钉共轴；杯局部Z4.5止挡贴合头壳Z42.1。上下垫圈、螺母和螺钉按真实承压面配合。杯底与拧紧螺母底名义间隙0.6mm。',
                '边界':['本报告检查名义刚性几何及配合，不证明柔性装配应力、保持力和疲劳',
                        '尚未完成相机、控制板、面框和屏幕自身的完整紧固',
                        'STEP曲线导出和0.126%体积差异仍在独立诊断；本装配引用原生SLDPRT',
                        '未冻结制造公差、采购型号或完成实物验证']}
        if camera:
            report['边界'].append('相机与可换托架仅完成空间/基准配合候选，相机M2及托架M3紧固件尚未加入；官方PDF和STEP板厚存在差异。')
            report['相机安装变换']={'旋转':CAM_ROT,'原点_mm':CAM_XYZ,'托架原点_mm':CARRIER_XYZ}
        report_path=ROOT/'validation'/('自动对焦相机头部空间检查.json' if camera else '头部长臂螺母防落装配检查.json')
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        assert report['组件数']==(27 if camera else 25) and report['配合数']==(58 if camera else 52) and not errors and not clashes,{'组件数':report['组件数'],'配合数':report['配合数'],'配合错误':errors,'干涉':clashes}
        save(d,out);preview(d,out.stem)
        report['装配SHA256']=hashlib.sha256(out.read_bytes()).hexdigest()
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:report[k] for k in ['装配','组件数','配合数','配合错误','干涉']},ensure_ascii=False,indent=2))
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized


if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main(camera='--camera' in sys.argv)
