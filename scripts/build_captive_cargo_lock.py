"""Native captive threaded locating pin and bridge, separate from the prior pull pin."""
from build_mechanism_parts import *
from build_body_fit_assembly import datum_mate,all_mates,interferences,z_up_preview
from sw_assembly import add,IDENTITY

HOLES=[(75,-21),(91,-21),(75,21),(91,21)]
def base(d):
    sketch(d,'销座底板圆角与四个紧固孔',lambda sm:(roundrect(sm,24,54,3,cx=83),*[sm.CreateCircleByRadius(x/1000,y/1000,0,.0017) for x,y in HOLES]))
    extrude(d,'销座底板厚3',3)
    sketch(d,'舱耳下方圆角承接台',lambda sm:roundrect(sm,18,18,3,cx=83));extrude(d,'承接台顶面16',13,3)
    sketch(d,'销尖盲孔直径4_2',lambda sm:sm.CreateCircleByRadius(.083,0,0,.0021));cut(d,'销尖承接孔深5_5',5.5,10.5)
    chamfer_top(d,.2)

def bridge(d):
    sketch(d,'桥顶圆角轮廓与M6攻丝底孔',lambda sm:(roundrect(sm,18,48,3,cx=85),sm.CreateCircleByRadius(.083,0,0,.0025)))
    extrude(d,'桥顶薄板厚3',3,40)
    sketch(d,'局部防脱与螺纹承载套',lambda sm:(sm.CreateCircleByRadius(.083,0,0,.007),sm.CreateCircleByRadius(.083,0,0,.0025)))
    extrude(d,'中心承载套连接桥顶',16,24)
    sketch(d,'防脱肩避空孔',lambda sm:sm.CreateCircleByRadius(.083,0,0,.0042));cut(d,'底开口防脱肩腔深11',11,24)
    for side in (-1,1):
        sketch(d,'桥脚安装面'+str(side),lambda sm,side=side:(roundrect(sm,24,12,2,cx=83,cy=side*21),*[sm.CreateCircleByRadius(x/1000,side*.021,0,.0017) for x in (75,91)]));extrude(d,'桥脚厚3_'+str(side),3,3,merge=False)
        sketch(d,'避开舱耳与垫圈的立柱'+str(side),lambda sm,side=side:roundrect(sm,5,8,1,cx=83.5,cy=side*20));extrude(d,'立柱连接桥脚与桥顶'+str(side),34,6)
    assert chamfer_top(d,.3)

def pin(d):
    # All pin geometry is relative to its own axis; locked assembly translation = (83,0,0).
    profile(d,'销尖直径4_轴向11至24',4,(),13,11)
    profile(d,'整体防脱肩直径8厚2',8,(),2,24)
    profile(d,'M6x1螺纹杆_公称实体',6,(),17,26)
    profile(d,'手拧帽止挡面',14,(),2,43)
    loft(d,'手拧帽圆润拱面',[(45,ellipse(14,14)),(47,ellipse(12,12)),(49,ellipse(6,6))])
    fillet_outer_end(d,49,.2)

def screw12(d):
    profile(d,'M3公称螺杆长12',3,(),12,-12)
    profile(d,'内六角圆柱头',5.5,(),3)
    pts=[(1.25/math.cos(math.pi/6)*math.cos(k*math.pi/3),1.25/math.cos(math.pi/6)*math.sin(k*math.pi/3)) for k in range(6)]
    sketch(d,'内六角对边2_5',lambda sm:polygon(sm,pts));cut(d,'内六角孔深1_5',1.5,1.5)

def set_pose(d,base,c,xyz,name,axes=(0,1,2)):
    for index,axis in ((0,2),(1,1),(2,0)):
        if axis not in axes:continue
        label=name+'_'+('XYZ'[axis]);datum_mate(d,base,c,index,xyz[axis],label);d.ForceRebuild3(False)
        if xyz[axis] and abs(c.Transform2.ArrayData[9+axis]*1000-xyz[axis])>1e-4:
            f=next(f for f in all_mates(d) if f.Name==label);df=cast(f.GetDefinition(),'IDistanceMateFeatureData');df.FlipDimension=not df.FlipDimension;assert f.ModifyDefinition(df,d,None);d.ForceRebuild3(False)

def main():
    sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    import refine_curved_parts as ref
    ref.preview=lambda *a,**k:False
    cat=json.loads(CAT_PATH.read_text(encoding='utf-8'))
    try:
        for code,name,builder,dims,mat,notes in [
            ('S01_M3x12','M3x12内六角螺钉',screw12,'M3×12；头径5.5高3；内六角2.5','钢（强度等级待选）','GB/T70.1尺寸系列简化模型；无实体牙型，非大工程师下载件。'),
            ('Q06_LockBase','防脱销承接底座',base,'底板24×54×3；承接台顶面16；D4.2盲孔底10.5','6061-T6 铝合金（设计假设）','四个M3间隙孔(75/91,±21)；与机身连接尚待总装，不替代燕尾导轨承载。'),
            ('Q07_LockBridge','防脱销圆角跨桥',bridge,'顶体X76至94；顶面43；D8.4肩腔至35；M6x1底孔D5','6061-T6 铝合金（设计假设）','销从跨桥下方装入再旋入M6孔，然后把跨桥螺接底座；禁止先装跨桥再强压防脱肩。有效螺纹8mm。'),
            ('Q08_CaptivePin','圆帽防脱螺旋定位销',pin,'销尖D4；防脱肩D8×2；M6x1公称杆；帽D14；行程9','不锈钢（设计假设）','螺纹未建牙型；旋出9圈到内部止挡。本阶段只检查轴向离散姿态，未建立连续螺旋运动副。振动防松未实测。')]:
            add_part(sw,cat,code,name,builder,dims,mat,notes)
        rows={r['id']:r for r in cat};rows['S01_M3x12']['kind']='standard_simplified';CAT_PATH.write_text(json.dumps(cat,ensure_ascii=False,indent=2),encoding='utf-8');audit=[]
        for code in ('Q06_LockBase','Q07_LockBridge','Q08_CaptivePin'):
            d=cast(sw.OpenDoc6(rows[code]['path'],1,1,'',0,0)[0],'IModelDoc2');err=[f.Name for f in features(d) if f.GetErrorCode2()[0]];bs=body_list(d)
            audit.append({'编号':code,'实体数':len(bs),'重建错误':err,'体积_mm3':sum(b.GetMassProperties(1)[3] for b in bs)*1e9});assert len(bs)==1 and not err
            sw.CloseDoc(d.GetTitle())
        d=newdoc(sw,'asm');cs={};plan=[('Q06_LockBase','防脱销承接底座',(0,0,0),IDENTITY),('Q07_LockBridge','防脱销跨桥',(0,0,0),IDENTITY),('Q08_CaptivePin','防脱螺旋销',(83,0,.001),IDENTITY),('C01_CargoShell','储物舱壳体_装入位置',(-.001,0,16.2),IDENTITY)]
        # Fastener set includes both bearing washers and the nut; x12 gives 2.6mm nominal protrusion.
        if 'S01_M3x12' not in rows:raise RuntimeError('M3x12 existing part required')
        for x,y in HOLES:
            tag=f'{x}_{y}'
            plan += [('S02_M3Washer','上垫圈_'+tag,(x,y,6),IDENTITY),('S01_M3x12','M3x12螺钉_'+tag,(x,y,6.5),IDENTITY),('S02_M3Washer','下垫圈_'+tag,(x,y,-.5),IDENTITY),('S03_M3Nut','螺母_'+tag,(x,y,-2.9),IDENTITY)]
        root=None
        for code,name,xyz,rot in plan:
            c=add(sw,d,rows[code]['path'],name,xyz,rot);cs[name]=c
            if root is None:root=c
            else:set_pose(d,root,c,xyz,name)
        checks=[]
        for lift,shift in [(0,0),(3,0),(6,0),(9,0),(9,-25),(9,-80),(9,-160)]:
            # Each editable distance mate configuration is an assembly pose, not a screw motion simulation.
            cm=cast(d.ConfigurationManager,'IConfigurationManager');name=f'销升{lift}_舱退{abs(shift)}'
            if name not in d.GetConfigurationNames():cm.AddConfiguration2(name,'防脱与退出离散姿态','',0,'','',True)
            d.ShowConfiguration2(name)
            for part,axis,value in [('防脱螺旋销','Z',lift),('储物舱壳体_装入位置','X',shift)]:
                label=part+'_'+axis;f=next(f for f in all_mates(d) if f.Name==label)
                assert f.SetSuppression2(1,1,None)
                dim=cast(d.Parameter('D1@'+label),'IDimension');assert dim.SetSystemValue3(abs(value)/1000,1,None)==0
            d.ForceRebuild3(False)
            current={Path(cast(c,'IComponent2').GetPathName()).name.split('_')[0]:cast(c,'IComponent2') for c in cast(d,'IAssemblyDoc').GetComponents(False)}
            actual_pin=[v*1000 for v in current['Q08'].Transform2.ArrayData[9:12]]
            actual_cargo=[v*1000 for v in current['C01'].Transform2.ArrayData[9:12]]
            assert max(abs(a-b) for a,b in zip(actual_pin,(83,0,lift)))<1e-4,(name,actual_pin)
            assert max(abs(a-b) for a,b in zip(actual_cargo,(shift,0,16.2)))<1e-4,(name,actual_cargo)
            clashes=interferences(d)
            for cl in clashes:
                if 'Q08_' in ' '.join(cl['components']) and 'Q07_' in ' '.join(cl['components']) and abs(cl['volume_mm3']-math.pi*(3**2-2.5**2)*8)<.05:cl['classification']='M6公称杆与D5攻丝底孔的预期简化交叠'
            checks.append({'销升_mm':lift,'舱退_mm':shift,'配置':name,'干涉':clashes,'配合错误':[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]],'实际销原点_mm':actual_pin,'实际舱原点_mm':actual_cargo})
            assert not checks[-1]['配合错误'] and not any(c['classification']=='需修复的实体干涉' for c in clashes),checks[-1]
            print('LOCK_POSE',name,checks[-1],flush=True)
        d.ShowConfiguration2('销升0_舱退0');d.ForceRebuild3(False)
        save(d,ROOT/'assemblies/储物舱防脱锁止_装入检查.SLDASM');z_up_preview(sw,d,'储物舱防脱锁止_装入检查');sw.CloseDoc(d.GetTitle())
        (ROOT/'validation/储物舱防脱锁止检查.json').write_text(json.dumps({'零件':audit,'姿态':checks,'边界':'固定基准面姿态检查；未接入导轨、全机或动态螺旋副；尚无振动防松试验'},ensure_ascii=False,indent=2),encoding='utf-8')
    finally:sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
