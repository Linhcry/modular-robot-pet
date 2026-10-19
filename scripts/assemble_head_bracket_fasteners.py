"""Actual concentric/contact mates for the screen-bracket clamp stack."""
from build_touch_head import *
import shutil,hashlib

def main():
    sw=connect();sw.FrameState=C.swWindowMinimized;sw.Visible=True;sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True;d=None
    rows={r['id']:r for r in json.loads(CAT_PATH.read_text(encoding='utf-8'))}
    src=ROOT/'assemblies/触控视觉头部_空间与安装候选.SLDASM';dest=ROOT/'assemblies/触控视觉头部_承架紧固候选.SLDASM';shutil.copy2(src,dest)
    try:
        opened=sw.OpenDoc6(str(dest),2,1,'',0,0);assert opened[1]==0;d=cast(opened[0],'IModelDoc2')
        comps={Path(c.GetPathName()).stem.split('_')[0]:c for c in [cast(o,'IComponent2') for o in cast(d,'IAssemblyDoc').GetComponents(True)]};shell=comps['H04'];bracket=comps['H06'];stacks=[]
        def put(code,name,xyz):return add(sw,d,rows[code]['path'],name,xyz)
        def coax(a,ar,b,br,point,name):return mate_entities(d,cylinder_at(a,ar),cylinder_at(b,br,point),1,name,lock_rotation=True)
        def contact(a,az,b,bz,name):return mate_entities(d,flat_face(a,az),flat_face(b,bz),0,name)
        for x,y in MOUNT_HOLES:
            tag=f'{x}_{y}'
            top=put('S02_M3Washer','承架上垫圈_'+tag,(x,y,51.2));coax(top,1.6,bracket,1.7,(x,y,0),'上垫圈同轴_'+tag);contact(top,0,bracket,2,'上垫圈承压面_'+tag)
            bolt=put('S01_M3x10','承架M3x10螺钉_'+tag,(x,y,51.7));coax(bolt,1.5,bracket,1.7,(x,y,0),'承架螺钉同轴_'+tag);contact(bolt,0,top,.5,'螺钉头承压面_'+tag)
            bottom=put('S02_M3Washer','环肩下垫圈_'+tag,(x,y,46.2));coax(bottom,1.6,shell,1.7,(x,y,46.7),'下垫圈同轴_'+tag);contact(bottom,.5,shell,46.7,'下垫圈承压面_'+tag)
            nut=put('S03_M3Nut','环肩M3螺母_'+tag,(x,y,43.8));coax(nut,1.5,shell,1.7,(x,y,46.7),'螺母同轴_'+tag);contact(nut,2.4,bottom,0,'螺母承压面_'+tag)
            d.ForceRebuild3(False)
            actual={key:list(c.Transform2.ArrayData[9:12]) for key,c in [('螺钉',bolt),('上垫圈',top),('下垫圈',bottom),('螺母',nut)]}
            for key,z in [('螺钉',51.7),('上垫圈',51.2),('下垫圈',46.2),('螺母',43.8)]:assert max(abs(v*1000-t) for v,t in zip(actual[key],(x,y,z)))<1e-4
            stacks.append({'安装轴_mm':[x,y],'各件原点_m':actual,'螺钉头下Z_mm':51.7,'螺钉末端Z_mm':41.7,'螺母末端Z_mm':43.8,'螺钉外露_mm':2.1,'夹紧路径':'螺钉头→上垫圈0.5→铝承架2→PA12环肩2.5→下垫圈0.5→M3螺母2.4'})
        errors=[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]];clashes=interferences(d);assert not errors and not clashes,(errors,clashes)
        assert len(cast(d,'IAssemblyDoc').GetComponents(True))==21;assert len(list(all_mates(d)))==44
        save(d,dest);preview(d,'触控视觉头部_承架紧固候选');sw.CloseDoc(d.GetTitle());d=None
        reopened=sw.OpenDoc6(str(dest),2,1,'',0,0);assert reopened[1]==0;d=cast(reopened[0],'IModelDoc2');d.ForceRebuild3(False)
        cs=[cast(o,'IComponent2') for o in cast(d,'IAssemblyDoc').GetComponents(True)];assert len(cs)==21
        assert not interferences(d) and not [f for f in all_mates(d) if f.GetErrorCode2()[0]]
        # The faceplate is fitted after these screws. Check the body, display and all clamp hardware.
        modeler=cast(sw.GetModeler(),'IModeler');tool_checks=[]
        for x,y in MOUNT_HOLES:
            hits=[]
            for c in cs:
                if Path(c.GetPathName()).stem.split('_')[0] in ('H05','H07'):continue
                for b in body_list(cast(c.GetModelDoc2(),'IModelDoc2')):
                    other=cast(b.Copy(),'IBody2');assert other.ApplyTransform(c.Transform2)
                    probe=cast(modeler.CreateBodyFromCyl(mm_array([x/1000,y/1000,.0547,0,0,1,.0025,.060])),'IBody2')
                    r=probe.Operations2(C.SWBODYINTERSECT,other,0);assert r[1] in (0,5,6,1067),(c.Name2,r[1])
                    volume=sum(cast(v,'IBody2').GetMassProperties(1)[3] for v in (r[0] or []))*1e9
                    if volume>1e-5:hits.append({'零件':c.Name2,'交叠_mm3':volume})
            tool_checks.append({'螺钉轴_mm':[x,y],'D5直进工具通道干涉':hits});assert not hits,(x,y,hits)
        report={'日期':'2026-09-08','装配':str(dest),'组件数':21,'配合数':44,'重新打开验证':True,'配合错误':errors,'干涉':clashes,'四组承架夹紧':stacks,'面框未安装时的工具通道':tool_checks,'边界':['紧固件为现有GB/T对应规格的简化实体，未取得大工程师标准件模型；螺纹未建牙型','M3螺母尚未防掉落，环肩背面的扳手进入路径和预紧力尚待完善','面框、屏幕四螺柱、相机与控制板的连接未因此完成','D5x60工具杆是设计预留，不等于已选真实工具及完整手部空间','PA12环肩的螺栓预紧压溃、蠕变与热循环未验证；不可直接按钢制接头扭矩拧紧','齐平密封圈仍是装配态名义几何，未通过试样耐久验证']}
        (ROOT/'validation/头部承架紧固与工具空间检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
