"""Conditional pinhole/entrance-pupil clearance budget, not a camera validation."""
from pathlib import Path
import json,math,csv
ROOT=Path(__file__).resolve().parents[1]
dfov=79.3;w,h=3280,2464;focal=2.85;fnumber=2.0
slope=math.tan(math.radians(dfov/2));entrance_radius=focal/fnumber/2
aperture_radius=8.;offset_budget=.5
hfov=math.degrees(2*math.atan(slope*w/math.hypot(w,h)))
vfov=math.degrees(2*math.atan(slope*h/math.hypot(w,h)))
rows=[]
for pupil_z in (51.2,53,55,57,59,60):
    depth=62.2-pupil_z
    # Highest radial requirement occurs at the outer plane for a straight D16 bore.
    needed=entrance_radius+depth*slope+offset_budget
    rows.append({'假设入瞳Z_mm':pupil_z,'入瞳到面框前面距离_mm':round(depth,3),'含偏心预算所需半径_mm':round(needed,4),'D16半径余量_mm':round(aperture_radius-needed,4),'本假设下是否足够':needed<=aperture_radius})
max_depth=(aperture_radius-entrance_radius-offset_budget)/slope
report={'日期':'2026-09-08','采购候选':'微雪Pi5-IMX219-77，SKU26184；未采购、未冻结','厂家来源':'https://www.waveshare.net/shop/Pi5-IMX219-77.htm','厂家数据':{'对角视场_deg':dfov,'全分辨率':[w,h],'焦距_mm':focal,'光圈F':fnumber,'板外形_mm':[25,24],'镜头外形_mm':[6.5,6.5]},'推导':{'水平视场_deg':hfov,'垂直视场_deg':vfov,'按f除F估计入瞳半径_mm':entrance_radius,'面框前面Z_mm':62.2,'窗口半径_mm':aperture_radius,'假设横向偏心预算_mm':offset_budget,'条件允许最大入瞳后缩_mm':max_depth,'条件入瞳Z下限_mm':62.2-max_depth},'深度敏感性':rows,'边界':['采用直线投影与名义F数推导；实际畸变、入瞳位置/形状、光阑和工作模式可能改变边缘光线','0.5mm偏心是设计预算，未依据公差链验证','目前未取得相机实物入瞳位置、板厚、安装孔坐标、排线插座高度；不能据此画定最终相机托架','只检查面框D16直孔的轴向光学预算；头壳、托架、线缆、镜头筒遮挡须用真实装配另查','25x24板外形满足26x25区域的名义平面余量不代表连接器/螺钉/装配过程都能通过','识别性能、运动模糊、照度及实拍视场尚未测试']}
(ROOT/'validation/相机D16窗口条件预筛.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/相机入瞳后缩敏感性.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(json.dumps(report,ensure_ascii=False,indent=2))
