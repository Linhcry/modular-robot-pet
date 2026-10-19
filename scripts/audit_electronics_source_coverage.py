"""Compare explicit manufacturer STEP product labels with schematic references.

Missing labels flag a geometry verification task; they do not prove missing physical parts.
"""
from pathlib import Path
import json,re,hashlib,pymupdf

ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'vendor/electronics_sources/CM5迷你底板A_厂家三维/CM5-NANO-A.step'
schematic=ROOT/'vendor/electronics_sources/CM5底板A_厂家原理图.pdf'
step=src.read_text(encoding='utf-8',errors='replace')
products=set(re.findall(r"PRODUCT\('([^']*)",step))
with pymupdf.open(schematic) as pdf:words={w[4] for p in pdf for w in p.get_text('words')}
checks=[]
for ref,function in [('CM1A','核心板连接器第一组'),('CM1B','核心板连接器第二组'),('J1','MIPI0排线插座'),('J3','MIPI1排线插座'),('H3','RTC电池插座'),('H5','风扇插座'),('Key1','BOOT按键'),('Key2','电源按键'),('Led1','状态指示灯'),('J2','USB-A插座'),('Type_C1','USB-C插座'),('TF1','MicroSD插座'),('PI1','40针排针')]:
    checks.append({'原理图位号':ref,'功能':function,'原理图文本中找到':ref in words,'STEP存在相同产品标签':ref in products})
report={'日期':'2026-09-08','厂家STEP':str(src),'STEP_SHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'厂家原理图':str(schematic),'原理图SHA256':hashlib.sha256(schematic.read_bytes()).hexdigest(),'原始STEP唯一产品标签数':len(products),'原始STEP开放曲面壳数量':step.count('OPEN_SHELL('),'原始STEP闭合壳数量':step.count('CLOSED_SHELL('),'位号交叉检查':checks,'结论边界':'位号未出现只表明无法按标签追踪；通用产品名称可能代表其他器件，不据此单独断定漏件。结合V04缺少常规安装孔、未确认板对板连接器和MIPI插座实体的位置，固定支架仍不得冻结。','后续机械门槛':['核实厂家PCB外形、孔位及三维版本与实物一致','补齐两个核心板连接器与两个MIPI插座的确切型号、位置和插拔包络','核实CM5叠层高度；核心板M2.5孔距不能直接复制为底板安装孔','固定结构只接触已确认的机械支承区，避开铜层、元件与天线净空','加入散热器与完整接头后再验证头部/机身候选位置']}
out=ROOT/'validation/CM5底板厂家三维覆盖核对.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
