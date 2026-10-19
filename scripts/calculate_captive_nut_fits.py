"""Small, deterministic dimension-chain study; no CAD or model imports."""
from pathlib import Path
import hashlib
import json
import math
import csv

ROOT = Path(__file__).resolve().parents[1]


def rotation_slack(nut_af, pocket_af):
    # For centered regular hexagons, each pocket flat must clear the nut vertex.
    ratio = pocket_af * math.sqrt(3) / (2 * nut_af)
    return 30.0 if ratio >= 1 else 30 - math.degrees(math.acos(ratio))


def evaluate(t, floor=4.0):
    # t is a conditional independent +/- error on each specified plastic size,
    # NOT a claimed printing capability or a GB/T tolerance.
    nut_max, washer_nom, washer_error = 2.4, .5, .05
    nominal_gap = 4.6 + 2.5 - floor - nut_max - washer_nom
    return {'假设每项塑料尺寸误差_mm': t,
            '直径间隙最小_mm': round(8.6 - 8.4 - 2*t, 4),
            '螺母槽对边间隙最小_mm': round(5.7 - t - 5.5, 4),
            '杯底卸载间隙最小_mm': round(nominal_gap - 3*t - washer_error, 4),
            '卡槽与钩轴向总间隙最小_mm': round(1.0 - .8 - 2*t, 4),
            '偏心前扣合量最小_mm': round(.3 - 2*t, 4),
            '最大直径间隙对应径向偏移_mm': round((.2 + 2*t)/2, 4)}


def main():
    paths = [ROOT/'scripts/build_captive_head_nuts.py',
             ROOT/'parts/H08_螺母杯定位曲面头壳.SLDPRT',
             ROOT/'parts/H09_卡扣式螺母杯防落底盖.SLDPRT',
             ROOT/'validation/头部紧固件国标与装配清单核对.json']
    hashes = {str(p.relative_to(ROOT)): hashlib.file_digest(p.open('rb'), 'sha256').hexdigest() for p in paths}
    rows = [evaluate(t) for t in (0, .05, .10, .15, .20)]
    # Independent checks at nominal and adverse corners.
    assert rows[0]['直径间隙最小_mm'] == .2
    assert rows[0]['杯底卸载间隙最小_mm'] == .15  # includes conditional +.05 washer error
    assert rows[2]['杯底卸载间隙最小_mm'] == -.15
    assert rows[3]['直径间隙最小_mm'] == -.1
    assert rotation_slack(5.32, 5.7) > 8
    revised = evaluate(.15, floor=3.6)
    assert revised['杯底卸载间隙最小_mm'] == .1
    report = {
        '来源文件SHA256': hashes,
        '方法': '独立区间最坏端点叠加；单位mm。t为灵敏度假设，不是打印商能力、国标公差或制造放行值。',
        '名义尺寸链': {
            '定位孔直径': 8.6, '杯外径': 8.4, '直径间隙': .2,
            '杯底卸载间隙表达式': '(环肩底面46.7-定位座底面42.1)+止挡柱顶2.5-杯内底4.0-螺母2.4-垫圈0.5=0.2',
            '钩与槽轴向间隙': 1.0-.8,
            '钩名义径向扣合量': 5.5-5.2,
            '说明': '杯底卸载间隙>0才支持杯底不进入主夹紧载荷路径；此条件不证明其他部位没有意外承压。'},
        '灵敏度结果': rows,
        '螺母居中时单向旋转游隙_deg': {
            '对边5.50_槽5.70': rotation_slack(5.5, 5.7),
            '对边5.32_槽5.70': rotation_slack(5.32, 5.7),
            '限制': '理想二维正六边形；未计螺母倒角、圆角和局部接触变形。最小对边螺母的8度试探不足以证明防转接触。'},
        '发现': [
            '现有D8.6/D8.4只留0.2直径间隙；不能直接假设普通未修整打印件必然能插入。',
            '杯底名义0.2卸载间隙，在各塑料功能尺寸独立±0.10、垫圈厚度±0.05的条件下最坏为-0.15，杯底可能进入夹紧路径。',
            '1.0高卡槽和0.8高卡钩也只有0.2轴向总间隙，需要检查相对位置误差，不能只查外形无干涉。',
            '径向扣合0.3还要扣除径向偏移和制造误差；不能直接把名义交叠视为可靠防脱。',
            '原8度螺母防转几何反例仅针对当前最大包络模型，不能覆盖最小对边5.32的实购螺母。'],
        '下一版候选_尚未建模': {
            '杯内底高度': 3.6, '杯口高度': 6.0,
            '理由': '杯内底和杯口一起降低0.4，保留2.4深六角槽及松放垫圈入口；名义卸载间隙增至0.6。',
            '条件计算': revised,
            '未解决': '该变化只改善杯底卸载尺寸链；定位孔装入、卡扣公差、强度和工具释放空间仍需设计与验证。'},
        '制造状态': '保留现有H08/H09为名义几何候选；未制造放行，未宣称卡扣保持力或装配可靠性通过。'}
    (ROOT/'validation/螺母杯尺寸链与公差敏感性.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    with (ROOT/'data/螺母杯配合公差敏感性.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps({'发现': report['发现'], '螺母旋转游隙':report['螺母居中时单向旋转游隙_deg'], '降低杯底候选':revised}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
