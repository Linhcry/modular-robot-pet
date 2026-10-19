"""Compare independently saved candidates against a preserved mass baseline."""
from size_actuators import ROOT,csvout,mass_budget
import json

def main():
    total,rows=mass_budget()
    old={r['编号']:r for r in json.loads((ROOT/'validation/零件体积与质量假设.json').read_text(encoding='utf-8'))}
    new={r['编号']:r for r in json.loads((ROOT/'validation/减重框架与护壳检查.json').read_text(encoding='utf-8'))}
    shoe=json.loads((ROOT/'validation/分体短滑靴检查.json').read_text(encoding='utf-8'))
    changes=[]
    for prior,replacement in [('F01_Belly','F10_LightBelly'),('F02_Deck','F11_LightDeck')]:
        changes.append({'变更':old[prior]['名称']+' → '+new[replacement]['名称'],'原估重_g':old[prior]['估计单件质量_g'],'候选估重_g':new[replacement]['估计质量_g'],'说明':'实体体积×相同材料假设；刚度和装配待校核'})
    changes.append({'变更':'两条312长侧梁 → 两条300长避空侧梁','原估重_g':2*old['F03_SideRail']['估计单件质量_g'],'候选估重_g':2*new['F12_ShortSideRail']['估计质量_g'],'说明':'端部缩短各6mm；孔端距8mm；载荷与连接强度待校核'})
    changes.append({'变更':'两条长滑靴 → 四个短滑靴','原估重_g':old['Q02_Shoe']['估计单件质量_g']*2,'候选估重_g':shoe['估计四件质量_g'],'说明':'同导向截面；连接保持能力待校核'})
    covermass=new['B01_LowerBody']['估计质量_g']+new['B02_UpperBody']['估计质量_g']+4*new['B03_JointCover']['估计质量_g']
    changes.append({'变更':'躯干护罩预算 → 两片机身壳+四个关节护罩','原估重_g':350,'候选估重_g':covermass,'说明':'仅计4个护罩；数量最终确定后重算，不代表12个关节均被覆盖'})
    for r in changes:r['减重_g']=r['原估重_g']-r['候选估重_g']
    updated=total-sum(r['减重_g'] for r in changes)/1000
    csvout('减重候选质量对比.csv',changes)
    allocated=[('12台腿部驱动总成',2100),('全部腿结构及传动支承',650),('机身承载框架及模块接口',450),('机械臂与夹爪含全部驱动',650),('头尾储物舱含驱动',300),('电池与电源保护',350),('算力视觉音频',200),('护壳',180),('线束与全机紧固件',120)]
    assert sum(m for _,m in allocated)==5000
    allocation=[{'分系统':n,'5kg目标分配_g':m,'状态':'反推质量上限；非已选件质量；允许经系统评审在分项间调配'} for n,m in allocated]
    csvout('5kg质量目标反推.csv',allocation)
    hard_items=[r for r in rows if r['分组'] in ('腿部电机','小型驱动','电源控制') or r['项目']=='线束连接器及全机紧固件']
    hardware_floor=sum(r['合计质量_g'] for r in hard_items)/1000
    report={'原架构估计本体_kg':total,'局部候选代入估计本体_kg':updated,'局部净减重_g':(total-updated)*1000,'相对5kg仍超重_kg':updated-5,'现有电机电子电池线束不含结构的估计下界_kg':hardware_floor,'12腿电机质量_g':3440,'腿驱动目标平均每台_g':2100/12,'候选代入条件':'仅质量敏感性；空间配合、结构等刚度和制造验证尚未全部通过','变更':changes,'目标分配':allocation}
    (ROOT/'validation/减重候选质量决策.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    md=f'''# 减重候选与质量分配

日期：2026-09-05。保留原架构基线，不把独立候选当作已经完成的整机。

将 F10、F11、两件 F12、四件 Q05 代入，再用实际生成的两片机身壳和四件关节罩替换原来350g护罩预算，本体估计由 **{total:.3f}kg** 变为 **{updated:.3f}kg**，净减重约 **{(total-updated)*1000:.1f}g**，距5kg仍差 **{updated-5:.3f}kg**。这些质量来自原生实体体积、拟装数量和材料假设，并非称重结果或装配体质量属性。

| 变更 | 原估重g | 候选估重g | 减重g |
|---|---:|---:|---:|
'''
    for r in changes:md+=f"| {r['变更']} | {r['原估重_g']:.1f} | {r['候选估重_g']:.1f} | {r['减重_g']:.1f} |\n"
    md+=f'''
现有腿电机、辅助驱动、电池电子及线束紧固件的预留合计已约 **{hardware_floor:.3f}kg**，尚未计入承载框架、四腿杆件、储物舱或机身壳。因此，继续给现有板件开孔不可能独自解决5kg目标；必须重做驱动和结构的一体化方案。

## 下一步设计门槛

1. 暂停冻结现有 AK45 接口为整机最终接口。按当前质量构成，12台完整驱动共3.44kg；目标分配暂为2.10kg，即平均175g/台。这是反推上限，不是已经找到满足力矩与寿命的电机。
2. 保留三轴腿和拾取机械臂任务。比较近髋膝驱动、共用轴承支承、连杆端与输出盘合并等拓扑，把新增传动件、损耗、预紧与维护空间一并计入。
3. 壳体预算需同时保留壁厚、局部连接柱和耐碰能力；不能把当前2.2mm壁厚按质量比例直接缩到不到1mm。
4. 对每个候选先计算慢走与爬阶的连贯轨迹，再核对扭矩—转速—峰值持续时间—散热。大工程师具体规格及模型未取得的候选不能定型。
5. 目标仍为本体4–5kg，另加300g载物。本报告不自动放宽目标、不触发采购。

## 5kg分系统目标

| 分系统 | 分配g |
|---|---:|
'''
    for name,m in allocated:md+=f'| {name} | {m} |\n'
    md+='\n分项均为设计约束，尚无完整BOM满足；可在总额内调配。模型、质量表和载荷表一致后，才能作为进入加工或采购阶段的依据。\n'
    (ROOT/'docs/05_减重候选与质量分配.md').write_text(md,encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8');main()
