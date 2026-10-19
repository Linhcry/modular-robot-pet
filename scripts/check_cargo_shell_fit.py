"""Check complete cassette against both real outer shells, preserving the original shells."""
from build_integrated_cargo_deck import *

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True
    rows={r['id']:r for r in json.loads(CAT_PATH.read_text(encoding='utf-8'))};d=newdoc(sw,'asm');checks=[]
    try:
        p=ROOT/'assemblies/储物舱_导轨锁止与承载板.SLDASM'
        root=add(sw,d,p,'储物舱承载总成',(0,0,0));root.ReferencedConfiguration='装入锁定'
        for code,name,z in [('B01_LowerBody','圆润机身下护壳',-71.8),('B02_UpperBody','拱形机身背盖',-6.2)]:
            c=add(sw,d,rows[code]['path'],name,(0,0,z));mate_pose(d,root,c,(0,0,z),IDENTITY,name)
        cm=cast(d.ConfigurationManager,'IConfigurationManager')
        for cfg in ('装入锁定','装入开盖90度','解锁待取出','解锁退出25','解锁退出80','解锁完全取出'):
            name='壳体检查_'+cfg
            if name not in d.GetConfigurationNames():cm.AddConfiguration2(name,'包含真实上下护壳的空间审核','',0,'','',True)
            d.ShowConfiguration2(name)
            root=next(cast(c,'IComponent2') for c in cast(d,'IAssemblyDoc').GetComponents(True) if Path(cast(c,'IComponent2').GetPathName()).suffix.upper()=='.SLDASM')
            root.ReferencedConfiguration=cfg;d.ForceRebuild3(False)
            clashes=interferences(d)
            for cl in clashes:
                ns=' '.join(cl['components'])
                if 'Q07_' in ns and 'Q08_' in ns and abs(cl['volume_mm3']-math.pi*(9-6.25)*8)<.05:cl['classification']='M6公称杆与底孔的预期简化交叠'
            errors=[f.Name for f in all_mates(d) if f.GetErrorCode2()[0]]
            checks.append({'配置':name,'子总成配置':cfg,'配合错误':errors,'干涉':clashes})
            (ROOT/'validation/储物舱对机身护壳空间检查.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
            print('SHELL_FIT',cfg,'unexpected',len([x for x in clashes if x['classification']=='需修复的实体干涉']),flush=True)
        d.ShowConfiguration2('壳体检查_装入锁定');d.ForceRebuild3(False);save(d,ROOT/'assemblies/储物舱与机身护壳_空间检查.SLDASM');z_up_preview(sw,d,'储物舱与机身护壳_空间检查')
    finally:sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
