"""Ideal point-foot step transfer: coherent IK/time history, not a whole-robot stair proof."""
from size_actuators import *

def ik(p):
    x,y,z=p
    rad=y*y+z*z-HIP_OFFSET**2
    if rad<=0:raise ValueError('外展偏置使目标不可达')
    a=math.sqrt(rad);c=(x*x+a*a-L1**2-L2**2)/(2*L1*L2)
    if not -1<=c<=1:raise ValueError('两连杆工作空间外')
    k=math.acos(c)
    h=math.atan2(x,a)-math.atan2(L2*math.sin(k),L1+L2*math.cos(k))
    r=math.atan2(y,-z)-math.atan2(HIP_OFFSET,a)
    return r,h,k

def smooth(u):
    u=max(0.,min(1.,u));return 10*u**3-15*u**4+6*u**5

def path(t,H,rise,durations=(.8,.8,.5)):
    # Cartesian foot reference starts 20mm behind hip and 60mm before assumed riser.
    # Lift entirely before traversing; contact force is zero throughout this swing calculation.
    a,b,c=durations;high=rise+.015
    if t<=a:return (-.02,HIP_OFFSET,-H+high*smooth(t/a))
    if t<=a+b:return (-.02+.15*smooth((t-a)/b),HIP_OFFSET,-H+high)
    return (.13,HIP_OFFSET,-H+high-.015*smooth((t-a-b)/c))

def point_gravity(q,masses):
    origins,axes,foot=layout(q);hip,knee=origins[1:]
    points=[(masses['hip_pitch'],hip,0),(masses['upper'],scale(add(hip,knee),.5),1),(masses['knee_motor'],knee,1),(masses['lower'],scale(add(knee,foot),.5),2),(masses['foot'],foot,2)]
    return [sum(m*G*cross(axes[i],sub(pt,origins[i]))[2] for m,pt,last in points if i<=last) for i in range(3)]

def torque(q,qd,qdd,masses):
    M=point_model(q,masses)[1];dM=[];eps=1e-5
    for k in range(3):
        qp=list(q);qm=list(q);qp[k]+=eps;qm[k]-=eps
        a=point_model(qp,masses)[1];b=point_model(qm,masses)[1]
        dM.append([[(a[i][j]-b[i][j])/(2*eps) for j in range(3)] for i in range(3)])
    g=point_gravity(q,masses)
    return [sum(M[i][j]*qdd[j] for j in range(3))+sum(.5*(dM[k][i][j]+dM[j][i][k]-dM[i][j][k])*qd[j]*qd[k] for j in range(3) for k in range(3))+g[i] for i in range(3)]

def evaluate(H,rise,dt,write=False):
    n=round(2.1/dt);dt=2.1/n
    Q=[ik(path(i*dt,H,rise)) for i in range(n+1)]
    histories=[];worst=0
    masses={'hip_pitch':.32,'upper':.12,'knee_motor':.34,'lower':.115,'foot':.106}
    for i,q in enumerate(Q):
        p=path(i*dt,H,rise);worst=max(worst,max(abs(a-b) for a,b in zip(p,layout(q)[2])))
        # Endpoint velocity/acceleration are zero for these quintic Cartesian segments.
        qd=[0.]*3 if i in (0,n) else [(Q[i+1][j]-Q[i-1][j])/(2*dt) for j in range(3)]
        qdd=[0.]*3 if i in (0,n) else [(Q[i+1][j]-2*q[j]+Q[i-1][j])/dt**2 for j in range(3)]
        T=torque(q,qd,qdd,masses)
        for j,name in enumerate(('髋外展','髋俯仰','膝俯仰')):
            histories.append({'阶高_mm':round(rise*1000),'髋高_mm':round(H*1000),'时间_s':i*dt,'阶段':'抬脚' if i*dt<=.8 else '越过台阶' if i*dt<=1.6 else '缓降至台阶','关节':name,'角度_deg':math.degrees(q[j]),'转速_rpm':qd[j]*60/(2*math.pi),'角加速度_rad_s2':qdd[j],'有符号摆动扭矩_Nm':T[j],'机械功率_W':T[j]*qd[j],'接触力_N':0.,'足参考X_mm':p[0]*1000,'足参考Z_mm':p[2]*1000})
    assert worst<1e-9,worst
    summary=[]
    for name in ('髋外展','髋俯仰','膝俯仰'):
        rr=[r for r in histories if r['关节']==name]
        peak=max(rr,key=lambda r:abs(r['有符号摆动扭矩_Nm']))
        summary.append({'关节':name,'最小角_deg':min(r['角度_deg'] for r in rr),'最大角_deg':max(r['角度_deg'] for r in rr),'最高转速_rpm':max(abs(r['转速_rpm']) for r in rr),'最大角加速度_rad_s2':max(abs(r['角加速度_rad_s2']) for r in rr),'摆动峰值扭矩_Nm':abs(peak['有符号摆动扭矩_Nm']),'该扭矩时转速_rpm':peak['转速_rpm'],'最大绝对机械功率_W':max(abs(r['机械功率_W']) for r in rr),'摆动RMS_Nm':math.sqrt(sum(r['有符号摆动扭矩_Nm']**2*(.5 if i in (0,n) else 1) for i,r in enumerate(rr))/n)})
    if write:csvout(f'单脚{round(rise*1000)}mm阶高转移时序.csv',histories)
    return {'阶高_mm':rise*1000,'髋高_mm':H*1000,'持续时间_s':2.1,'时间步长_s':dt,'IK回代最大误差_mm':worst*1000,'关节':summary}

def main():
    results=[]
    for H,rise in ((.245,.15),(.275,.18)):
        coarse=evaluate(H,rise,.004);fine=evaluate(H,rise,.002,True)
        diffs=[abs(a['摆动峰值扭矩_Nm']-b['摆动峰值扭矩_Nm']) for a,b in zip(coarse['关节'],fine['关节'])]
        fine['减半时间步长后峰值扭矩最大变化_Nm']=max(diffs)
        assert max(diffs)<.03,diffs
        results.append(fine)
    bad=evaluate(.245,.18,.004)
    # Check the conservative model's power balance at an arbitrary moving pose.
    masses={'hip_pitch':.32,'upper':.12,'knee_motor':.34,'lower':.115,'foot':.106}
    q=(.1,-.7,1.2);qd=(.4,-.6,.8);qdd=(1.1,.7,-.4);eps=1e-6
    def energy(q,v):
        origins,axes,foot=layout(q);hip,knee=origins[1:];M=point_model(q,masses)[1]
        potential=G*(masses['hip_pitch']*hip[2]+masses['upper']*(hip[2]+knee[2])/2+masses['knee_motor']*knee[2]+masses['lower']*(knee[2]+foot[2])/2+masses['foot']*foot[2])
        return .5*sum(v[i]*M[i][j]*v[j] for i in range(3) for j in range(3))+potential
    qp=tuple(q[i]+qd[i]*eps+.5*qdd[i]*eps**2 for i in range(3));qm=tuple(q[i]-qd[i]*eps+.5*qdd[i]*eps**2 for i in range(3))
    vp=tuple(qd[i]+qdd[i]*eps for i in range(3));vm=tuple(qd[i]-qdd[i]*eps for i in range(3))
    rate=(energy(qp,vp)-energy(qm,vm))/(2*eps);power=dot(torque(q,qd,qdd,masses),qd)
    assert abs(rate-power)<1e-7,(rate,power)
    report={'阶段':'理想点足、固定髋、单脚抬升转移；已采用同一轨迹的位姿/速度/加速度','集中质量模型功率守恒误差_W':abs(rate-power),'工况':results,'180mm阶高且髋高245mm的对照':bad,'限制':['不是四足连续楼梯验证；未求其他三脚反力与整机稳定域','足端参考点简化；没有足垫厚度、足尖尺寸、实体碰撞和防擦余量验证','不含旋转刚体自身惯量、转子反射惯量、摩擦与齿轮损耗','全程F=0，仅算摆动腿，落脚后承重仍使用独立载荷筛查','关节允许范围尚未与最终机构/线束一致，暂以膝150度作为设计观察线','本文件机械功率不是电池功率；不可用其直接确定电源容量']}
    (ROOT/'validation/单脚阶梯转移计算.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    text='# 单脚阶梯转移的连贯轨迹计算\n\n2026-09-05；初步运动学/集中质量动力学，未验证整机连续楼梯。\n\n'
    text+='按同一条抬脚、前移、缓降轨迹计算关节角、转速、角加速度和有符号力矩，避免把不同时刻的速度与扭矩峰值配成一个实际工况。每段使用端点速度和加速度均为零的五次曲线。抬脚0.8s，前移0.8s，落脚0.5s；足参考X从−20mm到130mm，假设阶沿X=40mm、脚参考点越过台阶顶15mm。\n\n'
    text+='| 阶高/髋高 mm | 关节 | 角范围 ° | 最高转速 rpm | 摆动峰值 Nm | 峰值扭矩时转速 rpm | 摆动 RMS Nm |\n|---|---|---:|---:|---:|---:|---:|\n'
    for r in results:
        for j in r['关节']:
            text+=f"| {r['阶高_mm']:.0f}/{r['髋高_mm']:.0f} | {j['关节']} | {j['最小角_deg']:.1f}～{j['最大角_deg']:.1f} | {j['最高转速_rpm']:.1f} | {j['摆动峰值扭矩_Nm']:.3f} | {j['该扭矩时转速_rpm']:.1f} | {j['摆动RMS_Nm']:.3f} |\n"
    text+=f"\n180mm阶高若仍保持245mm髋高，当前点足轨迹的膝最大角达{bad['关节'][2]['最大角_deg']:.1f}°；髋高提高至275mm后减少到{results[1]['关节'][2]['最大角_deg']:.1f}°。这表明上阶前身体高度必须参与规划，不能只抬小腿。这里的150°是观察线，尚未获得最终关节及足端实体全程无碰撞证据。\n\n"
    text+='两种时间步长4ms和2ms的峰值力矩差已记录；IK回代已数值核对。此处扭矩均未乘选型裕量，仅为单腿摆动。支撑腿、翻正、跳跃、地面摩擦、电池功率和温升仍须分别验证；不能据此宣称整机已经能爬180mm楼梯。\n\n'
    text+='方法沿用[Modern Robotics 的速度运动学与静力学](https://modernrobotics.northwestern.edu/nu-gm-book-resource/velocity-kinematics-and-statics/)，集中质量 M、重力和科氏项由现有模型计算。原始采样见 data/单脚150mm阶高转移时序.csv 和 data/单脚180mm阶高转移时序.csv。\n'
    (ROOT/'docs/06_单脚阶梯转移时序计算.md').write_text(text,encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8');main()
