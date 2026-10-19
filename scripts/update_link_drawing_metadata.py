from sw_core import *
sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized
p=ROOT/'data/parts_catalog.json';rows=json.loads(p.read_text(encoding='utf-8'))
row=next(r for r in rows if r['id']=='L01_UpperLink')
row['notes']='端部R24与收腰R30圆弧相切，直腰过渡；适配AK45-10输出转接盘。两端PCD38孔组；为候选接口，最终电机待大工程师具体规格确认。'
d=cast(sw.OpenDoc6(row['path'],1,1,'',0,0)[0],'IModelDoc2')
try:
    pm=cast(cast(d.Extension,'IModelDocExtension').CustomPropertyManager(''),'ICustomPropertyManager')
    pm.Set2('设计说明',row['notes']);save(d,row['path'])
finally:sw.CloseDoc(d.GetTitle())
p.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
