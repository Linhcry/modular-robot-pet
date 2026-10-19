"""Cargo cassette on a supported deck; native datums and discrete service configurations."""
from build_mechanism_parts import *
from sw_assembly import *
from build_cargo_assembly import all_mates,ROT_Z_TO_X
from audit_cargo_motion import interferences,z_up_preview

LOCK_HOLES=[(x,y) for x in (75,91) for y in (-21,21)]
def supported_deck(d):
    def outline(sm):
        roundrect(sm,220,190,14)
        roundrect(sm,70,64,8,-65,0);roundrect(sm,35,64,8,47.5,0)
        roundrect(sm,40,64,8)
        for y in (-72,72):roundrect(sm,170,20,8,0,y)
        for x in (-100,-60,60,100):
            for y in (-88,88):sm.CreateCircleByRadius(x/1000,y/1000,0,.0017)
        for x in (-50,0,50):
            for y in (-45,45):sm.CreateCircleByRadius(x/1000,y/1000,0,.0017)
        for x,y in LOCK_HOLES:sm.CreateCircleByRadius(x/1000,y/1000,0,.0017)
    sketch(d,'圆角承载上板_锁座下方保留连续材料',outline);extrude(d,'上板厚2',2);chamfer_top(d,.2)

def pad(d):
    sketch(d,'导轨等高垫块圆角与贯穿孔',lambda sm:(roundrect(sm,16,14,2),sm.CreateCircleByRadius(0,0,0,.0017)))
    extrude(d,'导轨等高3',3);chamfer_top(d,.2)

def mate_pose(d,root,c,xyz,rot,name):
    # Match a component's local datum normal to each world axis, including the rotated rail.
    local_axes={0:2,1:1,2:0};labels=[]
    for world_index,axis in ((0,2),(1,1),(2,0)):
        local_index=next(i for i,a in local_axes.items() if abs(rot[3*a+axis])>.99)
        d.ClearSelection2(True)
        for n,comp,index in ((0,root,world_index),(1,c,local_index)):
            doc=cast(comp.GetModelDoc2(),'IModelDoc2');p=[f for f in features(doc) if f.GetTypeName2()=='RefPlane'][index]
            assert cast(comp.FeatureByName(p.Name),'IFeature').Select2(bool(n),1)
        off=xyz[axis];r=cast(d,'IAssemblyDoc').AddMate5(5 if off else 0,2,False,abs(off)/1000,0,0,0,0,0,0,0,False,False,0,0)
        assert r[0] and r[1]==C.swAddMateError_NoError,(name,axis,r)
        label=name+'_'+('XYZ'[axis]);name_last_mate(d,label);labels.append((label,axis));d.ClearSelection2(True)
    d.ForceRebuild3(False)
    for label,axis in labels:
        if xyz[axis] and abs(c.Transform2.ArrayData[9+axis]*1000-xyz[axis])>1e-4:
            f=next(f for f in all_mates(d) if f.Name==label);data=cast(f.GetDefinition(),'IDistanceMateFeatureData');data.FlipDimension=not data.FlipDimension;assert f.ModifyDefinition(data,d,None)
    d.ForceRebuild3(False)
    a=list(c.Transform2.ArrayData)
    assert max(abs(a[9+j]*1000-xyz[j]) for j in range(3))<1e-4,(name,'position',a)
    assert max(abs(x-y) for x,y in zip(a[:9],rot))<1e-6,(name,'rotation',a)

def main():
    sw=connect();sw.FrameState=C.swWindowMinimized;sw.Visible=True;sw.FrameState=C.swWindowMinimized
    sw.DocumentVisible(True,1);sw.DocumentVisible(True,2);sw.CommandInProgress=True
    import refine_curved_parts as ref
    ref.preview=lambda *a,**k:False
    cat=json.loads(CAT_PATH.read_text(encoding='utf-8'));d=None
    try:
        if '--assembly-only' not in sys.argv:
            add_part(sw,cat,'F13_CargoSupportedDeck','锁座连体支承上板',supported_deck,'220×190×2；右侧窗X30至65；锁座孔(75/91,±21)','6061-T6 铝合金（设计假设）','保留F11旧板；锁座四孔下方保留材料，与双导轨承载带连通。仍需与侧梁总装和承载复核。')
            add_part(sw,cat,'Q09_RailPad','燕尾导轨等高垫块',pad,'16×14×3，圆角R2，中心D3.4','6061-T6 铝合金（设计假设）','每条导轨3块，间距50；用于统一舱底与锁座高度。不是贯穿整条导轨的支承条，须校核导轨跨距。')
        rows={r['id']:r for r in cat};records=[]
        for code in ('F13_CargoSupportedDeck','Q09_RailPad'):
            row=rows[code];doc=cast(sw.OpenDoc6(row['path'],1,1,'',0,0)[0],'IModelDoc2');bs=body_list(doc);err=[f.Name for f in features(doc) if f.GetErrorCode2()[0]];assert len(bs)==1 and not err
            records.append({'编号':code,'实体数':len(bs),'重建错误':err,'体积_mm3':sum(b.GetMassProperties(1)[3] for b in bs)*1e9,'文件':row['path']});sw.CloseDoc(doc.GetTitle())
        d=newdoc(sw,'asm');plan=[('F13_CargoSupportedDeck','锁座连体支承上板',(0,0,0),IDENTITY),('Q06_LockBase','防脱销承接底座',(0,0,2),IDENTITY),('Q07_LockBridge','防脱销跨桥',(0,0,2),IDENTITY),('Q08_CaptivePin','防脱螺旋销',(83,0,2),IDENTITY)]
        cargo_path=ROOT/'assemblies/储物舱模块_四短滑靴候选.SLDASM';rows['CARGO']={'path':str(cargo_path)}
        plan.append(('CARGO','完整储物舱模块',(-.001,0,18.2),IDENTITY))
        for y in (-45,45):
            plan.append(('Q01_Rail','燕尾导轨_'+str(y),(-65,y,5),ROT_Z_TO_X))
            for x in (-50,0,50):
                tag=f'{x}_{y}'
                plan += [('Q09_RailPad','等高垫块_'+tag,(x,y,2),IDENTITY),('S01_M3x16','导轨沉孔螺钉_'+tag,(x,y,10),IDENTITY),('S02_M3Washer','导轨底垫圈_'+tag,(x,y,-.5),IDENTITY),('S03_M3Nut','导轨螺母_'+tag,(x,y,-2.9),IDENTITY)]
        for x,y in LOCK_HOLES:
            tag=f'{x}_{y}'
            plan += [('S02_M3Washer','跨桥上垫圈_'+tag,(x,y,8),IDENTITY),('S01_M3x16','跨桥贯穿螺钉_'+tag,(x,y,8.5),IDENTITY),('S02_M3Washer','跨桥底垫圈_'+tag,(x,y,-.5),IDENTITY),('S03_M3Nut','跨桥螺母_'+tag,(x,y,-2.9),IDENTITY)]
        root=None
        for i,(code,name,xyz,rot) in enumerate(plan):
            c=add(sw,d,rows[code]['path'],name,xyz,rot)
            if code=='CARGO':c.ReferencedConfiguration='舱盖闭合'
            if root is None:root=c
            else:mate_pose(d,root,c,xyz,rot,name)
            if i%8==0:print('INTEGRATED_COMPONENTS',i+1,flush=True)
        # Top-level names are re-resolved after each configuration; stale handles are not reused.
        def fresh():
            return [cast(c,'IComponent2') for c in cast(d,'IAssemblyDoc').GetComponents(True)]
        def find(code):return next(c for c in fresh() if Path(c.GetPathName()).name.startswith(code))
        checks=[];cm=cast(d.ConfigurationManager,'IConfigurationManager')
        for name,lift,shift,cfg in [('装入锁定',0,0,'舱盖闭合'),('装入开盖90度',0,0,'舱盖开启90度'),('解锁待取出',9,0,'舱盖闭合'),('解锁退出25',9,-25,'舱盖闭合'),('解锁退出80',9,-80,'舱盖闭合'),('解锁完全取出',9,-160,'舱盖闭合')]:
            if name not in d.GetConfigurationNames():cm.AddConfiguration2(name,'储物模块与导轨锁座离散姿态','',0,'','',True)
            d.ShowConfiguration2(name)
            for label,value in [('防脱螺旋销_Z',2+lift),('完整储物舱模块_X',abs(shift))]:
                f=next(f for f in all_mates(d) if f.Name==label);assert f.SetSuppression2(1,1,None);assert cast(d.Parameter('D1@'+label),'IDimension').SetSystemValue3(value/1000,1,None)==0
            find('储物舱模块_').ReferencedConfiguration=cfg;d.ForceRebuild3(False)
            actual_pin=list(find('Q08_').Transform2.ArrayData[9:12]);actual_cargo=list(find('储物舱模块_').Transform2.ArrayData[9:12])
            assert abs(actual_pin[2]*1000-(2+lift))<1e-4 and abs(actual_cargo[0]*1000-shift)<1e-4,(name,actual_pin,actual_cargo)
            clashes=interferences(d)
            for cl in clashes:
                ns=' '.join(cl['components'])
                if 'Q07_' in ns and 'Q08_' in ns and abs(cl['volume_mm3']-math.pi*(9-6.25)*8)<.05:cl['classification']='M6公称杆与底孔的预期简化交叠'
            errors=[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]]
            checks.append({'配置':name,'舱体引用配置':cfg,'销升_mm':lift,'舱退_mm':shift,'当前销原点_mm':[x*1000 for x in actual_pin],'当前舱原点_mm':[x*1000 for x in actual_cargo],'干涉':clashes,'配合错误':errors})
            (ROOT/'validation/储物舱承载对接检查.json').write_text(json.dumps({'零件':records,'姿态':checks,'顶层实例':len(fresh()),'总实例含子件':len(cast(d,'IAssemblyDoc').GetComponents(False)),'顶层配合数':len(list(all_mates(d)))},ensure_ascii=False,indent=2),encoding='utf-8')
            print('INTEGRATED_POSE',name,'clashes',len(clashes),'unexpected',sum(x['classification']=='需修复的实体干涉' for x in clashes),flush=True)
            assert not errors and not any(x['classification']=='需修复的实体干涉' for x in clashes),checks[-1]
        d.ShowConfiguration2('装入锁定');d.ForceRebuild3(False);save(d,ROOT/'assemblies/储物舱_导轨锁止与承载板.SLDASM');z_up_preview(sw,d,'储物舱_导轨锁止与承载板')
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
