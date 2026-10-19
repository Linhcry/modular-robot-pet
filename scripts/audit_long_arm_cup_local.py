"""Independent nut/washer fit checks on the successfully translated H11 STEP."""
from occt_head_path_audit import *


def main():
    p=next((ROOT/'exports/step').glob('H11_*'));cup=read_step(p)
    expected=json.loads((ROOT/'validation/长臂螺母杯零件检查.json').read_text(encoding='utf-8'))
    expected=next(r['体积_mm3'] for r in expected if r['编号'].startswith('H11'))
    assert abs(volume(cup)-expected)<1e-5
    maximum=nut();minimum=nut(5.32/math.sqrt(3),2.15)
    washer=BRepAlgoAPI_Cut(BRepPrimAPI_MakeCylinder(3.5,.5).Shape(),BRepPrimAPI_MakeCylinder(1.6,.5).Shape()).Shape()
    rows=[]
    for name,s,z,wz in [('名义螺母松放',maximum,5.6,8),('名义螺母拧紧',maximum,6.2,8.6),
                        ('最小螺母松放',minimum,5.6,8),('最小螺母拧紧',minimum,6.45,8.6)]:
        placed=place(s,(0,0,z));placed_washer=place(washer,(0,0,wz))
        hits={'螺母对杯':overlap(placed,cup),'垫圈对杯':overlap(placed_washer,cup),'螺母对垫圈':overlap(placed,placed_washer)}
        assert not any(hits.values()),(name,hits)
        rows.append({'状态':name,'螺母底Z_mm':z,'垫圈底Z_mm':wz,'交叠':hits})
    faults=[]
    for name,s,z,angles in [('名义螺母',maximum,6.2,(-8,8)),('最小螺母',minimum,6.45,(-12,-8,8,12))]:
        for angle in angles:
            hit=overlap(place(s,(0,0,z),angle),cup)
            expected_hit=name=='名义螺母' or abs(angle)==12
            assert bool(hit)==expected_hit,(name,angle,hit)
            faults.append({'零件':name,'旋转_deg':angle,'预期接触防转壁':expected_hit,'交叠':hit})
    report={'阶段':'H11杯内名义简化包络检查通过','STEP_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),
            'STEP体积_mm3':volume(cup),'SolidWorks记录体积_mm3':expected,'状态检查':rows,'旋转反例':faults,
            '紧固件来源':'按现有建模脚本重建名义包络；最小螺母采用已记录尺寸族AF5.32、厚2.15；不是实购件测量。',
            '边界':['未包含H10头壳，不是头部完整装配或安装路径通过。',
                    '未包含螺母圆角/倒角、表面公差和变形，不构成接触应力、抗扭或保持力通过。',
                    '最小螺母有较大旋转游隙，8度不接触、12度接触；不得据此宣称无间隙防转。'],
            '本进程内存':win32process.GetProcessMemoryInfo(win32api.GetCurrentProcess())}
    (ROOT/'validation/长臂螺母杯_杯内配合独立检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'状态数':len(rows),'旋转反例数':len(faults),'峰值工作集_MiB':report['本进程内存']['PeakWorkingSetSize']/1024**2},ensure_ascii=False))


if __name__=='__main__':
    import sys;sys.stdout.reconfigure(encoding='utf-8');main()
