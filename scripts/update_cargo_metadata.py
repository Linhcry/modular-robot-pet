from sw_core import *
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();path=ROOT/'data/parts_catalog.json';cat=json.loads(path.read_text(encoding='utf-8'))
    row=next(r for r in cat if r['id']=='C03_Tray');row['key_dimensions_mm']='136×106×2；四角去角5'
    row['notes']='可取出软质内托盘，放置在舱内四个支承柱上；取物手指空间及物品外形仍需与夹爪核对。'
    d=cast(sw.OpenDoc6(row['path'],1,1,'',0,0)[0],'IModelDoc2')
    for key,value in [('关键尺寸',row['key_dimensions_mm']),('设计说明',row['notes'])]:
        manager=cast(cast(d.Extension,'IModelDocExtension').CustomPropertyManager(''),'ICustomPropertyManager');manager.Set2(key,value)
    save(d,row['path']);sw.CloseDoc(d.GetTitle());path.write_text(json.dumps(cat,ensure_ascii=False,indent=2),encoding='utf-8')
