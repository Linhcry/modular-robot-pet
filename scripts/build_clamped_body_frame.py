"""Native clamped frame candidate, retaining the earlier space-only assembly."""
from build_body_fit_assembly import *

def run():
    sw=connect();sw.FrameState=C.swWindowMinimized;sw.Visible=True;sw.FrameState=C.swWindowMinimized
    sw.DocumentVisible(True,1);sw.DocumentVisible(True,2);sw.CommandInProgress=True
    cat={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))}
    d=newdoc(sw,'asm');records=[];components={}
    try:
        plan=[('B01_LowerBody','圆润机身下护壳',(0,0,0),IDENTITY),
              ('B02_UpperBody','拱形机身背盖',(0,0,65.6),IDENTITY),
              ('F10_LightBelly','镂空下承载板',(0,0,15.3),IDENTITY),
              ('F12_ShortSideRail','左侧承载槽梁',(0,87,17.8),IDENTITY),
              ('F12_ShortSideRail','右侧承载槽梁',(0,-87,17.8),(-1,0,0,0,-1,0,0,0,1)),
              ('F11_LightDeck','双承载带上板',(0,0,71.8),IDENTITY)]
        for x in (-100,-60,60,100):
            for y in (-88,88):
                tag=f'X{x}_Y{y}'
                plan += [('F07_CompressionSleeve','压缩隔套_'+tag,(x,y,20.3),IDENTITY),
                         ('S02_M3Washer','下侧垫圈_'+tag,(x,y,14.8),IDENTITY),
                         ('S02_M3Washer','上侧垫圈_'+tag,(x,y,73.8),IDENTITY),
                         ('S03_M3Nut','顶侧螺母_'+tag,(x,y,74.3),IDENTITY),
                         ('S01_M3x65','向上贯穿螺钉_'+tag,(x,y,14.8),(1,0,0,0,-1,0,0,0,-1))]
        base=None
        for code,name,xyz,rot in plan:
            c=add(sw,d,cat[code]['path'],name,xyz,rot);components[name]=c
            if base is None:base=c
            else:
                for index,axis in ((0,2),(1,1),(2,0)):
                    label=name+'_基准_'+('XYZ'[axis]);datum_mate(d,base,c,index,xyz[axis],label)
                    d.ForceRebuild3(False);a=list(c.Transform2.ArrayData)
                    if xyz[axis] and abs(a[9+axis]*1000-xyz[axis])>1e-4:
                        f=next(f for f in all_mates(d) if f.Name==label)
                        definition=cast(f.GetDefinition(),'IDistanceMateFeatureData');definition.FlipDimension=not definition.FlipDimension
                        assert f.ModifyDefinition(definition,d,None);d.ForceRebuild3(False)
            records.append({'编号':code,'名称':name,'目标原点_mm':xyz,'目标方向':rot})
            if len(records)%8==0:print('FRAME_COMPONENTS',len(records),flush=True)
        d.ForceRebuild3(False)
        for r in records:
            a=list(components[r['名称']].Transform2.ArrayData)
            r['实际原点_mm']=[v*1000 for v in a[9:12]]
            r['原点误差_mm']=max(abs(x-y) for x,y in zip(r['实际原点_mm'],r['目标原点_mm']))
            r['方向误差']=max(abs(x-y) for x,y in zip(a[:9],r['目标方向']))
            assert r['原点误差_mm']<1e-4 and r['方向误差']<1e-6,r
        # Confirm actual cylindrical mounting holes in each CAD component, not catalog text alone.
        axis_checks=[]
        for x in (-100,-60,60,100):
            for y in (-88,88):
                for name,local in [('镂空下承载板',(x,y,0)),('双承载带上板',(x,y,0)),('左侧承载槽梁' if y>0 else '右侧承载槽梁',(x if y>0 else -x,1,0))]:
                    cylinder_at(components[name],1.7,local,2)
                    axis_checks.append({'组件':name,'世界孔轴XY_mm':[x,y],'实际D3_4圆柱面已找到':True})
        mates=[{'名称':f.Name,'类型':f.GetTypeName2(),'错误':f.GetErrorCode2()} for f in all_mates(d)]
        clashes=interferences(d)
        audit={'阶段':'带8组贯穿螺栓和压缩隔套的机身候选；尚无髋隔板/全机载荷验证','零件实例':records,'实际孔轴核对':axis_checks,'配合':mates,'干涉':clashes,
               '名义夹紧链_mm':{'下垫圈':.5,'下板':2.5,'侧梁含上下翼缘':54,'上板':2,'上垫圈':.5,'总夹紧厚度':59.5,'螺母厚度假设':2.4,'螺钉公称长度':65,'螺钉伸出螺母':3.1,'隔套长度':49,'侧梁翼缘间净距':49},
               '注意':['所用M3x65、螺母为已有尺寸简化件；具体GB商品规格及型号库存未冻结','隔套49mm与内距49mm为名义一致；未指定配磨/长度公差，不代表已有可靠预紧力','螺钉按名义杆部建模；未模拟螺纹接触、预紧或弹性变形','全部为真实基准面配合；固定姿态不代替接触载荷和螺栓强度校核','外壳自身安装螺钉、髋隔板、关节及电子系统尚未加入']}
        target=ROOT/'validation/机身贯穿夹紧装配检查.json'
        target.write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
        assert len(records)==46 and len(mates)==135 and not any(r['错误'][0] for r in mates)
        save(d,ROOT/'assemblies/机身框架_贯穿夹紧候选.SLDASM')
        z_up_preview(sw,d,'机身框架_贯穿夹紧候选')
        print(json.dumps({'零件实例数':len(records),'真实配合数':len(mates),'配合错误数':sum(bool(r['错误'][0]) for r in mates),'干涉':clashes},ensure_ascii=False,indent=2),flush=True)
    finally:
        sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');run()
