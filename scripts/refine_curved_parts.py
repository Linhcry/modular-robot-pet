from build_parts import *
from sw_curves import *
from localize_and_refine import cn_feature

CAT_PATH=ROOT/'data/parts_catalog.json'
def revise(sw,catalog,code,builder,dims=None,notes=None):
    row=next(x for x in catalog if x['id']==code);path=Path(row['path'])
    old=cast(sw.GetOpenDocumentByName(str(path)),'IModelDoc2')
    if old:sw.CloseDoc(old.GetTitle())
    d=newdoc(sw,'part')
    try:
        builder(d)
    except Exception:
        save(d,ROOT/'wip'/f'{code}_待修复.SLDPRT')
        sw.CloseDoc(d.GetTitle())
        raise
    assert len(body_list(d))==1,(code,'expected one solid')
    for f in features(d):
        if f.Name!=cn_feature(f.Name):f.Name=cn_feature(f.Name)
    rgb=(.81,.87,.87) if code.startswith(('H01','C01')) else (.27,.53,.59)
    if code=='H02_Faceplate':rgb=(.08,.12,.15)
    color(d,rgb)
    if dims:row['key_dimensions_mm']=dims
    if notes:row['notes']=notes
    for k,v in {'零件编号':code,'零件名称':row['name'],'设计阶段':'P1曲面结构样机；未制造释放','材料假设':row['material_assumption'],'关键尺寸':row['key_dimensions_mm'],'设计说明':row['notes']}.items():d.AddCustomInfo3('',k,30,v)
    save(d,path)
    row['bbox_mm']=[round(v*1000,3) for v in body_list(d)[0].GetBodyBox()]
    row['features']=[{'name':f.Name,'type':f.GetTypeName2(),'error':f.GetErrorCode2()} for f in features(d) if f.GetTypeName2() not in ('RefPlane','OriginProfileFeature') and f.GetTypeName2() in ('Extrusion','Blend','Shell','Chamfer','Fillet','Cut','ProfileFeature')]
    preview(d,code+'_曲面版');sw.CloseDoc(d.GetTitle())
    CAT_PATH.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    print('曲面改版完成并关闭',row['name'],flush=True)

def curved_link(d,L):
    def draw(sm):
        arc(sm,(-20,0),(20,0),(0,20))
        arc(sm,(20,0),(14,-L*.33),(13,-L*.18))
        line(sm,(14,-L*.33),(14,-L*.67))
        arc(sm,(14,-L*.67),(20,-L),(13,-L*.82))
        arc(sm,(20,-L),(-20,-L),(0,-L-20))
        arc(sm,(-20,-L),(-14,-L*.67),(-13,-L*.82))
        line(sm,(-14,-L*.67),(-14,-L*.33))
        arc(sm,(-14,-L*.33),(-20,0),(-13,-L*.18))
        for x,y,dia in pcd(0,0)+pcd(0,-L)+[(0,0,8.2),(0,-L,8.2)]:sm.CreateCircleByRadius(x/1000,y/1000,0,dia/2000)
        sm.CreateEllipse(0,-L/2000,0,0,(-L/2+L*.23)/1000,0,.006,-L/2000,0)
    sketch(d,'圆弧收腰连杆_草图',draw);extrude(d,'承载连杆_厚5',5);chamfer_top(d,.4)

def cargo(d):
    def base(sm):
        roundrect(sm,150,120,16)
        for x,y,diam in pattern(0,0,100):sm.CreateCircleByRadius(x/1000,y/1000,0,diam/2000)
    sketch(d,'舱底_圆角轮廓',base);extrude(d,'舱底_厚3',3)
    sketch(d,'舱壁_圆弧双轮廓',lambda sm:(roundrect(sm,150,120,16),roundrect(sm,144,114,13)))
    extrude(d,'舱壁_厚3高45',45,3)
    fillet_outer_end(d,48,.6)

def lid(d):
    loft(d,'舱盖_连续拱面',[(0,lambda sm:roundrect(sm,154,124,16)),(6,lambda sm:roundrect(sm,148,118,20)),(12,lambda sm:roundrect(sm,134,104,25)),(14,lambda sm:roundrect(sm,128,98,28))])
    shell_open_end(d,0,2.5)
    for x in (-45,45):
        profile(d,'铰链局部承托'+str(x),rect(16,20,cx=x,cy=52),[(x,55,3.4)],3)
    chamfer_top(d,.3)

def head(d):
    loft(d,'头部_连续曲面',[(0,ellipse(70,60)),(12,ellipse(88,74)),(38,ellipse(82,68)),(50,ellipse(70,56))])
    shell_open_end(d,50,3)
    def holes(sm):
        for x,y,diam in pcd(0,0):sm.CreateCircleByRadius(x/1000,y/1000,0,diam/2000)
    sketch(d,'后壁安装孔_草图',holes);cut(d,'后壁四孔_贯穿',both=True)

def face(d):
    def draw(sm):
        ellipse(70,56)(sm)
        for x,y,diam in [(-17,4,18),(17,4,18),(0,-14,5)]:sm.CreateCircleByRadius(x/1000,y/1000,0,diam/2000)
    sketch(d,'椭圆面罩_光学窗口',draw);extrude(d,'面罩_厚3',3)
    fillet_outer_end(d,3,.6)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();cat=json.loads(CAT_PATH.read_text(encoding='utf-8'))
    sw.CommandInProgress=True
    try:
        revise(sw,cat,'H01_HeadShell',head,'4 sections:70x60 /88x74 /82x68 /70x56; depth50; shell3','原生放样曲面、3mm抽壳、后壁安装孔；传感器选型前保留内部空间。')
        revise(sw,cat,'H02_Faceplate',face,'ellipse70 x56; thickness3; windows2 x18; microphone5')
        revise(sw,cat,'C01_CargoShell',cargo,'150 x120 x48; corner R16; wall3; inside144 x114 R13')
        revise(sw,cat,'C02_Lid',lid,'154 x124 x14; lofted dome; shell2.5; local hinge pads3')
        for code,L in [('L01_UpperLink',145),('L02_LowerLink',145),('A01_ArmLink',120)]:revise(sw,cat,code,lambda d,L=L:curved_link(d,L),f'axis spacing{L}; end R20; waist about28; thickness5; lightening ellipse')
    finally:sw.CommandInProgress=False
