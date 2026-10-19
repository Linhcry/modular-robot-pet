"""Remote knee drive: signed loads and ideal transmission coupling, no motor selection."""
from calculate_step_transfer import *
import random

BASE={'hip_pitch':.32,'upper':.12,'knee_motor':.34,'lower':.115,'foot':.106}
# Keep the same total mass. Move 300g from knee to hip; retain 40g distal transmission.
# Extra belt/pulley/bearing/bracket mass is NOT silently subtracted from robot weight.
REMOTE={**BASE,'hip_pitch':.62,'knee_motor':.04}

def transform_load(t,v,R):
    # Both motor stators on hip carrier; belt proximal pulley absolute angle a.
    # a = h + R*k, independent motor coordinates u=(r,h,a).
    # Virtual work gives tau_m=(tau_r,tau_h-tau_k/R,tau_k/R).
    return [t[0],t[1]-t[2]/R,t[2]/R],[v[0],v[1],v[1]+R*v[2]]

def swing(dt=.004):
    n=round(2.1/dt);dt=2.1/n
    Q=[ik(path(i*dt,.275,.18)) for i in range(n+1)]
    summary=[];history=[];max_power_error=0.
    for label,masses,R in [('原膝端电机',BASE,0),('电机近端化_独立随动传动',REMOTE,0)]+[(f'共髋轴同步带_R{R:g}',REMOTE,R) for R in (1,1.5,2,2.5,3)]:
        samples=[]
        for i,q in enumerate(Q):
            v=[0.]*3 if i in (0,n) else [(Q[i+1][j]-Q[i-1][j])/(2*dt) for j in range(3)]
            a=[0.]*3 if i in (0,n) else [(Q[i+1][j]-2*q[j]+Q[i-1][j])/dt**2 for j in range(3)]
            t=torque(q,v,a,masses)
            tm,vm=transform_load(t,v,R) if R else (t,v)
            max_power_error=max(max_power_error,abs(dot(t,v)-dot(tm,vm)))
            samples.append((tm,vm))
            if dt<.003 and R==2:
                for j,name in enumerate(('髋外展电机','髋俯仰电机','近端膝驱动电机')):
                    history.append({'方案':label,'时间_s':i*dt,'电机':name,'输出扭矩_Nm':tm[j],'输出转速_rpm':vm[j]*60/(2*math.pi),'机械功率_W':tm[j]*vm[j],'效率':'理想无损','工况':'固定髋180mm阶高单腿摆动'})
        for j,name in enumerate(('髋外展电机','髋俯仰电机','膝驱动电机')):
            peak=max(range(len(samples)),key=lambda i:abs(samples[i][0][j]))
            summary.append({'方案':label,'电机':name,'时间步长_s':dt,'摆动峰值_Nm':abs(samples[peak][0][j]),'峰值时转速_rpm':samples[peak][1][j]*60/(2*math.pi),'最高绝对转速_rpm':max(abs(v[j])*60/(2*math.pi) for t,v in samples),'摆动RMS_Nm':math.sqrt(sum(t[j]**2*(.5 if i in (0,n) else 1) for i,(t,v) in enumerate(samples))/n),'峰值时刻_s':peak*dt})
    return summary,history,max_power_error

def static_stance():
    rows=[]
    # Nominal single-leg loads; these are not a complete support-polygon solution.
    for label,degrees,share in [('四脚对称站立',(0,-25,50),.25),('低姿单腿载荷假设',(5,-65,120),.4),('上阶推升局部姿态',(5,-25,90),.55)]:
        q=tuple(map(math.radians,degrees));F=(0,0,5.3*G*share)
        for kind,m in [('原膝端电机',BASE),('近端膝电机',REMOTE)]:
            g=point_gravity(q,m);T=[g[j]-dot(jacobian(q)[j],F) for j in range(3)]
            for R in ([0] if kind=='原膝端电机' else [0,1,1.5,2,2.5,3]):
                tm,_=transform_load(T,(0,0,0),R) if R else (T,(0,0,0))
                rows.append({'局部支撑工况':label,'方案':kind,'带轮减速比_R':R,'单脚垂向反力_N':F[2],'髋外展_Nm':tm[0],'髋俯仰_Nm':tm[1],'膝驱动_Nm':tm[2],'注意':'有符号静力；没有动态系数或选型裕量；未解整机平衡'})
    return rows

def run():
    coarse,_,_=swing(.004);fine,history,err=swing(.002)
    change=max(abs(a['摆动峰值_Nm']-b['摆动峰值_Nm']) for a,b in zip(coarse,fine))
    assert change<.01 and err<1e-9
    rng=random.Random(701)
    for _ in range(100):
        R=rng.uniform(.5,4);t=[rng.uniform(-10,10) for _ in range(3)];v=[rng.uniform(-20,20) for _ in range(3)]
        tm,vm=transform_load(t,v,R)
        assert abs(dot(t,v)-dot(tm,vm))<1e-10
        assert abs(tm[1]+tm[2]-t[1])<1e-10 and abs(R*tm[2]-t[2])<1e-10
    assert abs(sum(BASE.values())-sum(REMOTE.values()))<1e-12
    stat=static_stance()
    csvout('膝驱动近端化摆动对比.csv',fine);csvout('膝驱动近端化静力耦合.csv',stat);csvout('近端膝驱动_R2_180mm摆动时序.csv',history)
    # Structural screening only: pitch radii for 3mm/20T and 40T pulleys.
    drive_torque=7.5;pitch_radius=.003*40/(2*math.pi)
    delta_t=drive_torque/pitch_radius
    report={'日期':'2026-09-07','阶段':'独立传动概念比较；没有选定电机或冻结制造尺寸','原质量参数_kg':BASE,'近端质量参数_kg':REMOTE,'附加传动总质量':'尚未加入；同质量位置变换用于隔离惯量效果','理想传动式':'a=h+R*k; tau_hmotor=tau_h-tau_k/R; tau_amotor=tau_k/R','功率映射最大误差_W':err,'4ms到2ms峰值变化_Nm':change,'随机虚功与反向扭矩映射检查数':100,'摆动对比':fine,'带力预筛':{'膝扭矩假设_Nm':drive_torque,'从动轮节距_mm':3,'从动轮齿数':40,'从动轮节圆半径_mm':pitch_radius*1000,'紧松边张力差_N':delta_t,'说明':'张力差不是轴承径向载荷，也不证明带宽可承载；需预紧力、包角、齿载、寿命与厂家选型表'},'未验证':['整机三脚支撑平衡和摩擦锥','带轮轴承尺寸与预紧径向载荷','传动弹性、齿隙、摩擦与反射转子惯量','额外传动零件质量和大工程师电机模型','满工况连续热负荷与扭矩转速电压联合曲线','同步带行程与机身外壳干涉']}
    (ROOT/'validation/膝驱动近端化计算.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 膝驱动近端化与同步带耦合计算','', '2026-09-07。此项用于比较传动拓扑，不是电机选型完成，也不是整机爬楼验证。','',
      '把膝附近的300g移至髋俯仰轴处，膝端保留40g，保持本次单腿质量总和不变。附加带轮、轴承、张紧件、保护罩没有凭空计为零质量；整机减重收益必须待这些件建模后重新核算。','',
      '研究方案的两个电机定子均安装在髋外展后的共同支架上，近端带轮与髋轴同轴，带轮绝对角为a，大腿角为h，膝相对大腿角为k。理想关系为 a=h+Rk。电机力矩应为 τa=τk/R、τh电机=τh−τk/R，转速为 ȧ=ḣ+Rk̇。若定子安装在运动大腿上，关系不同，不能复用此式。','',
      '| 方案 | 电机 | 摆动峰值 Nm | 最高转速 rpm | 摆动 RMS Nm |','|---|---|---:|---:|---:|']
    for x in fine:lines.append(f"| {x['方案']} | {x['电机']} | {x['摆动峰值_Nm']:.3f} | {x['最高绝对转速_rpm']:.2f} | {x['摆动RMS_Nm']:.3f} |")
    lines+=['','这些值来自同一条2.1s的180mm上阶摆动轨迹，髋固定275mm高，全程足端外力为零。独立随动传动一行仅表示同样关节轨迹下质量位置变化的对照；不代表该传动可无质量实现。所有数值未乘选型裕量。', '',
      f'若膝轴需求为7.5Nm，40齿、3mm节距从动轮的紧松边张力差约{delta_t:.1f}N。这个量级说明同步带方案必须另设承载轴承和刚性支座，不能把带轮直接挂在没有径向承载数据的小电机输出轴上。这里没有据此选定带宽或标准件。','',
      '决策：保留近端化作为候选，不能因膝驱动扭矩除以传动比而宣称整腿电机都可缩小。优先补齐总成质量、髋电机耦合负荷、预紧力与轴承载荷，再决定是否画完整传动。原有AK候选装配仍保留作尺寸和载荷对照。','',
      f'校验：100组确定种子随机虚功及反向力矩映射检查通过；同一轨迹最大功率映射误差{err:.3g}W；4ms减至2ms后摆动力矩峰值最大变化{change:.5f}Nm。','',
      '研究动机参见[Doggo机械说明](https://github.com/Nate711/StanfordDoggoProject)、[HyperDog的近端集中驱动与腿结构](https://arxiv.org/abs/2209.09171)。本文公式和本宠物结论为独立工程推导，未把参考机型性能当成本机性能。']
    (ROOT/'docs/09_膝驱动近端化与传动耦合.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'数值验证':{k:report[k] for k in ('功率映射最大误差_W','4ms到2ms峰值变化_Nm')},'主要对比':[x for x in fine if x['方案'] in ('原膝端电机','共髋轴同步带_R2')],'带力预筛':report['带力预筛']},ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8');run()
