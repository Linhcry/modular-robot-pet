"""可复算的初步关节载荷筛选；不是完整逆动力学或电机最终验收。仅使用标准库。"""
from pathlib import Path
import csv, json, math

ROOT=Path(__file__).resolve().parents[1]
G=9.80665
L1=L2=.145
HIP_OFFSET=.05
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def scale(a,s):return tuple(x*s for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def rx(v,a):return (v[0],math.cos(a)*v[1]-math.sin(a)*v[2],math.sin(a)*v[1]+math.cos(a)*v[2])
def layout(q):
    r,h,k=q
    hip=rx((0,HIP_OFFSET,0),r)
    knee=add(hip,rx((L1*math.sin(h),0,-L1*math.cos(h)),r))
    foot=add(knee,rx((L2*math.sin(h+k),0,-L2*math.cos(h+k)),r))
    # h/k positive angles use rotation about negative Y.
    return [(0,0,0),hip,knee],[(1,0,0),rx((0,-1,0),r),rx((0,-1,0),r)],foot
def jacobian(q):
    origins,axes,foot=layout(q)
    return [cross(a,sub(foot,o)) for o,a in zip(origins,axes)]
def csvout(name,rows):
    with (ROOT/'data'/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def mass_budget():
    measured=json.loads((ROOT/'validation/零件体积与质量假设.json').read_text(encoding='utf-8'))
    byid={r['编号']:r for r in measured}
    # Intended instance counts for the current architecture, not an assembled BOM.
    groups={
      '框架':{'F01_Belly':1,'F02_Deck':1,'F03_SideRail':2,'F04_Bulkhead':2,'F05_BatteryTray':1,'F06_CoreTray':1,'F07_CompressionSleeve':12,'F08_CoreStandoff':4,'F09_ArmPedestal':1},
      '四腿结构':{'J03_HipYoke':4,'L01_UpperLink':4,'L02_LowerLink':4,'L03_FootMount':4,'L04_FootPad':4,'J05_AK4510StatorAdapter':8,'J06_AK4510OutputAdapter':8},
      '储物与快拆':{'C01_CargoShell':1,'C02_Lid':1,'C03_Tray':1,'C04_HingeLeaf':2,'C05_MovingHinge':2,'C06_HingePin':2,'Q01_Rail':2,'Q02_Shoe':2,'Q03_PinSeat':1,'Q04_PullPin':1},
      '臂头尾结构':{'A01_ArmLink':2,'A02_GripperPalm':1,'A03_Finger':2,'A04_FingerPad':2,'H01_HeadShell':1,'H02_Faceplate':1,'T01_Tail':1}}
    rows=[]
    for group,parts in groups.items():
        for code,qty in parts.items():
            p=byid[code];unit=p['估计单件质量_g']
            rows.append({'分组':group,'项目':p['名称'],'数量':qty,'单件质量_g':unit,'合计质量_g':qty*unit,'证据':'SW实体体积×材料假设；数量为拟装数量，未完成总装'})
    allowances=[('腿部电机','AK45-10候选完整模组',8,260,'厂家标称完整模组；参考零件V01/V02不重复计重'),('腿部电机','AK45-36候选完整模组',4,340,'厂家标称；接口尚未设计'),('未建接口','膝关节转换及轴向支撑',4,70,'工程质量预留，非实测'),('小型驱动','臂腰肩肘腕及夹爪驱动',1,650,'初步质量预留；选型后替换'),('小型驱动','头尾与舱盖驱动',1,200,'初步质量预留；选型后替换'),('电源控制','电池及电源保护',1,550,'初步质量预留；额定电压/容量待选'),('电源控制','算力相机音频控制板',1,250,'初步质量预留'),('线束外壳','线束连接器及全机紧固件',1,300,'预留全部紧固件，不再叠加单颗螺钉质量'),('线束外壳','全机躯干关节护罩',1,350,'未建外壳质量预算')]
    for group,name,qty,unit,evidence in allowances:rows.append({'分组':group,'项目':name,'数量':qty,'单件质量_g':unit,'合计质量_g':qty*unit,'证据':evidence})
    csvout('当前架构质量估算.csv',rows)
    return sum(x['合计质量_g'] for x in rows)/1000,rows

def point_model(q,leg_mass):
    origins,axes,foot=layout(q);hip,knee=origins[1:]
    # Concentrated mass approximation; distributed inertia and rotor inertia remain separate.
    points=[(leg_mass['hip_pitch'],hip,0),(leg_mass['upper'],scale(add(hip,knee),.5),1),(leg_mass['knee_motor'],knee,1),(leg_mass['lower'],scale(add(knee,foot),.5),2),(leg_mass['foot'],foot,2)]
    grav=[0.,0.,0.];M=[[0.]*3 for _ in range(3)]
    for mass,pt,last in points:
        J=[cross(axes[j],sub(pt,origins[j])) if j<=last else (0,0,0) for j in range(3)]
        for j in range(last+1):
            arm=sub(pt,origins[j]);grav[j]+=abs(dot(axes[j],cross(arm,(0,0,-mass*G))))
            for k in range(last+1):M[j][k]+=mass*dot(J[j],J[k])
    return grav,M

def leg_load(q,force,accel,velocity,leg_mass):
    force_tau=[abs(dot(c,force)) for c in jacobian(q)]
    grav,M=point_model(q,leg_mass)
    acceleration=[sum(abs(M[j][k]*accel[k]) for k in range(3)) for j in range(3)]
    dM=[]
    for k in range(3):
        qp=list(q);qm=list(q);qp[k]+=1e-5;qm[k]-=1e-5
        mp=point_model(qp,leg_mass)[1];mm=point_model(qm,leg_mass)[1]
        dM.append([[(mp[i][j]-mm[i][j])/2e-5 for j in range(3)] for i in range(3)])
    # Christoffel terms; evaluate all velocity direction combinations of the specified magnitudes.
    coriolis=[0.,0.,0.]
    for mask in range(8):
        v=[velocity[j]*(1 if mask&(1<<j) else -1) for j in range(3)]
        for i in range(3):
            c=sum(.5*(dM[k][i][j]+dM[j][i][k]-dM[i][j][k])*v[j]*v[k] for j in range(3) for k in range(3))
            coriolis[i]=max(coriolis[i],abs(c))
    return force_tau,grav,[M[j][j] for j in range(3)],acceleration,coriolis,[force_tau[j]+grav[j]+acceleration[j]+coriolis[j] for j in range(3)]

def checks():
    worst=0
    for q in [(0,.3,-.6),(.3,-.8,1.5),(-.4,.7,.4)]:
        J=jacobian(q)
        for j in range(3):
            qp=list(q);qm=list(q);qp[j]+=1e-6;qm[j]-=1e-6
            fd=scale(sub(layout(qp)[2],layout(qm)[2]),1/(2e-6))
            worst=max(worst,max(abs(a-b) for a,b in zip(fd,J[j])))
    assert worst<1e-8
    # Vertical straight leg has no hip/knee pitch torque from vertical force; roll is F*offset.
    t=[dot(c,(0,0,20)) for c in jacobian((0,0,0))]
    assert abs(t[0]-1)<1e-12 and abs(t[1])+abs(t[2])<1e-12
    # Bent symmetric stance: hip pitch cancels, knee torque is F*L2*sin(30deg).
    t=[dot(c,(0,0,20)) for c in jacobian((0,math.radians(-30),math.radians(60)))]
    assert abs(t[1])<1e-12 and abs(abs(t[2])-20*L2*.5)<1e-12
    return {'雅可比与中心差分最大误差_m_rad':worst,'直腿静力手算校验':True,'屈腿静力手算校验':True}

def main():
    measured_mass,massrows=mass_budget()
    # force = mass*g*dynamic_factor*share. Horizontal force ratios are explicit assumptions.
    cases=[
      ('四脚安静站立',(0,-25,50),1,.25,0,0,(0,0,0),(0,0,0),30,'姿态停留；四脚均分'),
      ('三脚慢走承重',(5,-35,70),1.2,.40,.12,.05,(2,5,6),(5,12,15),12,'单脚40%载荷用于不均匀三脚支撑'),
      ('伸爪时三脚支撑',(8,-40,80),1.1,.45,.05,.1,(1,3,3),(3,8,8),8,'先移重心；并非任意单脚站立'),
      ('低姿爬行',(5,-65,120),1.15,.40,.1,.05,(2,4,6),(5,10,15),8,'深屈膝重载'),
      ('爬阶后腿推升',(5,-25,90),1.4,.55,.15,.05,(2,5,7),(5,15,20),5,'150–180mm阶高目标中的载荷筛选姿态；未证明连续楼梯可达'),
      ('受控对角小跑',(6,-40,80),1.8,.55,.18,.08,(5,12,16),(20,45,60),4,'对角两脚支撑且载荷不等'),
      ('四脚小跳起蹬',(0,-50,100),2.5,.30,.1,0,(4,14,18),(15,60,70),.15,'起跳峰值仅列边界；电源峰值与台架待核'),
      ('四脚有缓冲落地',(5,-50,100),3,.40,.12,.08,(4,14,18),(20,65,80),.1,'需足垫和屈腿缓冲控制约束，不是任意摔落'),
      ('单脚误着地边界',(8,-50,100),3,1,.15,.1,(4,14,18),(20,65,80),.05,'故障工况；不作为可反复执行动作')]
    leg_mass={'hip_pitch':.32,'upper':.12,'knee_motor':.34,'lower':.115,'foot':.106}
    out=[]
    for mass,label in [(5.3,'5kg本体+300g负载目标'),(measured_mass+.3,'当前架构估重+300g'),(7.3,'7kg本体敏感性')]:
        for name,angles,df,share,fx,fy,vel,alpha,duration,notes in cases:
            q=tuple(map(math.radians,angles));fz=mass*G*df*share;force=(fx*fz,fy*fz,fz)
            ext,grav,I,dyn,cor,req=leg_load(q,force,alpha,vel,leg_mass)
            for j,jn in enumerate(('髋外展','髋俯仰','膝俯仰')):
                out.append({'质量场景':label,'满载质量_kg':round(mass,4),'工况':name,'关节':jn,'角度_deg':angles[j],'单脚Fz_N':round(fz,4),'Fx_Fz':fx,'Fy_Fz':fy,'地面力矩_Nm':round(ext[j],4),'腿重附加上界_Nm':round(grav[j],4),'点质量惯量_kgm2':round(I[j],6),'集中质量加速上界_Nm':round(dyn[j],4),'集中质量科氏离心项_Nm':round(cor[j],4),'未乘裕量需求_Nm':round(req[j],4),'筛选裕量':1.25,'筛选需求_Nm':round(1.25*req[j],4),'转速需求_rpm':round(abs(vel[j])*60/(2*math.pi),2),'工况持续_s':duration,'说明':notes})
    csvout('腿部电机工况计算.csv',out)
    # One 60-second screening cycle uses explicitly defined dwell times; every row is a conservative magnitude.
    duty={'四脚安静站立':30,'三脚慢走承重':12,'伸爪时三脚支撑':8,'低姿爬行':5,'爬阶后腿推升':5}
    rms=[]
    for mass,label in [(5.3,'5kg本体+300g负载目标'),(measured_mass+.3,'当前架构估重+300g'),(7.3,'7kg本体敏感性')]:
        for jn in ('髋外展','髋俯仰','膝俯仰'):
            rr=[r for r in out if r['质量场景']==label and r['关节']==jn and r['工况'] in duty]
            t=math.sqrt(sum(r['筛选需求_Nm']**2*duty[r['工况']] for r in rr)/60)
            rms.append({'质量场景':label,'关节':jn,'含1.25裕量等效RMS_Nm':round(t,4),'周期_s':60,'备注':'筛选载荷谱；非实测RMS。还须加反射转子惯量、摩擦/耦合及按壳内散热修正'})
    csvout('腿部连续力矩筛选.csv',rms)
    # Horizontal extended arm; worst gravity leverage. Gear efficiency only belongs to any ADDED transmission.
    mlink=.06842;elbow=.185;wrist=.12;gripper=.16;payload=.3;reach=.24
    shoulder_g=G*(mlink*.06+elbow*.12+mlink*.18+(wrist+gripper+payload)*reach)
    elbow_g=G*(mlink*.06+(wrist+gripper+payload)*.12)
    shoulder_I=mlink*.12**2/3+elbow*.12**2+mlink*(.12**2+.12*.12+.12**2/3)+(wrist+gripper+payload)*reach**2
    elbow_I=mlink*.12**2/3+(wrist+gripper+payload)*.12**2
    aux=[{'关节':'臂肩俯仰','重力_Nm':shoulder_g,'惯量_kgm2':shoulder_I,'角加速度_rad_s2':4,'摩擦预留_Nm':.08,'条件':'双120mm连杆水平伸展；300g负载；腕120g，夹爪160g，肘电机185g'},
         {'关节':'臂肘俯仰','重力_Nm':elbow_g,'惯量_kgm2':elbow_I,'角加速度_rad_s2':5,'摩擦预留_Nm':.05,'条件':'前臂120mm水平伸展；同上末端负载'},
         {'关节':'腕俯仰','重力_Nm':G*(gripper*.035+payload*.06),'惯量_kgm2':gripper*.035**2+payload*.06**2,'角加速度_rad_s2':5,'摩擦预留_Nm':.03,'条件':'货物质心距腕60mm；尺寸增长须重算'},
         {'关节':'头部俯仰','重力_Nm':G*.22*.04,'惯量_kgm2':.22*.05**2,'角加速度_rad_s2':8,'摩擦预留_Nm':.03,'条件':'头部总成220g；质心距轴40mm'},
         {'关节':'舱盖开启','重力_Nm':G*.08*.065,'惯量_kgm2':.08*.13**2/3,'角加速度_rad_s2':4,'摩擦预留_Nm':.025,'条件':'盖含铰链80g；长度130mm；不含锁扣释放力'},
         {'关节':'尾部摆动','重力_Nm':0.,'惯量_kgm2':.035*.14**2/3,'角加速度_rad_s2':20,'摩擦预留_Nm':.02,'条件':'尾部35g、140mm；竖直摆轴；不用于翻正支撑'}]
    for r in aux:r['含1.5裕量筛选需求_Nm']=1.5*(r['重力_Nm']+r['惯量_kgm2']*r['角加速度_rad_s2']+r['摩擦预留_Nm'])
    csvout('辅助关节载荷计算.csv',aux)
    grip={'负载_kg':payload,'假设最小摩擦系数':.3,'加速度_m_s2':2,'抗滑安全系数':2,'每指最小法向力_N':2*payload*(G+2)/(2*.3),'指力臂_m':.04,'传动效率假设':.7}
    grip['双指合计驱动轴扭矩筛选_Nm']=2*grip['每指最小法向力_N']*.04/.7
    result={'阶段':'P1初步载荷筛选；所有输入可追踪，未声称完整动力学或热验证','当前拟装架构估计本体质量_kg':measured_mass,'目标本体质量_kg':[4,5],'目标差额相对5kg_kg':measured_mass-5,'RMS':rms,'辅助关节':aux,'夹爪抗滑初算':grip,'数值校验':checks(),'未覆盖':['完整M(q)qdd+C(q,qd)qd逆动力学','电机反射惯量及内部减速摩擦','扭矩-转速-电压联合曲线','峰值允许时间与壳内温升','轴承径向轴向载荷寿命','连续楼梯稳定域与接触摩擦','跌倒翻正的壳体接触与动作轨迹','减重结构刚度/疲劳/制造验证']}
    (ROOT/'validation/电机载荷初算.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8');main()
