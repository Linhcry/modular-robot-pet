"""Verify reconstruction only changes the two missing references and adds their curves."""
from pathlib import Path
import re,json,math,hashlib
ROOT=Path(__file__).resolve().parents[1]
TOKEN=re.compile(r"'(?:[^']|'')*'|#\d+|\.[A-Z_]+\.|[A-Z_][A-Z_0-9]*|[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:E[+-]?\d+)?|[(),$*]",re.I)

def main():
    paths=[next((ROOT/'exports/step').glob('H10_*')),next((ROOT/'wip/STEP修复候选').glob('H10_*_保留原始实体号.STEP'))]
    data=[dict(re.findall(r'#(\d+)\s*=\s*(.*?);',p.read_text(encoding='latin1'),re.S)) for p in paths]
    old,new=data;assert old.keys()<=new.keys()
    errors=[];max_numeric_delta=0
    expected={'19964','50188'}
    for key,value in old.items():
        a=TOKEN.findall(value);b=TOKEN.findall(new[key])
        if key in expected:
            differing=[(i,x,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y]
            assert len(a)==len(b) and len(differing)==1,(key,differing)
            _,before,after=differing[0]
            assert before=='$' and after.startswith('#') and after[1:] not in old,(key,differing)
            continue
        if len(a)!=len(b):errors.append({'实体':key,'原因':'token count changed'});continue
        for x,y in zip(a,b):
            if x==y:continue
            try:
                delta=abs(float(x)-float(y));max_numeric_delta=max(max_numeric_delta,delta)
                assert delta<1e-10
            except (ValueError,AssertionError):errors.append({'实体':key,'原值':x,'候选值':y})
    report={'原文件SHA256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),
            '候选SHA256':hashlib.sha256(paths[1].read_bytes()).hexdigest(),
            '原实体数':len(old),'候选实体数':len(new),'预期修改边':sorted(expected),
            '其他实体最大数值重写差':max_numeric_delta,'其他结构修改':errors,
            '说明':'只证明STEP实体定义变化范围；不代替原生几何、体积和装配验证。'}
    (ROOT/'validation/头壳STEP修复实体差异检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'原实体数':len(old),'候选实体数':len(new),'差异数':len(errors),'前3条':errors[:3]},ensure_ascii=False,indent=2));assert not errors

if __name__=='__main__':
    import sys;sys.stdout.reconfigure(encoding='utf-8');main()
