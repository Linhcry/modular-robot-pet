"""Fetch public primary-source text/PDF only. A successful fetch is NOT a completed study."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from html.parser import HTMLParser
import urllib.request,hashlib,json,re,sys,time,subprocess,datetime
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'research/primary_sources';DEST.mkdir(parents=True,exist_ok=True)
SOURCES=[
('Stanford Doggo','四足','https://github.com/Nate711/StanfordDoggoProject','https://raw.githubusercontent.com/Nate711/StanfordDoggoProject/master/README.md'),
('Pupper V3','四足','https://pupper-v3-documentation.readthedocs.io/en/latest/learn_more/tech_specs.html',''),
('Solo / ODRI早期八自由度','四足','https://arxiv.org/abs/1910.00093','https://arxiv.org/pdf/1910.00093'),
('Dingo','四足','https://github.com/Yerbert/DingoCAD','https://raw.githubusercontent.com/Yerbert/DingoCAD/main/README.md'),
('Mini Pupper','四足','https://mangdangroboticsclub.github.io/MiniPupperDocs/en/guide/Features.html',''),
('Petoi Bittle','四足','https://www.petoi.com/products/petoi-bittle-robot-dog',''),
('HyperDog','四足','https://arxiv.org/abs/2209.09171','https://arxiv.org/pdf/2209.09171'),
('MIT Mini Cheetah','四足','https://news.mit.edu/2019/mit-mini-cheetah-first-four-legged-robot-to-backflip-0304',''),
('MEVIUS2','四足','https://haraduka.github.io/mevius2-hardware/assets/paper.pdf',''),
('Unitree Go2','四足','https://www.unitree.com/go2/',''),
('ANYmal D','四足','https://www.anybotics.com/anymal-technical-specifications.pdf',''),
('Boston Dynamics Spot','四足','https://dev.bostondynamics.com/docs/concepts/about_spot',''),
('Ascento','轮腿','https://arxiv.org/abs/2005.11435','https://arxiv.org/pdf/2005.11435'),
('Wheelbot','轮式平衡','https://arxiv.org/abs/2207.06988','https://arxiv.org/pdf/2207.06988'),
('Cassie','双足','https://github.com/agilityrobotics/cassie-doc/wiki','https://raw.githubusercontent.com/wiki/agilityrobotics/cassie-doc/Home.md'),
('ToddlerBot','人形','https://arxiv.org/abs/2502.00893','https://arxiv.org/pdf/2502.00893'),
('Berkeley Humanoid Lite','人形','https://github.com/HybridRobotics/Berkeley-Humanoid-Lite','https://raw.githubusercontent.com/HybridRobotics/Berkeley-Humanoid-Lite/master/README.md'),
('BRUCE 双足','双足','https://wiki.bruce-op.com/index.php/Main_Page',''),
('Open Duck Mini v2','双足宠物','https://github.com/apirrone/Open_Duck_Mini/tree/v2','https://raw.githubusercontent.com/apirrone/Open_Duck_Mini/v2/README.md'),
('ROBOTIS OP3','人形','https://emanual.robotis.com/docs/en/platform/op3/introduction/',''),
('Poppy Humanoid','人形','https://flowers.inria.fr/PoppyHumanoids2014.pdf',''),
('igus Humanoid Open Platform','人形','https://arxiv.org/abs/1809.11110','https://arxiv.org/pdf/1809.11110'),
('Reachy 2','人形操作','https://docs.pollen-robotics.com/hardware-guide/specifications/general/',''),
('Unitree G1','人形','https://www.unitree.com/g1/',''),
('SO-101','机械臂','https://github.com/TheRobotStudio/SO-ARM100','https://raw.githubusercontent.com/TheRobotStudio/SO-ARM100/main/README.md'),
('ALOHA','双臂操作','https://tonyzhaozh.github.io/aloha/',''),
('OpenMANIPULATOR-X','机械臂','https://emanual.robotis.com/docs/en/platform/openmanipulator_x/specification/',''),
('PAROL6','机械臂','https://github.com/Source-Robotics/PAROL6-Desktop-robot-arm','https://raw.githubusercontent.com/Source-Robotics/PAROL6-Desktop-robot-arm/main/README.md'),
('Thor','机械臂','https://github.com/AngelLM/Thor','https://raw.githubusercontent.com/AngelLM/Thor/main/README.md'),
('BCN3D Moveo','机械臂','https://github.com/BCN3D/BCN3D-Moveo','https://raw.githubusercontent.com/BCN3D/BCN3D-Moveo/master/README.md'),
('Annin AR4','机械臂','https://anninrobotics.com/docs/what-are-the-dimensions-and-key-specifications-of-the-ar4-robot/',''),
('MeArm','机械臂','https://github.com/MeArm/MeArm','https://raw.githubusercontent.com/MeArm/MeArm/master/README.md'),
('UFACTORY Lite 6','机械臂','https://www.ufactory.us/product/lite-6',''),
('OpenArm','机械臂','https://github.com/enactic/openarm','https://raw.githubusercontent.com/enactic/openarm/main/README.md'),
('Yale OpenHand T42','夹爪','https://www.eng.yale.edu/grablab/openhand/',''),
('Festo DHAS Fin Ray','柔顺夹指','https://ftp.festo.com/public/PNEUMATIC/SOFTWARE_SERVICE/Documentation/2021/US/DHAS_ENUS.PDF',''),
('Festo FlexShapeGripper','仿生夹爪','https://media.festo.com/media/113635_documentation.pdf',''),
('Pisa IIT SoftHand','欠驱动手','https://arpi.unipi.it/retrieve/e0d6c92d-adb0-fcf8-e053-d805fe0aa794/PisaIIT_SoftHand_0.pdf',''),
('LEAP Hand','灵巧手','https://arxiv.org/abs/2309.06440','https://arxiv.org/pdf/2309.06440'),
('AmazingHand','灵巧手','https://github.com/pollen-robotics/AmazingHand','https://raw.githubusercontent.com/pollen-robotics/AmazingHand/main/README.md'),
('Robotiq 2F-85','自适应夹爪','https://assets.robotiq.com/website-assets/support_documents/document/2F-85_2F-140_UR_PDF_20210623.pdf',''),
('OnRobot RG2','夹爪','https://onrobot.com/en/products/rg2-finger-gripper',''),
('RBO Hand 3','气动柔性手','https://www.tu.berlin/robotics/forschungsgebiete/infrastruktur-and-tutorials/offene-ressourcen/building-your-own-rbo-hand-3',''),
('Shadow Dexterous Hand','腱驱动手','https://shadowrobot.com/dexterous-hand-series/',''),
('Festo Bionic Handling Assistant','连续体机械臂','https://media.festo.com/media/113684_documentation.pdf',''),
('Festo BionicKangaroo','弹性储能跳跃','https://media.festo.com/media/113655_documentation.pdf',''),
('Salto','跳跃机构','https://people.eecs.berkeley.edu/~ronf/Salto.html',''),
('RHex','柔顺六足','https://publications.ri.cmu.edu/rhex-a-biologically-inspired-hexapod-runner',''),
('Pleurobot','多段脊柱','https://www.epfl.ch/labs/biorob/research/amphibious/pleurobot/',''),
('HEBI X5模块','模块驱动','https://docs.hebi.us/resources/datasheets/X-SeriesDatasheet.pdf',''),
('ATI QC-11','快换连接','https://www.ati-ia.com/products/toolchanger/qc.aspx?id=qc-11',''),
('Festo BionicWheelBot','变形机构','https://www.festo.com/ch/de/e/ueber-festo/forschung-und-entwicklung/bionic-learning-network/bionische-laufroboter/bionicwheelbot-id_32767/',''),
]

class TextParser(HTMLParser):
    def __init__(self):super().__init__();self.block=0;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','svg','noscript'):self.block+=1
        if tag in ('p','br','h1','h2','h3','h4','li','tr','div'):self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style','svg','noscript'):self.block=max(0,self.block-1)
    def handle_data(self,data):
        if not self.block:self.parts.append(data)

def fetch(index,entry):
    name,group,url,fetchurl=entry;number=f'R{index:02}'
    result={'编号':number,'名称':name,'类别':group,'原始来源':url,'请求地址':fetchurl or url,'抓取日期':datetime.date.today().isoformat(),'研究状态':'尚待阅读提炼'}
    try:
        req=urllib.request.Request(fetchurl or url,headers={'User-Agent':'Mozilla/5.0 (compatible; MechanicalReferenceReview/1.0)'})
        try:
            with urllib.request.urlopen(req,timeout=20) as response:
                data=response.read(20_000_001);result['最终地址']=response.url;kind=response.headers.get('Content-Type','')
        except urllib.error.URLError as e:
            if 'CERTIFICATE_VERIFY_FAILED' not in str(e):raise
            # Schannel uses Windows trusted roots; never disable certificate validation.
            tmp=DEST/(number+'.download')
            proc=subprocess.run(['curl.exe','--fail','--location','--max-time','45','--max-filesize','20000000','--silent','--show-error',fetchurl or url,'--output',str(tmp),'--write-out','%{url_effective}\n%{content_type}'],capture_output=True,text=True,timeout=50)
            if proc.returncode:raise RuntimeError(proc.stderr.strip())
            data=tmp.read_bytes();tmp.unlink();info=proc.stdout.splitlines();result['最终地址']=info[0];kind=info[-1] if len(info)>1 else ''
            result['传输说明']='Windows Schannel证书验证；未关闭TLS验证'
        if len(data)>20_000_000:raise ValueError('source exceeds 20MB cap')
        ispdf=data.startswith(b'%PDF')
        result['文件字节']=len(data);result['SHA256']=hashlib.sha256(data).hexdigest()
        source=DEST/(number+('.pdf' if ispdf else '.md' if 'raw.githubusercontent.com' in (fetchurl or url) else '.html'))
        source.write_bytes(data)
        if ispdf:
            with pymupdf.open(stream=data,filetype='pdf') as doc:
                text='\n'.join(f'\n[PAGE {i+1}]\n'+page.get_text() for i,page in enumerate(doc));result['PDF页数']=len(doc)
        else:
            text=data.decode('utf-8',errors='replace')
            if 'html' in kind or '<html' in text[:1000].lower():
                p=TextParser();p.feed(text);text=''.join(p.parts)
        text=re.sub(r'[ \t]+',' ',text);text=re.sub(r'\n\s*\n+','\n\n',text).strip()
        target=DEST/(number+'.txt');target.write_text(text,encoding='utf-8')
        if len(text)<180:raise ValueError('too little readable text')
        result.update(抓取状态='可读取文本',文本文件=str(target),原始快照=str(source),文本字符数=len(text))
    except Exception as e:result.update(抓取状态='失败待补充',错误=str(e))
    return result

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');target=ROOT/'research/参考机械来源抓取.json'
    selected=set(sys.argv[1:]);old=json.loads(target.read_text(encoding='utf-8')) if target.exists() else []
    result={r['编号']:r for r in old}
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks={pool.submit(fetch,i,e):i for i,e in enumerate(SOURCES,1) if not selected or f'R{i:02}' in selected}
        for task in as_completed(tasks):
            r=task.result();result[r['编号']]=r
            target.write_text(json.dumps(sorted(result.values(),key=lambda r:r['编号']),ensure_ascii=False,indent=2),encoding='utf-8')
            print(r['编号'],r['名称'],r['抓取状态'],r.get('文本字符数',r.get('错误')),flush=True)
