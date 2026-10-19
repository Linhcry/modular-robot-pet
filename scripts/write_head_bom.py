"""Current assembly quantities and evidence-bounded GB/T size families."""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1]
cat={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))}
standards=[
{'编号':'S01_M3x10','标准':'GB/T 70.1-2008','名称':'内六角圆柱头螺钉','状态':'现行','官方状态来源':'https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=AA481BA038B2F9CE68879E6B087F4F73','当前模型名义尺寸':'M3×10；头外径5.5、头高3mm；螺纹与内六角简化'},
{'编号':'S02_M3Washer','标准':'GB/T 97.1-2002','名称':'平垫圈 A级','状态':'现行','官方状态来源':'https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=199E0585386FDF8B9CACF6225BA5F924','当前模型名义尺寸':'内径3.2、外径7、厚0.5mm'},
{'编号':'S03_M3Nut','标准':'GB/T 6170-2015','名称':'1型六角螺母','状态':'现行','官方状态来源':'https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=BDDE5AF77AC2FBC2D194289F10C69A4B','当前模型名义尺寸':'M3；对边5.5、厚2.4mm；未建牙型','尺寸交叉来源':'https://www.jlc-jdgf.com/mcbook/GBT6170-2000.htm','厂家尺寸交叉来源':'https://www.006008.com/?p=2817','交叉结果':'M3粗牙螺距0.5；表中厚度最大2.40/最小2.15，对边最大5.50/最小5.32；当前几何取最大包络'}]
byid={r['编号']:r for r in standards}
plan=[('H04_TouchHeadShell',1),('H05_TouchBezel',1),('H06_ScreenBracket',1),('H07_ScreenSeal',1),('V03_DsiScreen',1),('S01_M3x10',4),('S02_M3Washer',8),('S03_M3Nut',4)]
rows=[]
for n,(code,qty) in enumerate(plan,1):
    r=cat[code];s=byid.get(code)
    rows.append({'序号':n,'编号':code,'中文名称':r['name'],'数量':qty,'标准或来源':s['标准'] if s else ('Waveshare原厂STEP' if code.startswith('V') else '本项目自制候选'),'规格或尺寸':s['当前模型名义尺寸'] if s else r['key_dimensions_mm'],'零件文件':Path(r['path']).name,'采购状态':'后续采购；无下单' if s or code.startswith('V') else '未制造释放','限制':'尚未取得大工程师对应模型；材料等级、表面处理、公差和供货版本未冻结' if s else r['notes']})
assert sum(r['数量'] for r in rows)==21
with (ROOT/'data/触控头部承架紧固装配清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
report={'核对日期':'2026-09-08','标准状态与尺寸族':standards,'结论边界':'官方页面核实标准状态，采购平台/厂家尺寸表交叉核对M3螺母包络。简化几何不能证明实购件符合全部公差、性能等级、检验或防腐要求；国标尺寸族已明确，材料/供货规格和大工程师模型仍待选定。','装配种类数':len(rows),'装配组件数':sum(r['数量'] for r in rows),'未采购':True}
(ROOT/'validation/头部紧固件国标与装配清单核对.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
