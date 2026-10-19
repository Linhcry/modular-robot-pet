"""四点式储物导向候选，使用原导轨截面；不覆盖旧装配。"""
from build_mechanism_parts import *

def short_shoe(d):
    pts=[(-11,2.3),(-5.4,2.3),(-7.5,8.4),(7.5,8.4),(5.4,2.3),(11,2.3),(11,13.2),(-11,13.2)]
    profile(d,'短滑靴燕尾截面_每条导轨两支点',pts,(),24)
    sketch(d,'M3攻丝底孔_位于长度中心',lambda sm:sm.CreateCircleByRadius(0,-.012,0,.00125),index=1)
    cut(d,'M3底孔穿透4_8厚连接顶壁',6,8)
    assert chamfer_top(d,.2),'滑入端倒角失败'

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.FrameState=C.swWindowMinimized
    import refine_curved_parts as refine_module
    refine_module.preview=lambda *a,**k:False
    sw.CommandInProgress=True
    try:
        cat=json.loads(CAT_PATH.read_text(encoding='utf-8'))
        add_part(sw,cat,'Q05_ShortShoe','分体短燕尾滑靴',short_shoe,'长24；宽22；顶高13.2；顶壁4.8；M3底孔D2.5位于Z12','6061-T6 铝合金（设计假设）','每条导轨布置2件，全舱4件。M3×8穿过0.5垫圈与3mm舱底后啮合4.5mm，名义余隙0.3mm；公差与防松未释放。导向面间隙沿用原型，另需独立防退出锁止。')
        row=next(x for x in cat if x['id']=='Q05_ShortShoe')
        d=cast(sw.OpenDoc6(row['path'],1,1,'',0,0)[0],'IModelDoc2')
        errors=[(f.Name,f.GetErrorCode2()) for f in features(d) if f.GetErrorCode2()[0]]
        volume=sum(b.GetMassProperties(1)[3] for b in body_list(d))*1e9
        result={'编号':row['id'],'名称':row['name'],'实体数':len(body_list(d)),'重建错误':errors,'体积_mm3':volume,'估计单件质量_g':volume*.0027,'拟装数量':4,'估计四件质量_g':volume*.0027*4,'M3名义啮合_mm':4.5,'螺钉端名义余隙_mm':.3,'文件':row['path'],'阶段':'减重候选；待几何配合和实体干涉检查'}
        assert result['实体数']==1 and not errors
        sw.CloseDoc(d.GetTitle())
        (ROOT/'validation/分体短滑靴检查.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2))
    finally:sw.CommandInProgress=False
