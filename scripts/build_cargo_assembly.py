from sw_assembly import *

ROT_Z_TO_X=(0,1,0,0,0,1,1,0,0)
ROT_Z_TO_Y=(1,0,0,0,0,-1,0,1,0)
ROT_Z_DOWN=(1,0,0,0,-1,0,0,0,-1)

def all_mates(d):
    for group in features(d):
        if group.GetTypeName2()!='MateGroup':continue
        f=group.GetFirstSubFeature()
        while f:
            f=cast(f,'IFeature');yield f;f=f.GetNextSubFeature()

def run(short=False):
    sw=connect();cat=json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'));rows={x['id']:x for x in cat}
    d=newdoc(sw,'asm');items=[]
    def put(code,name,xyz=(0,0,0),rot=IDENTITY):
        c=add(sw,d,rows[code]['path'],name,xyz,rot);items.append({'name':name,'code':code,'component':c,'expected_xyz_mm':xyz});return c
    def coinc(c,z,b,w,name,axis=2,baxis=2):return mate_entities(d,flat_face(c,z,axis),flat_face(b,w,baxis),0,name)
    def coax(c,r,p,a,b,s,q,k,name,locked=True):return mate_entities(d,cylinder_at(c,r,p,a),cylinder_at(b,s,q,k),1,name,lock_rotation=locked)
    def washer(name,xyz,rot,b,point,axis,planevalue,planeaxis=2):
        c=put('S02_M3Washer',name,xyz,rot)
        coax(c,1.6,(0,0,0),2,b,1.7,point,axis,name+'_轴线')
        coinc(c,0,b,planevalue,name+'_贴合',baxis=planeaxis)
        return c
    def screw(name,xyz,rot,b,hole,holeaxis,contact,contactplane,contactaxis=2,length=8,holer=1.7):
        c=put('S01_M3x'+str(length),name,xyz,rot)
        coax(c,1.5,(0,0,0),2,b,holer,hole,holeaxis,name+'_轴线')
        coinc(c,0,contact,contactplane,name+'_头部承压面',baxis=contactaxis)
        return c
    shell=put('C01_CargoShell','储物舱壳体')
    for side in (-1,1):
        if short:
            for x in (-40,40):
                shoe=put('Q05_ShortShoe',f'分体燕尾滑靴_{side}_{x}',(x-12,side*45,-13.2),ROT_Z_TO_X)
                coinc(shoe,13.2,shell,0,f'短滑靴贴合舱底_{side}_{x}',axis=1)
                coax(shoe,1.25,(0,0,12),1,shell,1.7,(x,side*45,0),2,f'短滑靴安装孔_{side}_{x}')
        else:
            shoe=put('Q02_Shoe',('左' if side==1 else '右')+'燕尾滑靴',(-65,side*45,-15),ROT_Z_TO_X)
            coinc(shoe,15,shell,0,'滑靴贴合舱底_'+str(side),axis=1)
            coax(shoe,1.25,(0,0,25),1,shell,1.7,(-40,side*45,0),2,'滑靴安装孔_'+str(side))
        for x in (-40,40):
            w=washer(f'舱底垫圈_{side}_{x}',(x,side*45,3),IDENTITY,shell,(x,side*45,0),2,3)
            screw(f'滑靴紧固螺钉_{side}_{x}',(x,side*45,3.5),IDENTITY,shell,(x,side*45,0),2,w,.5)
    fixed=[]
    for x in (-45,45):
        h=put('C04_HingeLeaf',f'固定铰链页_{x}',(x,60,45));fixed.append(h)
        coinc(h,0,shell,60,f'铰链固定页面贴合_{x}',axis=1,baxis=1)
        coax(h,1.7,(-10,0,-10),1,shell,1.7,(x-10,0,35),1,f'铰链固定孔_{x}')
        for hx in (-10,10):
            w=washer(f'固定铰链外垫圈_{x}_{hx}',(x+hx,63,35),ROT_Z_TO_Y,h,(hx,0,-10),1,3,1)
            screw(f'固定铰链螺钉_{x}_{hx}',(x+hx,63.5,35),ROT_Z_TO_Y,h,(hx,0,-10),1,w,.5,length=10)
            nw=put('S02_M3Washer',f'固定铰链内垫圈_{x}_{hx}',(x+hx,56.5,35),ROT_Z_TO_Y)
            coax(nw,1.6,(0,0,0),2,h,1.7,(hx,0,-10),1,f'内垫圈轴线_{x}_{hx}')
            coinc(nw,.5,shell,57,f'内垫圈贴合_{x}_{hx}',baxis=1)
            nut=put('S03_M3Nut',f'固定铰链螺母_{x}_{hx}',(x+hx,54.1,35),ROT_Z_TO_Y)
            coax(nut,1.5,(0,0,0),2,h,1.7,(hx,0,-10),1,f'铰链螺母轴线_{x}_{hx}')
            coinc(nut,2.4,nw,0,f'铰链螺母承压面_{x}_{hx}')
    moving=put('C05_MovingHinge','左活动铰链页',(-45,60,45))
    coax(moving,2.1,(0,5,0),0,fixed[0],2.1,(0,5,0),0,'舱盖转轴同心',locked=False)
    mate_entities(d,flat_face(moving,5.5,0),flat_face(fixed[0],6,0),5,'铰链单侧轴向间隙0_5',distance=.5)
    lid=put('C02_Lid','储物舱拱面舱盖',(0,0,51))
    coinc(lid,0,moving,6,'舱盖与左活动页贴合')
    coax(lid,1.25,(-45,53,0),2,moving,1.7,(0,-7,0),2,'左活动页安装孔')
    moving2=put('C05_MovingHinge','右活动铰链页',(45,60,45))
    coinc(moving2,6,lid,0,'右活动页与舱盖贴合')
    coax(moving2,1.7,(0,-7,0),2,lid,1.25,(45,53,0),2,'右活动页安装孔')
    for x,h in [(-45,moving),(45,moving2)]:
        for y in (45,53):
            w=put('S02_M3Washer',f'活动页垫圈_{x}_{y}',(x,y,48),ROT_Z_DOWN)
            coax(w,1.6,(0,0,0),2,h,1.7,(0,y-60,0),2,f'活动页垫圈轴线_{x}_{y}')
            coinc(w,0,h,3,f'活动页垫圈贴合_{x}_{y}')
            screw(f'活动页螺钉_{x}_{y}',(x,y,47.5),ROT_Z_DOWN,h,(0,y-60,0),2,w,.5)
    for x,h in zip((-45,45),fixed):
        pin=put('C06_HingePin',f'铰链肩销_{x}',(x-20,65,45),ROT_Z_TO_X)
        coax(pin,2,(0,0,0),2,h,2.1,(0,5,0),0,f'铰链肩销同心_{x}')
        coinc(pin,2,h,-18,f'铰链销头止挡_{x}',baxis=0)
        w=put('S02_M3Washer',f'铰链销端垫圈_{x}',(x+18.5,65,45),ROT_Z_TO_X)
        coax(w,1.6,(0,0,0),2,pin,1.5,(0,0,0),2,f'铰链销端垫圈轴线_{x}')
        coinc(w,0,pin,38.5,f'铰链销端垫圈压肩_{x}')
        n=put('S03_M3Nut',f'铰链销端螺母_{x}',(x+19,65,45),ROT_Z_TO_X)
        coax(n,1.5,(0,0,0),2,pin,1.5,(0,0,0),2,f'销端螺母轴线_{x}')
        coinc(n,0,w,.5,f'销端螺母贴合_{x}')
    tray=put('C03_Tray','可取出储物舱内托盘',(0,0,7))
    # Tray is removable and rests on four pads; lock records its installed pose only.
    lock(d,shell,tray,'内托盘放置姿态_可抑制')
    mate_entities(d,flat_face(lid,0),flat_face(shell,0),6,'舱盖姿态角_可调',angle=0)
    d.ForceRebuild3(False)
    audit=[]
    for item in items:
        c=item.pop('component');arr=list(c.Transform2.ArrayData);actual=[v*1000 for v in arr[9:12]]
        item.update(actual_xyz_mm=actual,max_origin_error_mm=max(abs(a-b) for a,b in zip(actual,item['expected_xyz_mm'])),fixed=bool(c.IsFixed()))
        audit.append(item)
    assembly_name='储物舱模块_四短滑靴候选' if short else '储物舱模块'
    data={'assembly':assembly_name,'components':audit,'mates':[{'name':f.Name,'type':f.GetTypeName2(),'error':f.GetErrorCode2()} for f in all_mates(d)]}
    out=ROOT/'assemblies'/f'{assembly_name}.SLDASM';save(d,out);preview(d,assembly_name)
    audit_name='短滑靴储物舱装配审计.json' if short else '储物舱装配审计.json'
    (ROOT/'validation'/audit_name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print('ASSEMBLY_SAVED',len(audit),'mates',len(data['mates']),'max_origin_error',max(i['max_origin_error_mm'] for i in audit),flush=True)
    sw.CloseDoc(d.GetTitle())
    return data

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.CommandInProgress=True
    if '--background' in sys.argv:sw.FrameState=C.swWindowMinimized
    try:run(short='--short' in sys.argv)
    finally:sw.CommandInProgress=False
