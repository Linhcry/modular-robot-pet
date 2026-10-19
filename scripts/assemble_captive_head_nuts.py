from build_captive_head_nuts import *
import hashlib

def common(sw,d,root,rows):
    for code,name,xyz,rot in [('H05_TouchBezel','触控与相机面框',(0,0,60),IDENTITY),('H06_ScreenBracket','屏幕承架',(0,0,49.2),IDENTITY),('V03_DsiScreen','厂家触控屏',(-2,-12,61.1),PANEL_ROT),('H07_ScreenSeal','齐平柔性密封圈',(0,0,60.6),IDENTITY)]:
        c=add(sw,d,rows[code]['path'],name,xyz,rot);mate_pose(d,root,c,xyz,rot,name)

def main():
    sw=connect();sw.Visible=True;sw.FrameState=C.swWindowMinimized;sw.DocumentVisible(True,1);sw.DocumentVisible(True,2);sw.CommandInProgress=True;d=None
    rows={r['id']:r for r in json.loads(CAT_PATH.read_text(encoding='utf-8'))}
    out=ROOT/'assemblies/触控视觉头部_螺母防落候选.SLDASM'
    try:
        d=newdoc(sw,'asm');shell=add(sw,d,rows['H08_CaptiveHeadShell']['path'],'螺母杯定位曲面头壳');common(sw,d,shell,rows)
        checkpoint=ROOT/'wip/触控头部_螺母防落_未验证检查点.SLDASM'
        save(d,checkpoint)
        cs=[cast(o,'IComponent2') for o in cast(d,'IAssemblyDoc').GetComponents(True)]
        bracket=next(c for c in cs if Path(c.GetPathName()).stem.startswith('H06_'))
        def put(code,name,xyz):return add(sw,d,rows[code]['path'],name,xyz)
        def coax(a,ar,b,br,point,name):mate_entities(d,cylinder_at(a,ar),cylinder_at(b,br,point),1,name,lock_rotation=True)
        def contact(a,az,b,bz,name):mate_entities(d,flat_face(a,az),flat_face(b,bz),0,name)
        for x,y in MOUNT_HOLES:
            tag=f'{x}_{y}'
            top=put('S02_M3Washer','承架上垫圈_'+tag,(x,y,51.2));coax(top,1.6,bracket,1.7,(x,y,0),'上垫圈同轴_'+tag);contact(top,0,bracket,2,'上垫圈承压面_'+tag)
            bolt=put('S01_M3x10','承架M3x10螺钉_'+tag,(x,y,51.7));coax(bolt,1.5,bracket,1.7,(x,y,0),'承架螺钉同轴_'+tag);contact(bolt,0,top,.5,'螺钉头承压面_'+tag)
            bottom=put('S02_M3Washer','环肩下垫圈_'+tag,(x,y,46.2));coax(bottom,1.6,shell,1.7,(x,y,46.7),'下垫圈同轴_'+tag);contact(bottom,.5,shell,46.7,'下垫圈承压面_'+tag)
            nut=put('S03_M3Nut','环肩M3螺母_'+tag,(x,y,43.8));coax(nut,1.5,shell,1.7,(x,y,46.7),'螺母同轴_'+tag);contact(nut,2.4,bottom,0,'螺母承压面_'+tag)
            cup=put('H09_CaptiveNutCup','卡扣螺母杯_'+tag,(x,y,CAP_Z));coax(cup,1.9,shell,1.7,(x,y,46.7),'螺母杯与螺钉共轴_'+tag);contact(cup,2.5,shell,42.1,'四点止挡贴合_'+tag)
            d.ForceRebuild3(False)
            for c,z in [(top,51.2),(bolt,51.7),(bottom,46.2),(nut,43.8),(cup,CAP_Z)]:assert max(abs(c.Transform2.ArrayData[9+i]*1000-v) for i,v in enumerate((x,y,z)))<1e-4,(c.Name2,list(c.Transform2.ArrayData))
            save(d,checkpoint)
        require_memory('头部25组件干涉检查',physical_gib=5,commit_gib=8)
        errors=[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]];clashes=interferences(d)
        save(d,out);preview(d,'触控视觉头部_螺母防落候选')
        report={'日期':'2026-09-08','装配':str(out),'组件数':len(cast(d,'IAssemblyDoc').GetComponents(True)),'配合数':len(list(all_mates(d))),'配合错误':errors,'干涉':clashes,'装配逻辑':'螺母杯与螺钉共轴，杯的四点止挡贴合头壳定位座底面；螺母和上下垫圈仍按真实承压面配合。杯底与拧紧后螺母底面名义留0.2mm。','边界':['卡扣只作名义刚性几何，装入弹性变形与保持力未完成实物验证','装配路径、卡钩限位与螺母防转的几何反例检查另行记录','螺钉预紧力、PA12压溃蠕变与长期温升仍未验证','屏幕/面框紧固、相机、控制板与整机仍未完成']}
        (ROOT/'validation/头部螺母防落装配检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
        assert report['组件数']==25 and report['配合数']==52 and not errors and not clashes
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
