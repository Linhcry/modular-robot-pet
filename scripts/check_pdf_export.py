from sw_core import *
import pymupdf

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.CommandInProgress=True
    p=ROOT/'drawings/parts/L01_大腿连杆.SLDDRW';d=cast(sw.OpenDoc6(str(p),3,1,'',0,0)[0],'IModelDoc2')
    try:
        for font in ('SimSun','Arial'):
            v=cast(d,'IDrawingDoc').GetFirstView();count=0
            while v:
                v=cast(v,'IView');n=v.GetFirstNote()
                while n:
                    n=cast(n,'INote');a=cast(n.GetAnnotation(),'IAnnotation')
                    fmt=cast(a.GetTextFormat(0),'ITextFormat');fmt.TypeFaceName=font
                    print('SET_FONT',a.SetTextFormat(0,False,fmt),font,flush=True);count+=1
                    n=n.GetNext()
                v=v.GetNextView()
            print('NOTES_CHANGED',count,flush=True)
            out=ROOT/'tmp'/f'font_{font}.pdf'
            pdf=cast(sw.GetExportFileData(1),'IExportPdfData');pdf.ViewPdfAfterSaving=False;pdf.SetSheets(3,VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,list(cast(d,'IDrawingDoc').GetSheetNames())))
            d.ClearSelection2(True)
            r=cast(d.Extension,'IModelDocExtension').SaveAs(str(out),0,1,pdf,0,0)
            f=pymupdf.open(out);print('FONT_EXPORT',font,r,'text',f[0].get_text()[:1000],flush=True)
            if r[0] and r[1]==0:
                save(d,p)
                f[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(str(ROOT/'previews/drawings'/f'font_{font}.png'))
                break
    finally:sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False
