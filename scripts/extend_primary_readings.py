"""Refresh specified primary mechanical sources without changing unrelated rows."""
from collect_mechanism_references import *
UPDATES={
5:'https://mangdangroboticsclub.github.io/MiniPupperDocs/en/guide/Assembly/MiniPupper.html',
6:'https://guide.petoi.com/product/bittle-x-v2/quick-start-guide/assembling',
16:'https://arxiv.org/html/2502.00893v2',
17:'https://lite.berkeley-humanoid.org/static/paper/demonstrating-berkeley-humanoid-lite.pdf',
19:'https://raw.githubusercontent.com/apirrone/Open_Duck_Mini/v2/docs/assembly_guide.md',
28:'https://source-robotics.github.io/PAROL-docs/page2_2/',
37:'https://www.festo.com/us/en/e/about-festo/research-and-development/bionic-learning-network/bionic-grippers-and-soft-robots/flexshapegripper-id_33444',
45:'https://www.festo.com/au/en/e/about-festo/research-and-development/bionic-learning-network/bionic-grippers-and-soft-robots/bionic-handling-assistant-id_33759/',
46:'https://www.festo.com/PDF_Flip/corp/Festo_BionicKangaroo/en/',
47:'https://funginstitute.berkeley.edu/news/by-leaps-and-bounds-how-the-biomimetic-millisystem-labs-salto-robot-reaches-new-heights/',
52:'https://www.festo.com/PDF_Flip/corp/Festo_BionicWheelBot/en/files/assets/common/downloads/Festo_BionicWheelBot_en.pdf?uni=d750f1e6b535c34381c1078308358bc5',
}
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    target=ROOT/'research/参考机械来源抓取.json';old=json.loads(target.read_text(encoding='utf-8'));rows={r['编号']:r for r in old}
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks={pool.submit(fetch,i,(*SOURCES[i-1][:2],u,'')):i for i,u in UPDATES.items()}
        for f in as_completed(tasks):
            r=f.result();print(r['编号'],r['抓取状态'],r.get('文本字符数',r.get('错误')),flush=True)
            if r['抓取状态']=='可读取文本':rows[r['编号']]=r
    target.write_text(json.dumps(sorted(rows.values(),key=lambda r:r['编号']),ensure_ascii=False,indent=2),encoding='utf-8')
