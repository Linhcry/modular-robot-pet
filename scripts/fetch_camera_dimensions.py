"""Retrieve publicly published mechanical references from the vendor page."""
from pathlib import Path
import re,json,hashlib
from urllib.request import urlopen,Request
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parents[1]
url='https://www.waveshare.net/shop/Pi5-IMX219-77.htm'
text=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read().decode('utf-8')
out=ROOT/'vendor/electronics_sources/Pi5-IMX219-77_尺寸参考';out.mkdir(exist_ok=True)
if 'initAliyunCaptcha' in text or '_waf_is_mobile' in text:
    (out/'响应_未取得产品页.html').write_text(text,encoding='utf-8')
    (out/'产品页资源.json').write_text(json.dumps({'url':url,'status':'未取得产品内容，返回访问验证页','links':[]},ensure_ascii=False,indent=2),encoding='utf-8')
    raise RuntimeError('Vendor returned access verification page; do not treat as mechanical evidence')
(out/'产品页.html').write_text(text,encoding='utf-8')
links=sorted(set(urljoin(url,s) for s in re.findall(r'''(?:src|data-src|href)\s*=\s*["']([^"']+)["']''',text) if 'IMX219' in s))
print('\n'.join(links))
(out/'产品页资源.json').write_text(json.dumps({'url':url,'links':links},ensure_ascii=False,indent=2),encoding='utf-8')
