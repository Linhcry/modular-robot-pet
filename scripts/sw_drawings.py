from sw_core import *
import textwrap

def print_pdf(d,path):
    """Use the explicit local PDF printer; the SaveAs PDF converter omits sheet annotations here."""
    path=Path(path);path.parent.mkdir(exist_ok=True,parents=True)
    ext=cast(d.Extension,'IModelDocExtension');dr=cast(d,'IDrawingDoc');sheet=cast(dr.GetCurrentSheet(),'ISheet')
    setup=cast(sheet.PageSetup,'IPageSetup');setup.PrinterPaperSize=8;setup.Orientation=2;setup.ScaleToFit=True;setup.HighQuality=True
    spec=cast(ext.GetPrintSpecification(),'IPrintSpecification');spec.PrinterQueue='Microsoft Print to PDF';spec.PrintFile=str(path);spec.PrintToFile=True
    spec.NumberOfCopies=1;spec.ConvertToHighQuality=True;spec.ResetPrintRange();spec.AddPrintRange(1,len(dr.GetSheetNames()));spec.PrintBackground=False
    ext.PrintOut4('Microsoft Print to PDF',str(path),spec)
    assert path.exists() and path.stat().st_size>1000,('PDF print failed',path)
    import pymupdf
    f=pymupdf.open(path);assert len(f)==len(dr.GetSheetNames())
    assert '模块化机械宠物' in f[0].get_text(),'PDF sheet annotation missing'
    return path

def material_text(value):
    if '6061' in value and 'PA12' in value:return value+'（设计假设）'
    if '6061' in value:return '6061-T6 铝合金（设计假设）'
    if 'PA12' in value:return 'PA12 尼龙（设计假设）'
    if 'TPU' in value:return 'TPU 弹性体（设计假设）'
    if 'Steel' in value:return '钢（强度等级待选）'
    return value


def circle_edge(model,center,radius):
    matches=[]
    for body in body_list(model):
        for edge in body.GetEdges():
            edge=cast(edge,'IEdge');curve=cast(edge.GetCurve(),'ICurve')
            if curve.IsCircle():
                cp=curve.CircleParams
                if abs(cp[6]*1000-radius)<.002 and sum((cp[i]*1000-center[i])**2 for i in range(3))<.00001:matches.append(edge)
    assert matches,('circle edge missing',center,radius)
    return matches[0]


def linked_dimension(d,view,entities,kind,position,expected,label):
    d.ClearSelection2(True)
    for i,e in enumerate(entities):assert view.SelectEntity(cast(e,'IEntity'),i>0),(label,'selection failed')
    method={'horizontal':d.AddHorizontalDimension2,'vertical':d.AddVerticalDimension2,'diameter':d.AddDiameterDimension2}[kind]
    obj=method(position[0]/1000,position[1]/1000,0)
    assert obj,(label,'dimension creation failed')
    dd=cast(obj,'IDisplayDimension');dim=cast(dd.GetDimension2(0),'IDimension');value=dim.SystemValue*1000
    assert abs(value-expected)<.002,(label,'unexpected dimension',value,expected)
    ann=cast(dd.GetAnnotation(),'IAnnotation');fmt=cast(ann.GetTextFormat(0),'ITextFormat');fmt.CharHeight=.003;ann.SetTextFormat(0,False,fmt)
    d.ClearSelection2(True)
    return {'名称':label,'模型关联值_mm':round(value,5)}


def cargo_dimensions(d,views,model,code):
    result=[]
    def centers(view,a,b,r,kind,pos,value,label):
        result.append(linked_dimension(d,views[view],[circle_edge(model,a,r),circle_edge(model,b,r)],kind,pos,value,label))
    def dia(view,a,r,pos,label):
        result.append(linked_dimension(d,views[view],[circle_edge(model,a,r)],'diameter',pos,2*r,label))
    if code=='C01':
        centers(0,(-40,-45,3),(40,-45,3),1.7,'horizontal',(105,128),80,'滑靴孔横距')
        centers(0,(-40,-45,3),(-40,45,3),1.7,'vertical',(18,195),90,'滑靴孔纵距')
        dia(0,(83,0,3),2.1,(192,158),'定位销孔径')
        centers(1,(-55,60,35),(-35,60,35),1.7,'horizontal',(60,70),20,'单组铰链孔距')
    elif code=='C02':
        # These bore edges are on the underside, so add a dedicated bottom view for mounting dimensions.
        centers(4,(-45,45,0),(45,45,0),1.25,'horizontal',(325,179),90,'铰链安装横距')
        centers(4,(45,45,0),(45,53,0),1.25,'vertical',(390,246),8,'单侧螺纹孔距')
    elif code=='C03':
        for axis,horizontal,pos,value in [(0,True,(105,120),136),(1,False,(25,185),106),(2,False,(88,95),2)]:
            v=dim_extents(d,views[0 if axis<2 else 1],model,axis,horizontal,pos)
            assert v is not None and abs(v*1000-value)<.002,('tray dimension',v,value)
            result.append({'名称':['托盘长度','托盘宽度','托盘厚度'][axis],'模型关联值_mm':value})
    elif code=='C04':
        centers(1,(-10,0,-10),(10,0,-10),1.7,'horizontal',(105,90),20,'安装孔距')
        dia(1,(-10,0,-10),1.7,(53,157),'安装通孔直径')
        dia(2,(-18,5,0),2.1,(267,232),'铰轴孔径')
        value=dim_extents(d,views[0],model,0,True,(105,237));assert abs(value*1000-36)<.002
        result.append({'名称':'固定页总宽','模型关联值_mm':36})
    elif code=='C05':
        centers(0,(0,-7,6),(0,-15,6),1.7,'vertical',(82,203),8,'安装孔距')
        dia(0,(0,-15,6),1.7,(144,187),'安装通孔直径')
        dia(2,(-5.5,5,0),2.1,(272,236),'铰轴孔径')
        value=dim_extents(d,views[0],model,0,True,(105,254));assert abs(value*1000-11)<.002
        result.append({'名称':'活动页宽度','模型关联值_mm':11})
    elif code=='C06':
        # Two circular shoulders project to straight transverse lines in the side view.
        result.append(linked_dimension(d,views[2],[circle_edge(model,(0,0,0),3.5),circle_edge(model,(0,0,43.5),1.5)],'horizontal',(220,246),43.5,'肩销总长'))
        centers(2,(0,0,2),(0,0,38.5),2,'horizontal',(220,210),36.5,'光轴有效长度')
        dia(0,(0,0,2),2,(149,244),'光轴直径')
        dia(0,(0,0,0),3.5,(63,217),'销头直径')
    elif code=='Q02':
        centers(1,(0,15,25),(0,15,105),1.25,'vertical',(83,145),80,'舱底连接孔距')
        value=dim_extents(d,views[4],model,0,True,(325,194));assert abs(value*1000-22)<.002
        result.append({'名称':'滑靴截面外宽','模型关联值_mm':22})
    return result


def joint_dimensions(d,views,model,code):
    result=[]
    def span(a,b,r,kind,pos,expected,label,view=0):result.append(linked_dimension(d,views[view],[circle_edge(model,a,r),circle_edge(model,b,r)],kind,pos,expected,label))
    def dia(p,r,place,label):result.append(linked_dimension(d,views[0],[circle_edge(model,p,r)],'diameter',place,2*r,label))
    if code=='J05':
        span((-25,-25,0),(25,-25,0),1.7,'horizontal',(105,124),50,'框架孔横距')
        span((-25,-25,0),(-25,25,0),1.7,'vertical',(53,180),50,'框架孔纵距')
        dia((22.5,0,0),1.45,(183,205),'电机安装通孔')
        value=dim_extents(d,views[0],model,0,True,(105,241));assert abs(value*1000-64)<.002
        result.append({'名称':'安装盘外宽','模型关联值_mm':64})
    elif code=='J06':
        dia((0,0,0),24,(169,223),'输出盘外径')
        dia((0,-13.5,2.8),2.6,(172,161),'安装螺钉沉孔直径')
        span((-19,0,0),(19,0,0),1.25,'horizontal',(105,133),38,'M3连接孔分度圆直径')
    elif code in ('L01','L02','A01'):
        span((-19,0,0),(19,0,0),1.7,'horizontal',(105,251),38,'端部孔圆直径')
        dia((19,0,0),1.7,(153,234),'连杆连接通孔')
        dia((0,0,0),4.1,(161,218),'连杆中心孔')
    return result

def lightweight_dimensions(d,views,model,code):
    result=[]
    def extent(view,axis,horizontal,pos,value,label):
        actual=dim_extents(d,views[view],model,axis,horizontal,pos)
        assert actual is not None and abs(actual*1000-value)<.002,(label,actual,value)
        result.append({'名称':label,'模型关联值_mm':value})
    if code in ('F10','F11','F13'):
        extent(0,0,True,(105,133 if code=='F10' else 112),320 if code=='F10' else 220,'板件总长')
        extent(0,1,False,(22,185),190,'板件总宽')
        extent(1,2,False,(185,100),2.5 if code=='F10' else 2,'板厚')
        x=142 if code=='F10' else 100
        result.append(linked_dimension(d,views[0],[circle_edge(model,(-x,-88,0),1.7),circle_edge(model,(x,-88,0),1.7)],'horizontal',(105,121),2*x,'两端侧梁孔距'))
        result.append(linked_dimension(d,views[0],[circle_edge(model,(x,88,0),1.7)],'diameter',(189,226),3.4,'侧梁安装通孔'))
        if code=='F13':
            result.append(linked_dimension(d,views[0],[circle_edge(model,(75,-21,0),1.7),circle_edge(model,(91,-21,0),1.7)],'horizontal',(151,161),16,'锁座安装孔横距'))
            result.append(linked_dimension(d,views[0],[circle_edge(model,(91,-21,0),1.7),circle_edge(model,(91,21,0),1.7)],'vertical',(180,185),42,'锁座安装孔纵距'))
    elif code in ('Q09','Q10'):
        extent(0,0,True,(105,158),16 if code=='Q09' else 44,'垫块长度' if code=='Q09' else '压板长度')
        extent(0,1,False,(75 if code=='Q09' else 60,185),14,'板宽')
        extent(1,2,False,(145,100),3 if code=='Q09' else 2,'板厚')
        result.append(linked_dimension(d,views[0],[circle_edge(model,(0 if code=='Q09' else 13,0,0),1.7)],'diameter',(142,213),3.4,'贯穿通孔'))
        if code=='Q10':result.append(linked_dimension(d,views[0],[circle_edge(model,(-13,0,0),1.7),circle_edge(model,(13,0,0),1.7)],'horizontal',(105,150),26,'压板孔距'))
    elif code=='Q05':
        extent(0,0,True,(105,181),22,'滑靴截面宽度')
        extent(0,1,False,(50,215),10.9,'滑靴截面总高')
        extent(1,2,False,(50,115),24,'短滑靴总长')
        result.append(linked_dimension(d,views[1],[circle_edge(model,(0,13.2,12),1.25)],'diameter',(165,165),2.5,'M3攻丝底孔直径'))
    return result

def note(d,text,x,y,height=3.2):
    d.ClearSelection2(True)
    n=cast(d.InsertNote(text),'INote');assert n
    n.SetHeight(height/1000)
    a=cast(n.GetAnnotation(),'IAnnotation');a.SetPosition2(x/1000,y/1000,0)
    fmt=cast(a.GetTextFormat(0),'ITextFormat');fmt.TypeFaceName='Microsoft YaHei';fmt.CharHeight=height/1000
    a.SetTextFormat(0,False,fmt)
    return n

def dim_extents(d,view,model,axis,horizontal,pos):
    verts=[]
    for b in body_list(model):
        for edge in b.GetEdges():
            e=cast(edge,'IEdge')
            for v in (e.GetStartVertex(),e.GetEndVertex()):
                if v:
                    v=cast(v,'IVertex');verts.append((v,list(v.GetPoint())))
    if not verts:return None
    # Select actual model vertices in the drawing view, then insert associative dimensions.
    lo=min(v[1][axis] for v in verts);hi=max(v[1][axis] for v in verts)
    a=min((v for v in verts if abs(v[1][axis]-lo)<1e-7),key=lambda v:abs(v[1][2]))
    b=min((v for v in verts if abs(v[1][axis]-hi)<1e-7),key=lambda v:abs(v[1][2]))
    if hi-lo<1e-6:return None
    d.ClearSelection2(True)
    ra=view.SelectEntity(cast(a[0],'IEntity'),False);rb=view.SelectEntity(cast(b[0],'IEntity'),True)
    if not ra or not rb:return None
    obj=(d.AddHorizontalDimension2 if horizontal else d.AddVerticalDimension2)(pos[0]/1000,pos[1]/1000,0)
    d.ClearSelection2(True)
    if obj:
        dd=cast(obj,'IDisplayDimension');ann=cast(dd.GetAnnotation(),'IAnnotation')
        fmt=cast(ann.GetTextFormat(0),'ITextFormat');fmt.CharHeight=.003;ann.SetTextFormat(0,False,fmt)
        return cast(dd.GetDimension2(0),'IDimension').SystemValue
    return None

def make(sw,row,export_pdf=False):
    require_memory('单张工程图:'+row['id'])
    path=Path(row['path'])
    model=cast(sw.GetOpenDocumentByName(str(path)),'IModelDoc2')
    is_assembly=path.suffix.upper()=='.SLDASM'
    if model is None:model=cast(sw.OpenDoc6(str(path),2 if is_assembly else 1,1,'',0,0)[0],'IModelDoc2')
    d=newdoc(sw,'drawing');dr=cast(d,'IDrawingDoc');sheet=cast(dr.GetCurrentSheet(),'ISheet')
    assert dr.SetupSheet6(sheet.GetName(),8,13,1,1,True,'',.420,.297,'',True,.010,.010,.010,.010,0,0)
    dr.EditTemplate()
    def ln(a,b):d.CreateLine2(a[0]/1000,a[1]/1000,0,b[0]/1000,b[1]/1000,0)
    for a,b in [((10,10),(410,10)),((410,10),(410,287)),((410,287),(10,287)),((10,287),(10,10)),((255,10),(255,48)),((255,48),(410,48)),((255,33),(410,33)),((255,22),(410,22)),((330,10),(330,33))]:ln(a,b)
    note(d,'结构设计 / 未制造释放',260,44,3)
    note(d,row['name'],260,30,3)
    note(d,'图号 '+row['id'].split('_')[0],260,19,2.6)
    note(d,'版本 P1  |  单位 mm',335,19,2.6)
    dr.EditSheet()
    bbox=row['bbox_mm'];w=bbox[3]-bbox[0];h=bbox[4]-bbox[1];depth=bbox[5]-bbox[2]
    code=row['id'].split('_')[0]
    scale=row.get('drawing_scale',{'C01':1.,'C02':1.,'C03':1.,'C04':2.,'C05':2.,'C06':2.,'Q02':.5,'ASM':.75}.get(code,min(1.5,145/max(w,1),118/max(h,1),80/max(depth,1))))
    # Clean A3 first-angle sheet: conventional frame from the GB template, manually placed views.
    sheet.SetScale(scale,1,False,False)
    views=[]
    front_y,top_y={'C01':(195,100),'C02':(185,95),'C03':(185,95),'C04':(210,120),'C05':(210,120),'C06':(230,130),'Q02':(240,145),'Q05':(215,115)}.get(code,(185,100))
    iso_scale=row.get('drawing_iso_scale',min(scale,.65))
    for vname,name,x,y in [('*前视','主视图',105,front_y),('*上视','俯视图',105,top_y),('*左视','左视图',220,front_y),('*等轴测','等轴测图',335,125 if code in ('C02','Q02') else 150)]:
        v=cast(dr.CreateDrawViewFromModelView3(str(path),vname,x/1000,y/1000,0),'IView');assert v,(row['id'],vname)
        v.SetName2(name);v.ScaleDecimal=scale if name!='等轴测图' else iso_scale
        if row.get('front_configuration') and name=='主视图':v.ReferencedConfiguration=row['front_configuration']
        views.append(v)
    if code in ('C02','Q02'):
        v=cast(dr.CreateDrawViewFromModelView3(str(path),'*后视' if code=='C02' else '*前视',.325,.221 if code=='C02' else .230,0),'IView');assert v
        v.SetName2('底面安装视图' if code=='C02' else '截面端视放大图');v.ScaleDecimal=.6 if code=='C02' else 4.;views.append(v)
    d.ForceRebuild3(False)
    dims=[];interface_dims=[]
    if code=='Q06':
        interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(75,-21,0),1.7),circle_edge(model,(91,-21,0),1.7)],'horizontal',(105,138),16,'底座孔距X'))
        interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(75,-21,0),1.7),circle_edge(model,(75,21,0),1.7)],'vertical',(70,185),42,'底座孔距Y'))
        interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(91,21,0),1.7)],'diameter',(143,225),3.4,'底座安装孔'))
    if code=='Q07':
        interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(83,0,35),2.5)],'diameter',(140,215),5,'M6攻丝底孔'))
        note(d,'中心孔后加工 M6x1；有效螺纹长度8',65,245,2.8)
    if code=='Q08':
        views[0].ScaleDecimal=3.;d.ForceRebuild3(False)
        interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(0,0,24),4)],'diameter',(145,215),8,'整体防脱肩直径'))
        interface_dims.append(linked_dimension(d,views[2],[circle_edge(model,(0,0,11),2),circle_edge(model,(0,0,24),2)],'horizontal',(220,225),13,'销尖光轴长度'))
        note(d,'主视图局部放大3:1；螺纹 M6x1',65,245,2.8)
    if code=='F07':
        views[0].ScaleDecimal=5.
        d.ForceRebuild3(False)
        interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(0,0,0),3)],'diameter',(140,208),6,'隔套外径'))
        interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(0,0,0),1.7)],'diameter',(140,165),3.4,'隔套通孔'))
        interface_dims.append(linked_dimension(d,views[2],[circle_edge(model,(0,0,0),3),circle_edge(model,(0,0,49),3)],'horizontal',(220,210),49,'隔套名义长度'))
        note(d,'主视图局部放大 5:1',65,245,2.8)
    if not is_assembly and code in ('C01','C02','C03','C04','C05','C06','Q02'):interface_dims=cargo_dimensions(d,views,model,code)
    if not is_assembly and code in ('J05','J06','L01','L02','A01'):interface_dims=joint_dimensions(d,views,model,code)
    if not is_assembly and code in ('F10','F11','F13','Q05','Q09','Q10'):interface_dims=lightweight_dimensions(d,views,model,code)
    if code in ('B04','B05'):
        x=-64 if code=='B04' else -90
        interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(x,-78,32),1.7),circle_edge(model,(x,78,32),1.7)],'vertical',(26,185),156,'压板安装孔纵距'))
        interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(x,78,32),1.7)],'diameter',(176,240),3.4,'背盖连接通孔'))
    if code=='H07':
        for axis,pos,expected in [(0,(105,151),76.3),(1,(62,185),57.9)]:
            v=dim_extents(d,views[0],model,axis,axis==0,pos);assert abs(v*1000-expected)<.002
            interface_dims.append({'名称':'承边外形'+('宽' if axis==0 else '高'),'模型关联值_mm':expected})
        note(d,'装配态尺寸；自由态收缩与压缩量待试样',56,236,2.8)
    if code=='H11':
        for axis,pos,val in [(0,(105,138),16),(1,(48,185),16)]:
            actual=dim_extents(d,views[0],model,axis,axis==0,pos)
            assert abs(actual*1000-val)<.002
            interface_dims.append({'名称':'底板外形'+str(axis),'模型关联值_mm':val})
        interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(0,0,8),4.2)],'diameter',(105,242),8.4,'杯外径'))
        interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(0,0,0),1.9)],'diameter',(156,212),3.8,'螺杆避空孔'))
        interface_dims.append(linked_dimension(d,views[2],[circle_edge(model,(0,0,0),1.9),circle_edge(model,(0,0,8),4.2)],'horizontal',(220,222),8,'杯总高'))
        note(d,'六角槽 AF5.7 深2.4；四柱止挡顶Z4.5',58,251,2.8)
    if code=='H13':
        for a,b,r,kind,pos,val,label in [((-10.5,-12.4,2.6373),(10.5,-12.4,2.6373),1.1,'horizontal',(105,143),21,'相机安装孔横距'),((-10.5,-12.4,2.6373),(-10.5,.1,2.6373),1.1,'vertical',(30,185),12.5,'相机安装孔纵距'),((-20,-5,0),(20,-5,0),1.7,'horizontal',(105,225),40,'安装耳孔距')]:
            interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,a,r),circle_edge(model,b,r)],kind,pos,val,label))
        interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(10.5,.1,2.6373),1.1)],'diameter',(170,214),2.2,'相机通孔'))
        interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(20,-5,0),1.7)],'diameter',(174,172),3.4,'安装耳通孔'))
        note(d,'支承高度依据官方STEP；实际PCB叠层待复核',43,247,2.8)
    if code in ('H04','H05','H06','H10','H12'):
        def head_span(a,b,r,kind,pos,val,label):interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,a,r),circle_edge(model,b,r)],kind,pos,val,label))
        if code in ('H04','H10'):
            head_span((-39,-28,46.7),(39,-28,46.7),1.7,'horizontal',(105,137),78,'承架安装孔横距')
            head_span((-39,-28,46.7),(-39,28,46.7),1.7,'vertical',(48,185),56,'承架安装孔纵距')
            interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(0,0,2.5),9)],'diameter',(162,229),18,'颈部穿线通孔'))
        elif code=='H05':
            head_span((-47,-20,0),(47,-20,0),1.45,'horizontal',(105,138),94,'面框孔横距')
            head_span((-47,-20,0),(-47,20,0),1.45,'vertical',(42,185),40,'面框孔纵距')
            interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(0,30,0),8)],'diameter',(163,235),16,'镜头预留孔'))
        else:
            head_span((-29.35,-32.45,0),(30.12,-32.45,0),1.45,'horizontal',(105,143),59.47,'厂家屏幕孔横距')
            head_span((-29.35,-32.45,0),(-29.35,8.45,0),1.45,'vertical',(58,185),40.9,'厂家屏幕孔纵距')
            head_span((-39,28,0),(39,28,0),1.7,'horizontal',(105,231),78,'承架安装孔横距')
            interface_dims.append(linked_dimension(d,views[0],[circle_edge(model,(30.12,8.45,0),1.45)],'diameter',(172,205),2.9,'屏幕螺柱连接通孔'))
            if code=='H12':head_span((-20,25,0),(20,25,0),1.7,'horizontal',(105,243),40,'可换相机托架孔距')
    # Vertex extrema are unsuitable for rounded ends; only add verified associative dimensions.
    if row['id'] in ('L01_UpperLink','L02_LowerLink','A01_ArmLink'):
        circles=[]
        for body in body_list(model):
            for edge in body.GetEdges():
                edge=cast(edge,'IEdge');curve=cast(edge.GetCurve(),'ICurve')
                if curve.IsCircle():
                    cp=curve.CircleParams
                    if abs(cp[6]-.0041)<1e-7 and abs(cp[2])<1e-7:circles.append((edge,cp))
        circles.sort(key=lambda x:x[1][1])
        if len(circles)>=2:
            d.ClearSelection2(True)
            views[0].SelectEntity(cast(circles[0][0],'IEntity'),False)
            views[0].SelectEntity(cast(circles[-1][0],'IEntity'),True)
            obj=d.AddVerticalDimension2(.071,.180,0)
            if obj:dims.append(cast(cast(obj,'IDisplayDimension').GetDimension2(0),'IDimension').SystemValue)
            d.ClearSelection2(True)
    dr.ActivateView('')
    note(d,'模块化机械宠物  /  '+('装配工程图' if is_assembly else '零件工程图'),22,280,4)
    note(d,row['id'].split('_')[0]+'  '+row['name'],22,269,4)
    note(d,'第一角投影    比例 '+f'{scale:.3g}:1',285,274,2.8)
    if row.get('front_configuration'):note(d,'主视图：面框与柔性圈拆下，显示内部紧固件',42,245,2.8)
    if code in ('C02','Q02'):note(d,'底面安装视图 0.6:1' if code=='C02' else '截面端视图 4:1',285,264,2.8)
    outline=views[3].GetOutline();note(d,f'等轴测图 {iso_scale:.3g}:1',outline[0]*1000,max(68,outline[1]*1000-5),2.4)
    note(d,'关键尺寸与接口说明',22,63,3.1)
    body='尺寸：'+row['key_dimensions_mm']+'\n材料：'+material_text(row['material_assumption'])+'\n说明：'+row['notes']
    lines=[]
    for t in body.splitlines():
        wrapped=textwrap.wrap(t,58,break_long_words=True) or ['']
        if len(wrapped)>1 and wrapped[-1] and all(c in '。；，、.,;:！？!?' for c in wrapped[-1]):
            last=wrapped.pop();wrapped[-1]+=last
        lines.extend(wrapped)
    note(d,'\n'.join(lines[:7]),22,55,2.4)
    note(d,'视图关联原生零件；孔位及公差须复核后制造。',255,57,2.4)
    d.ViewZoomtofit2();d.GraphicsRedraw2()
    out=ROOT/('drawings/assemblies' if is_assembly else 'drawings/parts')/f'{path.stem}.SLDDRW'
    if export_pdf:print_pdf(d,ROOT/'drawings/pdf'/f'{path.stem}.pdf')
    save(d,out)
    preview_path=ROOT/'previews/drawings'/f'{path.stem}.bmp';preview_path.parent.mkdir(parents=True,exist_ok=True)
    view=cast(d.ActiveView,'IModelView');view.Scale2=view.Scale2*.75
    d.GraphicsRedraw2();d.SaveBMP(str(preview_path),2400,1697)
    result={'id':row['id'],'drawing':str(out),'views':[list(v.GetOutline()) for v in views],'associative_overall_dimensions_m':dims,'interface_dimensions':interface_dims,'scale':scale}
    print('DRAWING_DONE',row['name'],dims,flush=True)
    sw.CloseDoc(d.GetTitle());sw.CloseDoc(model.GetTitle());return result

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();cat=json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))
    row=next(x for x in cat if x['id']=='L01_UpperLink')
    print(json.dumps(make(sw,row),ensure_ascii=False),flush=True)
