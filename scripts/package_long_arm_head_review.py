"""Native-only review package; failed STEP candidates are deliberately excluded."""
from pathlib import Path
import hashlib,json,zipfile,csv,collections
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
assembly=json.loads((ROOT/'validation/头部长臂螺母防落装配检查.json').read_text(encoding='utf-8'))
reopen=json.loads((ROOT/'validation/长臂头部装配图与重开检查.json').read_text(encoding='utf-8'))
paths=json.loads((ROOT/'validation/长臂螺母杯安装路径检查.json').read_text(encoding='utf-8'))
assert assembly['组件数']==25 and assembly['配合数']==52 and not assembly['干涉'] and not assembly['配合错误']
assert len(paths['离散安装路径'])==64 and len(paths['几何反例检查'])==24
assert len(reopen['重开配置检查'])==3 and all(not r['配合错误'] for r in reopen['重开配置检查'])
assert reopen['重开配置检查'][0]['本次重开干涉']==[]
asm=Path(reopen['原生装配']);assert hashlib.sha256(asm.read_bytes()).hexdigest()==reopen['原生装配SHA256']
for p,h in assembly['原生零件SHA256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
cat={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))}
quantities={'H10_ClearanceHeadShell':1,'H11_LongArmNutCup':4,'H05_TouchBezel':1,'H06_ScreenBracket':1,
            'H07_ScreenSeal':1,'V03_DsiScreen':1,'S01_M3x10':4,'S02_M3Washer':8,'S03_M3Nut':4}
assert sum(quantities.values())==25
bom=ROOT/'data/长臂头部装配清单.csv'
with bom.open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['编号','中文名称','数量','原生零件','性质'])
    for code,qty in quantities.items():
        r=cat[code];writer.writerow([code,r['name'],qty,Path(r['path']).name,'厂家参考' if code.startswith('V') else '标准件简化参考' if code.startswith('S') else '自制候选'])
pdf_report_path=ROOT/'validation/长臂头部图纸交付复核.json'
pdf_report=json.loads(pdf_report_path.read_text(encoding='utf-8'))
pdf=Path(pdf_report['合册']);assert hashlib.sha256(pdf.read_bytes()).hexdigest()==pdf_report['SHA256']
with pymupdf.open(pdf) as combined:
    assert len(combined)==6
    for i,s in enumerate(pdf_report['源图']):
        p=Path(s['路径']);assert hashlib.sha256(p.read_bytes()).hexdigest()==s['SHA256']
        with pymupdf.open(p) as source:assert source[0].get_text()==combined[i].get_text()
# Run only after the six corresponding page renderings have been viewed.
pdf_report['逐页视觉检查']='六页内容已逐页查看；新装配/H10/H11源图渲染和合册后三页渲染均已复核，合册与六张源图文字一致。未发现裁切及标注重叠。'
pdf_report_path.write_text(json.dumps(pdf_report,ensure_ascii=False,indent=2),encoding='utf-8')
reopen['视觉检查']='装配工程图PDF已渲染查看；主视图维修配置与其他完整视图可辨，无文字裁切。'
(ROOT/'validation/长臂头部装配图与重开检查.json').write_text(json.dumps(reopen,ensure_ascii=False,indent=2),encoding='utf-8')
files=[Path(cat[i]['path']) for i in quantities]+[asm,Path(reopen['原生工程图']['drawing']),pdf,bom]
for code in quantities:
    if code.startswith('H'):files.append(ROOT/'drawings/parts'/(Path(cat[code]['path']).stem+'.SLDDRW'))
files.extend(ROOT/'validation'/n for n in ['头部长臂螺母防落装配检查.json','长臂头部装配图与重开检查.json',
    '长臂螺母杯零件检查.json','长臂螺母杯工程图检查.json','长臂螺母杯安装路径检查.json',
    '长臂螺母杯尺寸链核算.json','长臂螺母杯_杯内配合独立检查.json','长臂头部图纸交付复核.json',
    '原生头壳高精度体积与AP214检查.json','头壳周期面拆分导出诊断.json','头壳保留周期面STEP原生回读诊断.json'])
files.append(ROOT/'docs/16_螺母防落结构与STEP导出接续.md')
assert len(set(files))==len(files)
for p in files:assert p.is_file(),p
assert not any(p.suffix.upper() in ('.STEP','.STP') for p in files)
manifest=[{'文件':p.relative_to(ROOT).as_posix(),'SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'字节数':p.stat().st_size} for p in files]
readme='''触控视觉头部 - 长臂螺母防落结构审阅包

先查看 drawings/pdf/触控视觉头部_长臂螺母防落六页审阅版.pdf。
SolidWorks 打开 assemblies/触控视觉头部_长臂螺母防落候选.SLDASM。
保留目录结构；如提示引用位置，请选本包parts目录中的同名零件。
共9种独立SLDPRT、25个组件、52个真实配合、5张独立零件图和1张装配图。
默认配置完整；面框拆下_长臂螺母杯配置仅抑制面框与柔性圈。

本包是名义结构候选，未制造释放。
四组防落杯安装原点Z37.6，止挡顶Z42.1，杯底卸载间隙0.6mm。
原生配合、名义干涉、64个离散安装位置及24个几何反例已检查。
卡扣应力、保持力、疲劳、真实打印公差和卸扣工具仍未验证。
屏幕及面框自身完整紧固、相机、控制板、散热、线缆仍待完善。
标准件为对应尺寸族简化实体，实际材料/等级/供应商未冻结；采购件未购买。

头壳STEP导出/回读仍有曲面转换问题，本包不含STEP。
“没有缺失曲线引用”不能代替跨CAD几何等价验证。
原生零件保持不变；有问题的转换候选均未替代正式原生模型。
详情见docs和validation，逐文件校验值见文件清单.json。
'''
out=ROOT/'output/触控视觉头部_长臂防落原生审阅包.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,p.relative_to(ROOT).as_posix())
    z.writestr('先读我.txt',readme.encode('utf-8'))
    z.writestr('文件清单.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    for row in manifest:assert hashlib.sha256(z.read(row['文件'])).hexdigest()==row['SHA256']
report={'审阅包':str(out),'原生零件种数':9,'组件数':25,'配合数':52,'原生工程图数':6,'PDF页数':6,
        'STEP文件数':0,'ZIP逐文件校验':True,'字节数':out.stat().st_size,'SHA256':hashlib.sha256(out.read_bytes()).hexdigest()}
(ROOT/'validation/长臂头部审阅包检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
