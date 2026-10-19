"""Download observed manufacturer resources and retain source hashes; do not execute archives."""
from pathlib import Path
import urllib.request,urllib.error,hashlib,json,zipfile,subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'vendor/electronics_sources';OUT.mkdir(parents=True,exist_ok=True)
ITEMS=[('2.8寸DSI触控屏_厂家三维.zip','https://www.waveshare.net/w/upload/b/b3/2.8inch_DSI_LCD.zip'),('CM5迷你底板A_厂家三维.zip','https://www.waveshare.net/w/upload/5/50/CM5-NANO-A-3D.zip'),('CM5_官方数据手册.pdf','https://datasheets.raspberrypi.com/cm5/cm5-datasheet.pdf'),('SM105B_C001_厂家规格.pdf','https://www.feetechrc.com/Data/feetechrc/upload/file/20260622/6391773486236271034827287.pdf')]

def fetch(item):
    name,url=item;p=OUT/name;temporary=p.with_suffix(p.suffix+'.download');fallback=False
    try:
        if p.exists():return record(item,p,False)
        total=0
        with urllib.request.urlopen(url,timeout=45) as r, temporary.open('wb') as f:
            while b:=r.read(65536):
                total+=len(b);assert total<=50*1024*1024,'resource exceeds50MiB cap';f.write(b)
    except urllib.error.URLError as exc:
        if 'CERTIFICATE_VERIFY_FAILED' not in str(exc):raise
        fallback=True
        result=subprocess.run(['curl.exe','--fail','--location','--max-time','60','--max-filesize','52428800','--output',str(temporary),url],capture_output=True,text=True)
        assert result.returncode==0,(name,result.stderr[-600:])
    temporary.replace(p)
    return record(item,p,fallback)

def record(item,p,fallback):
    name,url=item
    names=[]
    if p.suffix=='.zip':
        dest=OUT/p.stem;dest.mkdir(exist_ok=True)
        with zipfile.ZipFile(p) as z:
            for info in z.infolist():
                target=(dest/info.filename).resolve();assert target.is_relative_to(dest.resolve()),'archive path outside destination'
                assert info.file_size<=100*1024*1024,'archive member too large'
            z.extractall(dest);names=z.namelist()
    else:assert p.read_bytes().startswith(b'%PDF-')
    row={'文件':str(p),'来源':url,'获取日期':'2026-09-08','SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'字节数':p.stat().st_size,'系统证书库后备下载':fallback,'归档条目':names}
    print(json.dumps(row,ensure_ascii=False),flush=True);return row

if __name__=='__main__':
    rows=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[(item,pool.submit(fetch,item)) for item in ITEMS]
        for item,future in futures:
            try:rows.append(future.result())
            except Exception as exc:
                row={'文件名':item[0],'来源':item[1],'状态':'下载失败','错误':str(exc)};rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
    (OUT/'厂家来源清单.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
