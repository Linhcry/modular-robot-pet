"""Manufacturer-data screening, not a thermal or whole-body validation."""
from compare_remote_knee_drive import *
import hashlib,sys,csv

def main():
    factor=1.3;eta=.85
    variants=[{'版本':'12V','额定_Nm':20*.0980665,'堵转_Nm':80*.0980665,'空载_rpm':62.,'额定电流_A':1.475,'堵转电流_A':5.9,'输入_V':[9,12.6]},
              {'版本':'24V','额定_Nm':21*.0980665,'堵转_Nm':85*.0980665,'空载_rpm':70.,'额定电流_A':.975,'堵转电流_A':3.9,'输入_V':[16.8,25.2]}]
    for s in variants:
        p=ROOT/'vendor'/f"SM80BL_{s['版本']}_厂家规格.pdf"
        s.update(质量_kg=.0975,外形_mm=[46.5,28.5,34],内部减速比=353,规格日期='2024-06-07',证据页={'额定堵转空载':3,'机械反馈':4,'保护':5,'外形寿命':6,'曲线与舵盘':7},SHA256=hashlib.sha256(p.read_bytes()).hexdigest())
    summary,_,_=swing(.002);stat=static_stance();rows=[]
    for s in variants:
        for R in (1,1.5,2,2.5,3):
            for j,key in enumerate(('髋外展','髋俯仰','膝驱动')):
                case=max([x for x in stat if x['方案']=='近端膝电机' and x['带轮减速比_R']==R],key=lambda x:abs(x[key+'_Nm']))
                demand=abs(case[key+'_Nm'])*factor/eta
                swg=next(x for x in summary if x['方案']==f'共髋轴同步带_R{R:g}' and x['电机']==key+'电机')
                # Necessary no-load speed screen only; separate peaks are NOT a torque-speed operating point.
                speed=swg['最高绝对转速_rpm']
                rows.append({'舵机':s['版本'],'外部比_R':R,'电机':key,'静态控制工况':case['局部支撑工况'],'静态筛选需求_Nm':demand,'额定_Nm':s['额定_Nm'],'静态需求对额定比':demand/s['额定_Nm'],'摆动最高_rpm':speed,'空载_rpm':s['空载_rpm'],'静态额定筛选':demand<=s['额定_Nm'],'空载速度必要条件':speed<=s['空载_rpm']})
    # Same-instant motoring-only checks on the R2 trajectory. Manufacturer Fig11 straight N curve
    # is approximated by endpoints; regenerative/braking quadrants are intentionally not inferred.
    history=list(csv.DictReader((ROOT/'data/近端膝驱动_R2_180mm摆动时序.csv').open(encoding='utf-8-sig')))
    curve=[]
    for s in variants:
        for motor in ('髋外展电机','髋俯仰电机','近端膝驱动电机'):
            vals=[];lower_vals=[];braking=0
            for x in history:
                if x['电机']!=motor:continue
                t=float(x['输出扭矩_Nm']);n=float(x['输出转速_rpm'])
                if t*n<0:braking+=1;continue
                td=abs(t)*factor/eta
                allowed=s['空载_rpm']*max(0,1-td/s['堵转_Nm'])
                vals.append((abs(n)-allowed,float(x['时间_s']),td,abs(n),allowed))
                lower_allowed=.9*s['空载_rpm']*max(0,1-td/(.9*s['堵转_Nm']))
                lower_vals.append((abs(n)-lower_allowed,float(x['时间_s']),td,abs(n),lower_allowed))
            worst=max(vals)
            curve.append({'舵机':s['版本'],'电机':motor,'电动区检查点':len(vals),'制动区未推断点':braking,'最差速度超出_rpm':worst[0],'时刻_s':worst[1],'该点扭矩_Nm':worst[2],'该点速度_rpm':worst[3],'曲线近似允许速度_rpm':worst[4],'电动区必要筛选':worst[0]<=0})
            low=max(lower_vals)
            curve[-1].update(空载及堵转各减10百分比的速度超出_rpm=low[0],端点下偏差筛选=low[0]<=0,下偏差最差时刻_s=low[1])
    csvout('SM80BL_近端传动筛选.csv',rows);csvout('SM80BL_R2_同刻曲线筛选.csv',curve)
    report={'阶段':'有规格来源的候选筛选；未冻结最终腿部驱动','日期':'2026-09-07','厂商资料':variants,'筛选约定':{'静态及摆动力矩系数':factor,'传动效率保守代理':eta,'效率边界':'静态保持没有功率效率；除0.85仅作为摩擦及传动不确定度余量，不是静态效率物理模型','旧单腿质量参数沿用':True,'未重算轻舵机后的整机惯性':True,'样本范围':'3个局部支撑姿态及180mm单腿摆动；不是全机爬阶'},'传动筛选':rows,'同刻电动区曲线筛选':curve,'厂商待澄清':['24V输入上限25.2V与第5页默认过压25V不一致，电源阈值须确认','第6页寿命动作60度/0.25s与同栏30或35rpm口径待确认','规格书额定负载符号为20/21kg.cm≤；本筛选保守采用标称数，不解释为完整连续热包络','无外部径向/轴向承载及背驱测试数据','1kHz最大位置更新率不等于12轴总线实际全反馈频率'],
      '设计决定':['SM80BL不作为全腿12轴通用直接替换；保留不同轴采用不同驱动的路线','R2近端膝驱动继续研究，但本次带余量静态额定筛选未全通过','轻载头尾无需97.5g大舵机；优先更小的反馈舵机另核算','机械臂肩轴原需求约2.97Nm，SM80直接驱动额定不足；继续比较外部减速或更高额定型号','所有动力件在大工程师取得确切型号模型后再冻结接口；当前不采购'],
      '质量替换算术':{'现腿驱动预留_kg':3.44,'十二只SM80本体_kg':12*.0975,'仅驱动质量差_kg':3.44-12*.0975,'注意':'不是整机新质量；此12轴方案未通过选型，不把差值计入正式BOM'}}
    (ROOT/'validation/SM80BL候选筛选.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# SM80BL智能舵机候选与传动筛选','','2026-09-07。用户授权自行决定电机或舵机。本报告为候选筛选，不是最终选型或采购清单。','',
      '厂家2024-06-07 A/0规格书给出97.5±1g、46.5×28.5×34mm、RS485、位置/电流/温度等反馈，内部减速比353:1。第6–7页已视觉检查尺寸与曲线；不能按低减速比准直驱的背驱性能使用。','',
      '| 版本 | 标称额定 Nm | 堵转 Nm | 空载 rpm | 输入范围 V |','|---|---:|---:|---:|---|']
    for s in variants:lines.append(f"| {s['版本']} | {s['额定_Nm']:.3f} | {s['堵转_Nm']:.3f} | {s['空载_rpm']:.0f} | {s['输入_V']} |")
    lines+=['','本地厂家原件：[12V规格](../vendor/SM80BL_12V_厂家规格.pdf)、[24V规格](../vendor/SM80BL_24V_厂家规格.pdf)。[12V公开产品页](https://www.feetechrc.com/552209.html)。','',
      '## 筛选约定','', '沿用旧质量模型以隔离传动拓扑影响，三个局部支撑姿态的绝对力矩乘1.3，再除0.85作为传动不确定度余量。静态保持没有功率效率，这里的0.85是保守代理。比较额定值仅表示本设计采用“不依赖短时过载”的预筛，不证明超过额定的短动作绝对不可行。没有解全机平衡，也没有实测热曲线。','',
      '| 24V，外部比 | 轴 | 静态带余量 Nm | 对额定比 | 摆动最高 rpm |','|---|---|---:|---:|---:|']
    for x in rows:
        if x['舵机']=='24V' and x['外部比_R'] in (2,3):lines.append(f"| {x['外部比_R']} | {x['电机']} | {x['静态筛选需求_Nm']:.3f} | {x['静态需求对额定比']:.2f} | {x['摆动最高_rpm']:.2f} |")
    lines+=['','R2使膝扭矩降低，但带余量静态需求仍超过额定；继续加大比例又会增加近端驱动转速。不能把各自发生在不同时间的最大扭矩、最大速度拼成同一负载点。另一个CSV逐时刻检查R2轨迹：只在正机械功率区，用厂家直线速度曲线端点近似；制动和再生区单列为未验证。','',
      '厂家同时标注空载速度和堵转扭矩±10%。将两端点都下调10%的敏感性预筛中，12V的R2近端膝驱动已超出近似速度曲线，24V在当前电动摆动区仍有余量；这不是实测四象限工作包络，也不能覆盖静态额定、回生和温升问题。','',
      '## 本阶段设计决定','']+['- '+x for x in report['设计决定']]+['','## 规格边界','']+['- '+x for x in report['厂商待澄清']]+['','不能将80/85kgf·cm堵转扭矩当成连续能力。过流超过2.5A持续2s会关断输出，过温70°C也会关断；动作控制器必须识别故障并有序恢复。','',
      '舵盘图示外径18.8、4-M3孔在直径14分布圆、中心孔3.1、总厚5.4mm；图中25T文字仍写SM40BL，属于厂家图纸型号标注待核项。对侧凸台/支承面、30处M3×3深孔及线束出口需与实际大工程师模型交叉校验，尚未自制接口替代厂家模型。']
    (ROOT/'docs/10_智能舵机候选与驱动筛选.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'方案行数':len(rows),'同刻曲线检查':curve,'结论':report['设计决定']},ensure_ascii=False,indent=2))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
