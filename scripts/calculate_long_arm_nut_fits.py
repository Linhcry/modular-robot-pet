"""Conditional tolerance study tied to saved H10/H11, not a manufacturing release."""
from pathlib import Path
import json, math, hashlib
ROOT=Path(__file__).resolve().parents[1]

def main():
    rows=[]
    for t in (0,.05,.10,.15,.20):
        radial_shift=(9-8.4+2*t)/2
        worst_deflection=1+2*t+radial_shift
        rows.append({'每项塑料尺寸独立误差_mm':t,
                     '直径间隙最小_mm':round(9-8.4-2*t,4),
                     '杯底卸载间隙最小_mm':round(4.6+4.5-5.6-2.4-.5-3*t-.05,4),
                     '偏心后径向扣合量保守最小_mm':round(1-2*t-radial_shift,4),
                     '居中时臂内侧与座侧最小间隙_mm':round(6.9-6.5-2*t,4),
                     '居中时卡槽侧向总间隙最小_mm':round(3-2.4-2*t,4),
                     '卡槽高度与钩高总间隙最小_mm':round(1.8-.8-2*t,4),
                     '假设三项轴向位置误差后的单侧槽间隙_mm':round(.5-3*t,4),
                     '偏心与尺寸误差叠加的挠曲量_mm':round(worst_deflection,4),
                     '简化梁外纤维应变量级':1.5*.6*worst_deflection/6.2**2})
    assert rows[3]['杯底卸载间隙最小_mm']==.1
    assert rows[3]['偏心后径向扣合量保守最小_mm']==.25
    files=['parts/H10_宽槽螺母杯定位曲面头壳.SLDPRT','parts/H11_长臂卡扣螺母防落杯.SLDPRT','scripts/build_tolerant_head_nuts.py']
    hashes={}
    for name in files:
        with (ROOT/name).open('rb') as f:hashes[name]=hashlib.file_digest(f,'sha256').hexdigest()
    report={'依据文件SHA256':hashes,'名义杯底装配Z_mm':37.6,
            '名义尺寸链_mm':{'直径间隙':.6,'杯底卸载间隙':.6,'卡钩径向扣合量':1.,'钩槽轴向总间隙':1.,'杯壁最薄':4.2-5.7/math.sqrt(3)},
            '灵敏度结果':rows,
            '核算边界':['所有误差为条件假设，不代表打印商能力或国标尺寸公差；应向实际供应商确认并以试样量测。',
                    '间隙计算不包含完整形位误差；正值不能代替插入路径、卡扣保持力或制造检验。',
                    '长臂增加有效长度，但加深扣合也增加装入挠曲；应变结果仅线性悬臂梁数量级，未证明材料通过。',
                    '螺母最小对边的防转游隙仍约8.11度；需按实际采购螺母检查防转接触和局部压应力。',
                    '头壳及杯都已保存为原生零件；安装路径检查被内存门限停止，尚无通过结论。']}
    (ROOT/'validation/长臂螺母杯尺寸链核算.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'名义':report['名义尺寸链_mm'],'条件误差0.15':rows[3]},ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys;sys.stdout.reconfigure(encoding='utf-8');main()
