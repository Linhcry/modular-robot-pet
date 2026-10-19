from build_camera_carrier import *
from audit_tolerant_head_nuts import place,overlap


def main():
    sw=connect();assert sw.GetDocumentCount()==0;sw.FrameState=C.swWindowMinimized;sw.CommandInProgress=True;d=None
    cat={r['id']:r for r in json.loads(CAT_PATH.read_text(encoding='utf-8'))}
    try:
        d=cast(sw.OpenDoc6(cat['H13_CameraCarrier']['path'],1,3,'',0,0)[0],'IModelDoc2')
        carrier=place(sw,body_list(d)[0],CARRIER_XYZ);bounds=carrier.GetBodyBox();sw.CloseDoc(d.GetTitle());d=None
        d=cast(sw.OpenDoc6(cat['V06_CameraModule3']['path'],1,3,'',0,0)[0],'IModelDoc2');hits=[];tested=0
        for index,b in enumerate(body_list(d),1):
            positioned=place(sw,b,CAM_XYZ,CAM_ROT);box=positioned.GetBodyBox()
            if any(box[i]>bounds[i+3] or box[i+3]<bounds[i] for i in range(3)):continue
            tested+=1;hit=overlap(positioned,carrier)
            if hit:hits.append({'相机实体序号':index,'相机实体名':b.Name,'实体包围盒_mm':[v*1000 for v in box],**hit})
        report={'相机实体数':590,'包围盒筛后求交数':tested,'交叠':hits,'托架原点_mm':CARRIER_XYZ,'相机原点_mm':CAM_XYZ}
        (ROOT/'validation/相机板背与托架接触检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False,indent=2))
    finally:
        if d:sw.CloseDoc(d.GetTitle())
        sw.CommandInProgress=False;sw.FrameState=C.swWindowMinimized


if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
