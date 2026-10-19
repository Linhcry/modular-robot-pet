from sw_core import *
import csv

def density(material):
    if '6061' in material:return 2700
    if 'PA12-CF' in material:return 1100
    if 'PA12' in material:return 1010
    if 'TPU' in material:return 1200
    if 'Silicone' in material or '硅胶' in material:return 1100
    if '不锈钢' in material:return 7930
    if 'Steel' in material or '钢' in material:return 7850
    return None

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();rows=json.loads((ROOT/'data/parts_catalog.json').read_text(encoding='utf-8'));out=[];sw.CommandInProgress=True
    try:
        for row in rows:
            if row['kind'] not in ('custom','standard_simplified'):continue
            d=cast(sw.OpenDoc6(row['path'],1,1,'',0,0)[0],'IModelDoc2');assert d
            volume=sum(b.GetMassProperties(1)[3] for b in body_list(d));rho=density(row['material_assumption'])
            out.append({'编号':row['id'],'名称':row['name'],'实体体积_mm3':volume*1e9,'假设密度_kg_m3':rho,'估计单件质量_g':volume*rho*1000 if rho else None,'材料说明':row['material_assumption'],'说明':'原生实体体积×假设密度；打印填充、涂层、嵌件及制造公差未计'})
            sw.CloseDoc(d.GetTitle());print(row['name'],round(volume*rho*1000,2) if rho else 'density unknown',flush=True)
            (ROOT/'validation/零件体积与质量假设.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
        with (ROOT/'data/零件体积与质量假设.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    finally:sw.CommandInProgress=False
