"""Print bounded, located evidence for manual review; this does not mark a source reviewed."""
from pathlib import Path
import re,sys,json
root=Path(__file__).resolve().parents[1]/'research/primary_sources'
sys.stdout.reconfigure(encoding='utf-8')
for arg in sys.argv[1:]:
    ident,pattern=arg.split('=',1)
    text=(root/(ident+'.txt')).read_text(encoding='utf-8')
    matches=list(re.finditer(pattern,text,re.I))
    selected=[]
    for m in matches:
        if any(abs(m.start()-p)<1200 for p in selected):continue
        selected.append(m.start())
        if len(selected)==2:break
    print(json.dumps({'编号':ident,'定位表达式':pattern,'片段':[{'字符起点':max(0,p-100),'文本':text[max(0,p-100):p+1500]} for p in selected]},ensure_ascii=False))
