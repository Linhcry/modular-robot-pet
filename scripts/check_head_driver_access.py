"""Exact vendor-solid Boolean checks of an assumed D5 straight tool corridor."""
from build_touch_head import *

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True;doc=None
    try:
        cat=json.loads(CAT_PATH.read_text(encoding='utf-8'));r=next(r for r in cat if r['id']=='V03_DsiScreen')
        doc=cast(sw.OpenDoc6(r['path'],1,1,'',0,0)[0],'IModelDoc2');sources=[]
        for b in body_list(doc):
            tmp=cast(b.Copy(),'IBody2');assert tmp.ApplyTransform(transform(sw,(-2,-12,61.1),PANEL_ROT));sources.append((b.Name,tmp))
        modeler=cast(sw.GetModeler(),'IModeler');rows=[]
        for xmag in (37,39):
            for sign in (-1,1):
                for y in (-28,28):
                    x=xmag*sign;hits=[]
                    for name,source in sources:
                        tool=cast(modeler.CreateBodyFromCyl(mm_array([x/1000,y/1000,.0547,0,0,1,.0025,.060])),'IBody2');assert tool
                        result=tool.Operations2(C.SWBODYINTERSECT,cast(source.Copy(),'IBody2'),0)
                        assert result[1] in (0,5,6,1067),(name,result[1])
                        solids=[cast(b,'IBody2') for b in (result[0] or [])];v=sum(b.GetMassProperties(1)[3] for b in solids)*1e9
                        if v>1e-6:hits.append({'厂家实体':name,'交叠体积_mm3':v})
                    rows.append({'工具中心_mm':[x,y,54.7],'工具外径_mm':5,'工具有效直线段_mm':60,'与屏幕实体交叠':hits})
        assert any(r['与屏幕实体交叠'] for r in rows if abs(r['工具中心_mm'][0])==37)
        assert not any(r['与屏幕实体交叠'] for r in rows if abs(r['工具中心_mm'][0])==39)
        report={'日期':'2026-09-08','阶段':'前面框拆下、屏幕已装时的直进工具通道预筛','工具':'D5x60直圆柱几何预留，尚未冻结具体工具型号或手柄包络','检查对象':'厂家触控屏10实体，保持头部安装变换；原始文件未改','结果':rows,'结论':'承架螺钉X±37妨碍D5直进工具，外移到±39消除本项屏幕遮挡；仍须检查完整头壳和真实紧固件','API来源':'https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModeler~CreateBodyFromCyl.html'}
        (ROOT/'validation/头部直进工具通道预筛.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
    finally:
        if doc:sw.CloseDoc(doc.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized
