"""Nominal beam screening; no yield/fatigue or full-deck acceptance claim."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
# Deliberately omit the dovetail above the 2 mm base, and use the clearance-hole net width.
E=69000.0  # N/mm², aluminium modulus assumption; actual alloy/condition remains to be frozen.
b=20-3.4;t=2.;I=b*t**3/12
rows=[]
for force in (1,25,100):
    rows.append({'单轨集中力_N':force,'50mm简支跨中名义应力_MPa':force*50/4*(t/2)/I,
                 '50mm简支跨中挠度_mm':force*50**3/(48*E*I),
                 '15mm端悬臂根部名义应力_MPa':force*15*(t/2)/I,
                 '15mm端悬臂末端挠度_mm':force*15**3/(3*E*I)})
result={'截面假设':{'剩余底带宽_mm':b,'厚_mm':t,'惯性矩_mm4':I,'弹性模量假设_MPa':E},
        '工况':rows,'荷载含义':'1N为单位响应；25N和100N为透明的筛选载荷，不是已确定的整机工况。',
        '边界':['只计算单根导轨底带的线弹性名义梁响应，省略上部燕尾截面刚度','50mm为垫块中心距，15mm为端部至最近支承中心的距离','假定垫块和承载板不变形；真实薄板支承柔度未纳入','孔边应力集中、局部承压、螺栓预紧和轨靴接触未建模','不能据此称为结构强度通过；需整合全舱质量、运动加速度、偏载和实际材料许用值','滑出过程中接触长度减少，需清空载荷并手托模块；梁模型不能证明滑出过程稳定','F13的外侧减重窗使导轨载荷需经两端及周边板带传至侧梁；整块上板的弯扭刚度必须另行校核']}
(root/'validation/导轨跨距名义梁初算.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
