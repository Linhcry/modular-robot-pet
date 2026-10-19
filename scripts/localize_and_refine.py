from build_parts import *

TRANSLATIONS={'LOAD_PLATE':'承载板外形与安装孔','DECK':'上板外形与安装孔','RAIL':'侧梁外形与贯穿孔','BULKHEAD':'隔板与髋安装孔','FLOOR':'托架底板','RIM':'托架侧围','TRAY':'托板轮廓','MOUNT_FLANGE':'定子安装法兰','ACTUATOR_ENVELOPE':'电机外形包络','JOURNAL':'输出轴包络','OUTPUT_FLANGE':'输出法兰','ORTHOGONAL_WALL':'正交安装壁','ROLL_INTERFACE':'横滚输出连接面','LINK':'连杆外形与轴孔','ADAPTER':'双孔系转接板','FOOT_ADAPTER':'足端竖板','FOOT_SOLE':'足端水平支撑','PAD':'柔性垫外形','CARGO_FLOOR':'储物舱底板','CARGO_WALL':'储物舱侧壁','LID':'舱盖轮廓','REMOVABLE_TRAY':'可拆内托盘','LEAF':'铰链安装页','KNUCKLE':'铰链轴套','PALM':'夹爪掌板','FINGER':'手指轮廓与轴孔','HEAD_BASE':'头部安装底板','HEAD_SHELL':'头部壳体','FACE':'面罩与光学开孔','LENS':'镜头包络','TAIL':'尾部轮廓','BATTERY_ENVELOPE':'电池外形包络','COMPUTE_ENVELOPE':'计算板外形包络','NOMINAL_M3_SHANK':'公称M3杆部_螺纹简化','HEAD':'螺钉头部_内六角省略','WASHER':'平垫圈','NUT':'六角螺母_螺纹简化','PIN':'铰轴杆部','PIN_HEAD':'铰轴挡肩'}
def cn_feature(name):
    if name.startswith('EDGE_C'):return name.replace('EDGE_C','非功能外缘倒角_C')
    if name.endswith('_SK'):return TRANSLATIONS.get(name[:-3],name[:-3])+'_草图'
    return TRANSLATIONS.get(name,name)

def run():
    sw=connect();catalog=json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))
    # These two refinements remove a rail overlap and give the foot a horizontal support.
    for row in catalog:
        if row['id'] not in ('F04_Bulkhead','L03_FootMount'):continue
        old=cast(sw.GetOpenDocumentByName(row['path']),'IModelDoc2')
        if old:sw.CloseDoc(old.GetTitle())
        d=newdoc(sw,'part')
        if row['id']=='F04_Bulkhead':
            profile(d,'BULKHEAD',rect(164,54,c=2),pattern(-54,0,44)+pattern(54,0,44)+[(-54,0,26),(54,0,26)],4)
            row['key_dimensions_mm']='164 x54 x4; joint centres108; 8 x diameter3.4 on44-square'
        else:
            profile(d,'FOOT_ADAPTER',rect(42,48,c=2),[(0,0,8.2)],8)
            profile(d,'FOOT_SOLE',rect(46,40,cy=-20),[(x,-20,3.4) for x in (-15,15)],8,-24,index=1)
            row['key_dimensions_mm']='vertical plate42 x48 x8; sole46 x40 x8; pivot8.2; passive ankle'
            row['notes']='Passive ankle pivot; pin retaining details and hard stops require next design iteration.'
        chamfer_top(d,.3);color(d,(.30,.42,.50));save(d,row['path'])
    for row in catalog:
        old=Path(row['path']);d=cast(sw.GetOpenDocumentByName(str(old)),'IModelDoc2')
        if d is None:d=cast(sw.OpenDoc6(str(old),1,1,'',0,0)[0],'IModelDoc2')
        for f in features(d):
            name=cn_feature(f.Name)
            if name!=f.Name:
                try:f.Name=name
                except Exception as e:print('NAME_WARN',row['id'],str(e))
        short=row['id'].split('_')[0]
        if short=='S01':short+='_'+row['id'].split('_')[1]
        path=ROOT/'parts'/f"{short}_{row['name']}.SLDPRT"
        if old!=path:
            save(d,path)
            # Safe cleanup of this script's superseded files only, after successful native SaveAs.
            if old.is_file() and old.parent.resolve()==(ROOT/'parts').resolve():old.unlink()
        row['path']=str(path)
        row['bbox_mm']=[round(v*1000,3) for v in body_list(d)[0].GetBodyBox()]
        row['features']=[{'name':f.Name,'type':f.GetTypeName2(),'error':f.GetErrorCode2()} for f in features(d) if f.GetTypeName2() in ('Extrusion','Chamfer','Fillet','ProfileFeature','Cut')]
        d.AddCustomInfo3('','零件名称',30,row['name']);d.AddCustomInfo3('','设计阶段',30,'P0结构设计；未制造释放')
        save(d,path)
        print('中文化',path.name,flush=True)
        sw.CloseDoc(d.GetTitle())
    (ROOT/'data/parts_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');run()
