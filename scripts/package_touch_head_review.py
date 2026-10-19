"""Package only current head references, drawings and audits after delivery validation."""
from pathlib import Path
import hashlib,json,zipfile,re
ROOT=Path(__file__).resolve().parents[1]
review=json.loads((ROOT/'validation/触控头部图纸交付复核.json').read_text(encoding='utf-8'))
assert review['逐页视觉检查']!='待检查' and len(review['承架紧固总成配置复查'])==3
assert hashlib.sha256(Path(review['合册']).read_bytes()).hexdigest()==review['SHA256']
cat={r['id']:r for r in json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'))}
ids=['H04_TouchHeadShell','H05_TouchBezel','H06_ScreenBracket','H07_ScreenSeal','V03_DsiScreen','S01_M3x10','S02_M3Washer','S03_M3Nut']
files=[Path(cat[i]['path']) for i in ids]
files.append(ROOT/'assemblies/触控视觉头部_承架紧固候选.SLDASM')
files.append(ROOT/'drawings/assemblies/触控视觉头部_承架紧固候选.SLDDRW')
for i in ids[:4]:
    stem=Path(cat[i]['path']).stem
    files.extend([ROOT/'drawings/parts'/(stem+'.SLDDRW'),ROOT/'exports/step'/(stem+'.STEP')])
files.append(Path(review['合册']))
files.extend(ROOT/'validation'/n for n in ['头部直进工具通道预筛.json','头部承架紧固与工具空间检查.json','触控头部最终孔轴复核.json','触控头部工程图检查.json','触控头部图纸交付复核.json'])
files.append(ROOT/'docs/15_触控视觉头部与智能化接口规划.md')
files.append(ROOT/'data/触控头部承架紧固装配清单.csv')
files.append(ROOT/'validation/头部紧固件国标与装配清单核对.json')
files.append(ROOT/'validation/相机D16窗口条件预筛.json')
for p in files:assert p.is_file(),p
# Check before opening/replacing an existing ZIP. A successful SW SaveAs is
# insufficient: the curved shell exports have contained undefined edge curves.
for p in files:
    if p.suffix.upper()=='.STEP':
        assert not re.search(r'EDGE_CURVE\s*\([^;]*?,\s*\$\s*,',p.read_text(encoding='latin1')),('STEP曲线定义缺失，停止打包，先修复导出',p)
manifest=[{'文件':p.relative_to(ROOT).as_posix(),'SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'字节数':p.stat().st_size} for p in files]
out=ROOT/'output/触控视觉头部_承架紧固审阅包.zip';out.parent.mkdir(exist_ok=True)
readme='''触控视觉头部｜承架紧固审阅包

先查看 drawings/pdf/触控视觉头部_齐平嵌入五页审阅版.pdf。
SolidWorks 请打开 assemblies/触控视觉头部_承架紧固候选.SLDASM。
保留文件夹结构；若要求定位引用件，选择本包 parts 目录中的同名文件。

总成21组件、44配合；四张自制零件图和一张装配图。
默认配置完整；面框拆下_承架紧固配置仅拆下面框与柔性圈。
承架孔距78×56mm；玻璃、面框、柔性圈名义齐平。
零件、图纸、STEP为本次审阅所用版本，逐件SHA256见文件清单.json。

这是结构候选，未制造释放：螺母防掉落/扳手路径、屏幕和面框紧固、
相机、控制板、散热、线束及整机载荷验证仍未完成。
紧固件按GB/T70.1-2008、GB/T97.1-2002和GB/T6170-2015对应尺寸族预选，
已核实上述标准现行；模型为简化参考实体，不含螺纹牙型，材料等级等仍未冻结。
厂家屏幕来自Waveshare STEP，均非大工程师下载模型。
H07为硅胶装配态名义几何，不可直接用于开模。
完整设计记录及验证边界见 docs 与 validation 目录。
'''
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,p.relative_to(ROOT).as_posix())
    z.writestr('先读我.txt',readme.encode('utf-8'))
    z.writestr('文件清单.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    for row in manifest:assert hashlib.sha256(z.read(row['文件'])).hexdigest()==row['SHA256']
report={'审阅包':str(out),'原生独立零件文件数':8,'原生总成数':1,'原生工程图数':5,'受检文件数':len(files),'ZIP_SHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'字节数':out.stat().st_size,'ZIP逐文件校验':True}
(ROOT/'validation/触控头部审阅包检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
