"""SM105BL-C001 source-based pre-screen; preserve the legacy mass model explicitly."""
from compare_remote_knee_drive import *
import hashlib

def main():
    source=ROOT/'vendor/electronics_sources/SM105B_C001_厂家规格.pdf';rated=50*.0980665;stall=150*.0980665;speed=60.;margin=1.3/.85
    fine,_,_=swing(.002);stat=static_stance();rows=[]
    for R in (1,1.5,2,2.5,3):
        for name in ('髋外展','髋俯仰','膝驱动'):
            cases=[s for s in stat if s['方案']=='近端膝电机' and s['带轮减速比_R']==R]
            worst=max(cases,key=lambda s:abs(s[name+'_Nm']));demand=abs(worst[name+'_Nm'])*margin
            s=next(x for x in fine if x['方案']==f'共髋轴同步带_R{R:g}' and x['电机']==name+'电机')
            rows.append({'传动比':R,'驱动轴':name,'静态带余量_Nm':demand,'静态对额定比':demand/rated,'最高摆动_rpm':s['最高绝对转速_rpm'],'静态额定预筛':demand<=rated,'速度减10百分比预筛':s['最高绝对转速_rpm']<=speed*.9,'静态工况':worst['局部支撑工况']})
    # Evaluate matched torque-speed points for R1.5, not independent maxima.
    dt=.002;n=1050;Q=[ik(path(i*dt,.275,.18)) for i in range(n+1)];curves=[]
    for j,name in enumerate(('髋外展','髋俯仰','膝驱动')):
        cases=[];braking=0
        for i,q in enumerate(Q):
            v=[0.]*3 if i in (0,n) else [(Q[i+1][k]-Q[i-1][k])/(2*dt) for k in range(3)]
            a=[0.]*3 if i in (0,n) else [(Q[i+1][k]-2*q[k]+Q[i-1][k])/dt**2 for k in range(3)]
            tm,vm=transform_load(torque(q,v,a,REMOTE),v,1.5);t=tm[j];rpm=vm[j]*60/(2*math.pi)
            if t*rpm<0:braking+=1;continue
            td=abs(t)*margin;allowed=.9*speed*max(0,1-td/(.9*stall));cases.append((abs(rpm)-allowed,i*dt,td,abs(rpm),allowed))
        worst=max(cases)
        curves.append({'轴':name,'电动区点数':len(cases),'制动区未验证点数':braking,'最差超出_rpm':worst[0],'时刻_s':worst[1],'该刻带余量_Nm':worst[2],'该刻_rpm':worst[3],'端点均减10百分比曲线允许_rpm':worst[4],'电动区预筛':worst[0]<=0})
    mass_rows=[]
    for total_mass in (5.3,7.,10.):
        maxima=[0.,0.,0.]
        for deg,share in [((0,-25,50),.25),((5,-65,120),.4),((5,-25,90),.55)]:
            q=tuple(map(math.radians,deg));F=(0,0,total_mass*G*share);g=point_gravity(q,REMOTE)
            tj=[g[j]-dot(jacobian(q)[j],F) for j in range(3)];tm,_=transform_load(tj,(0,0,0),1.5)
            maxima=[max(maxima[j],abs(tm[j])*margin) for j in range(3)]
        mass_rows.append({'含载荷总质量_kg':total_mass,'R1.5各轴带余量静态_Nm':maxima,'各轴额定预筛':[t<=rated for t in maxima]})
    report={'日期':'2026-09-08','阶段':'候选预筛，未最终选型','厂家页面型号':'SM-105B-C001','PDF型号':'SM105BL-C001','规格日期':'2025-05-28 A/0','原件':str(source),'SHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'参数':{'额定_Nm':rated,'堵转_Nm':stall,'空载_rpm':speed,'额定电流_A':2.1,'堵转电流_A':6.3,'质量_g':200,'内部减速比':254,'输入_V':[9,16],'壳体_mm':[58.5,33.5,44],'厂家图含舵盘高度_mm':49.1},'静态及速度筛选':rows,'R1_5同刻曲线':curves,'总质量敏感性':mass_rows,'边界':['沿用原单腿质量，5.3kg为目标含载荷质量；另算7/10kg反力敏感性，不是重建完整质量惯量模型','1.3/0.85为设计余量代理；静态没有功率效率含义','三种局部支撑姿态不能证明全机平衡或楼梯可靠性','曲线为厂家图的直线端点近似；四象限、温升及连续热包络未验证','PDF第5页只给出70摄氏度关断，未列过流阈值；不能套用SM80的2.5A/2s','页6标注舵机噪声70±5dB且无防水，宠物安静目标需实测，不能按马达45dB宣传','页面型号与PDF型号写法不同、配件栏文字No Accessories但有舵盘图，供货版本需确认','厂家图12-M2.5x3深孔、舵盘8-M3 PCD21和总高49.1已阅；仍须大工程师对应型号三维核对','R1.5同步带的轴承、张紧、带宽和新增质量未设计；不把仅电机减重直接记为整机减重']}
    csvout('SM105BL_C001_驱动候选筛选.csv',rows)
    (ROOT/'validation/SM105BL_C001候选筛选.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# SM105BL-C001候选筛选','', '2026-09-08。厂家规格书与本机局部模型预筛，尚未冻结采购和接口。','',f'标称额定{rated:.3f}Nm，堵转{stall:.3f}Nm，空载60rpm，200±3g，9–16V输入；规格书日期2025-05-28。','', '[厂家产品页](https://www.feetechrc.com/861651.html)。厂家PDF和SHA256见验证JSON。','', '| R1.5轴 | 带余量静态 Nm | 对额定比 | 摆动最高 rpm |','|---|---:|---:|---:|']
    for r in rows:
        if r['传动比']==1.5:lines.append(f"| {r['驱动轴']} | {r['静态带余量_Nm']:.3f} | {r['静态对额定比']:.2f} | {r['最高摆动_rpm']:.2f} |")
    lines+=['','R1.5可继续进入传动详细设计，依据是以上有限工况的预筛；不能据此宣布全机动作可行。电动摆动区逐时刻比较力矩和速度，并将厂家曲线两端点各下调10%；制动区单独保留未验证。','','| 含载荷总质量 kg | 髋外展 Nm | 髋俯仰 Nm | 膝驱动 Nm |','|---|---:|---:|---:|']
    for row in mass_rows:lines.append('| '+str(row['含载荷总质量_kg'])+' | '+' | '.join(f'{v:.3f}' for v in row['R1.5各轴带余量静态_Nm'])+' |')
    lines+=['','以上改变总反力而保留单腿质量参数，仅为重量敏感性。当前旧方案约9.66kg的估重不能被5.3kg目标工况替代；总机减重是这套轻驱动成立的前提。','']+['- '+s for s in report['边界']]
    (ROOT/'docs/14_SM105舵机与近端驱动预筛.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'R1.5':[r for r in rows if r['传动比']==1.5],'同刻预筛':curves},ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8');main()
