from build_cargo_assembly import *
from build_real_joint_parts import polar_holes,BACK_ANGLES,OUTPUT_ANGLES


def mate_planes(d,a,b,index,name,angle=0):
    d.ClearSelection2(True)
    for i,c in enumerate((a,b)):
        model=cast(c.GetModelDoc2(),'IModelDoc2');local=[f for f in features(model) if f.GetTypeName2()=='RefPlane'][index]
        f=cast(c.FeatureByName(local.Name),'IFeature');assert f,(c.Name2,local.Name)
        assert f.Select2(i>0,1)
    result=cast(d,'IAssemblyDoc').AddMate5(6,2,False,0,0,0,0,0,angle,angle,angle,False,False,0,0)
    d.ClearSelection2(True);assert result[0] and result[1]==C.swAddMateError_NoError,(name,result)
    name_last_mate(d,name)


def run():
    sw=connect();rows={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))}
    d=newdoc(sw,'asm');items=[]
    def put(code,label,xyz=(0,0,0),rot=IDENTITY):
        c=add(sw,d,rows[code]['path'],label,xyz,rot);items.append({'name':label,'code':code,'expected_xyz_mm':xyz,'component':c});return c
    def face(a,z,b,k,name):return mate_entities(d,flat_face(a,z),flat_face(b,k),0,name)
    def coax(a,r,pt,b,s,qt,name,locked=True):return mate_entities(d,cylinder_at(a,r,pt),cylinder_at(b,s,qt),1,name,lock_rotation=locked)
    stator=put('V01_AK4510Stator','采购电机固定部件')
    rotor=put('V02_AK4510Output','采购电机输出端')
    coax(rotor,18.5,(0,0,0),stator,26.5,(0,0,0),'电机真实输出轴线',False)
    mate_entities(d,flat_face(stator,0),flat_face(rotor,43),5,'电机输出端面位置43',distance=43)
    d.ForceRebuild3(False)
    if abs(rotor.Transform2.ArrayData[11])>.000001:
        f=next(f for f in all_mates(d) if f.Name=='电机输出端面位置43');definition=cast(f.GetDefinition(),'IDistanceMateFeatureData')
        definition.FlipDimension=not definition.FlipDimension;assert f.ModifyDefinition(definition,d,None);d.ForceRebuild3(False)
    assert abs(rotor.Transform2.ArrayData[11])<.000001
    mate_planes(d,stator,rotor,2,'关节姿态角_可调')
    back=put('J05_AK4510StatorAdapter','定子安装盘',(0,0,-3))
    coax(back,1.45,(22.5,0,0),stator,1.025,(22.5,0,0),'定子五孔接口基准_同心锁转')
    face(back,3,stator,0,'定子安装盘贴合后端盖')
    out=put('J06_AK4510OutputAdapter','输出转换盘',(0,0,43))
    coax(out,1.45,(0,-13.5,0),rotor,1.025,(0,-13.5,0),'输出三孔接口基准_同心锁转')
    face(out,0,rotor,43,'输出转换盘贴合厂家法兰')
    link=put('L01_UpperLink','大腿承载连杆',(0,0,49))
    coax(link,4.1,(0,0,0),out,4.1,(0,0,0),'连杆中心接口_同心锁转')
    face(link,0,out,6,'连杆贴合输出转换盘')
    for i,(x,y,_) in enumerate(polar_holes(22.5,BACK_ANGLES,2.9),1):
        w=put('S05_M25Washer',f'定子端M2.5垫圈{i}',(x,y,-3),ROT_Z_DOWN)
        coax(w,1.35,(0,0,0),back,1.45,(x,y,0),f'定子垫圈{i}轴线');face(w,0,back,0,f'定子垫圈{i}承压面')
        s=put('S04_M25x8',f'定子端M2.5螺钉{i}',(x,y,-3.5),ROT_Z_DOWN)
        coax(s,1.25,(0,0,0),back,1.45,(x,y,0),f'定子螺钉{i}轴线');face(s,0,w,.5,f'定子螺钉{i}头部贴合')
    for i,(x,y,_) in enumerate(polar_holes(13.5,OUTPUT_ANGLES,2.9),1):
        w=put('S06_M25SmallWasher',f'输出端M2.5小垫圈{i}',(x,y,45.8))
        coax(w,1.35,(0,0,0),out,1.45,(x,y,0),f'输出垫圈{i}轴线');face(w,0,out,2.8,f'输出垫圈{i}沉孔底贴合')
        s=put('S04_M25x8',f'输出端M2.5螺钉{i}',(x,y,46.3))
        coax(s,1.25,(0,0,0),out,1.45,(x,y,0),f'输出螺钉{i}轴线');face(s,0,w,.5,f'输出螺钉{i}头部贴合')
    for i,(x,y,_) in enumerate(polar_holes(19,(0,90,180,270),3.4),1):
        w=put('S02_M3Washer',f'连杆M3垫圈{i}',(x,y,54))
        coax(w,1.6,(0,0,0),link,1.7,(x,y,0),f'连杆垫圈{i}轴线');face(w,0,link,5,f'连杆垫圈{i}贴合')
        s=put('S01_M3x10',f'连杆M3螺钉{i}',(x,y,54.5))
        coax(s,1.5,(0,0,0),link,1.7,(x,y,0),f'连杆螺钉{i}轴线');face(s,0,w,.5,f'连杆螺钉{i}头部贴合')
    d.ForceRebuild3(False);records=[]
    for item in items:
        c=item.pop('component');actual=[v*1000 for v in c.Transform2.ArrayData[9:12]]
        item.update(actual_xyz_mm=actual,max_origin_error_mm=max(abs(v-w) for v,w in zip(actual,item['expected_xyz_mm'])),fixed=bool(c.IsFixed()));records.append(item)
    data={'assembly':'AK45-10大腿关节模块','components':records,'mates':[{'name':f.Name,'type':f.GetTypeName2(),'error':f.GetErrorCode2()} for f in all_mates(d)],'采购计数':'V01+V02合计一台AK45-10 KV75，非两台电机','边界':'安装与运动结构样机；不代表强度、温升或整机爬楼已验证'}
    path=ROOT/'assemblies/AK45-10大腿关节模块.SLDASM';save(d,path);preview(d,'AK45-10大腿关节模块')
    (ROOT/'validation/AK45-10关节装配审计.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    assert max(r['max_origin_error_mm'] for r in records)<.001
    assert not [f for f in data['mates'] if f['error'][0]!=0]
    print('关节装配完成',len(records),'实例',len(data['mates']),'配合',flush=True);sw.CloseDoc(d.GetTitle())


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.CommandInProgress=True
    try:run()
    finally:sw.CommandInProgress=False
