from build_integrated_cargo_deck import *

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    rows={r['id']:r for r in json.loads(CAT_PATH.read_text(encoding='utf-8'))};d=newdoc(sw,'asm');checks=[]
    try:
        root=add(sw,d,ROOT/'assemblies/储物舱_导轨锁止与承载板.SLDASM','储物舱承载总成');root.ReferencedConfiguration='装入锁定'
        plan=[('B01_LowerBody','圆润机身下护壳',(0,0,-71.8)),('B04_MainBack','曲面主背盖',(0,0,-6.2)),('B05_ServiceBack','可拆曲面后背盖',(0,0,-6.2))]
        for y in (-78,78):
            plan.append(('Q10_BackStrap','连接压板_'+str(y),(-77,y,32.8)))
            for x in (-90,-64):
                tag=f'{x}_{y}'
                plan += [('S01_M3x16','护盖螺钉_'+tag,(x,y,35.3)),('S02_M3Washer','护盖上垫圈_'+tag,(x,y,34.8)),('S02_M3Washer','护盖下垫圈_'+tag,(x,y,25.3)),('S03_M3Nut','护盖螺母_'+tag,(x,y,22.9))]
        for i,(code,name,xyz) in enumerate(plan):
            c=add(sw,d,rows[code]['path'],name,xyz);mate_pose(d,root,c,xyz,IDENTITY,name)
            if i%6==0:print('BACK_COMPONENT',i+2,flush=True)
        cm=cast(d.ConfigurationManager,'IConfigurationManager')
        def fresh():return [cast(c,'IComponent2') for c in cast(d,'IAssemblyDoc').GetComponents(True)]
        def find(prefix):return next(c for c in fresh() if Path(c.GetPathName()).name.startswith(prefix))
        poses=[('常用_装入锁定','装入锁定',False,0),('常用_开盖90度','装入开盖90度',False,0),('维护_已卸两压板','装入锁定',True,0),('维护_后盖抬高5','装入锁定',True,5),('维护_后盖抬高15','装入锁定',True,15),('维护_后盖抬高40','装入锁定',True,40),('维护_后盖完全移开','装入锁定',True,120),('维护_储物舱解锁','解锁待取出',True,120),('维护_储物舱退出25','解锁退出25',True,120),('维护_储物舱退出80','解锁退出80',True,120),('维护_储物舱退出160','解锁完全取出',True,120)]
        for name,cfg,removed,lift in poses:
            if name not in d.GetConfigurationNames():cm.AddConfiguration2(name,'按先卸压板后移开后盖再滑舱的顺序检查','',0,'','',True)
            d.ShowConfiguration2(name)
            for c in fresh():
                if Path(c.GetPathName()).name.startswith(('Q10_','S01_','S02_','S03_')):
                    c.SetSuppression2(0 if removed else 2)
            find('储物舱_导轨锁止').ReferencedConfiguration=cfg
            label='可拆曲面后背盖_Z';f=next(f for f in all_mates(d) if f.Name==label);assert f.SetSuppression2(1,1,None)
            target=-6.2+lift;assert cast(d.Parameter('D1@'+label),'IDimension').SetSystemValue3(abs(target)/1000,1,None)==0
            d.ForceRebuild3(False)
            if abs(find('B05_').Transform2.ArrayData[11]*1000-target)>1e-4:
                definition=cast(f.GetDefinition(),'IDistanceMateFeatureData');definition.FlipDimension=not definition.FlipDimension;assert f.ModifyDefinition(definition,d,None);d.ForceRebuild3(False)
            actual=find('B05_').Transform2.ArrayData[11]*1000;assert abs(actual-target)<1e-4
            clashes=interferences(d)
            for cl in clashes:
                ns=' '.join(cl['components'])
                if 'Q07_' in ns and 'Q08_' in ns and abs(cl['volume_mm3']-math.pi*(9-6.25)*8)<.05:cl['classification']='M6公称杆与底孔的预期简化交叠'
            errors=[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]]
            checks.append({'配置':name,'储物子装配配置':cfg,'压板及其紧固件已拆':removed,'后盖抬高_mm':lift,'后盖实际Z_mm':actual,'干涉':clashes,'配合错误':errors})
            (ROOT/'validation/分体背盖与储物舱维护检查.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
            print('SERVICE_BACK',name,'unexpected',sum(c['classification']=='需修复的实体干涉' for c in clashes),'mateerrors',errors,flush=True)
        from repair_service_back_configs import repair
        repair(sw,d)
        d.ShowConfiguration2('常用_装入锁定');d.ForceRebuild3(False);save(d,ROOT/'assemblies/分体曲面背盖与储物舱_维护候选.SLDASM');z_up_preview(sw,d,'分体曲面背盖与储物舱_维护候选')
        assert not any(c['classification']=='需修复的实体干涉' for p in checks for c in p['干涉']), 'Unexpected clashes recorded; assembly saved for diagnosis'
    finally:sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
