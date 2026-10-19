from sw_core import *
import pymupdf

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sw=connect();sw.CommandInProgress=True
    path=ROOT/'drawings/parts/L01_大腿连杆.SLDDRW';d=cast(sw.OpenDoc6(str(path),3,1,'',0,0)[0],'IModelDoc2')
    try:
        ext=cast(d.Extension,'IModelDocExtension')
        sheet=cast(cast(d,'IDrawingDoc').GetCurrentSheet(),'ISheet')
        setup=cast(sheet.PageSetup,'IPageSetup');setup.PrinterPaperSize=8;setup.Orientation=2;setup.ScaleToFit=True;setup.HighQuality=True
        out=ROOT/'tmp/L01_print.pdf'
        spec=cast(ext.GetPrintSpecification(),'IPrintSpecification');spec.PrinterQueue='Microsoft Print to PDF';spec.PrintFile=str(out);spec.PrintToFile=True
        spec.NumberOfCopies=1;spec.ConvertToHighQuality=True;spec.ResetPrintRange();spec.AddPrintRange(1,1);spec.PrintBackground=False
        print('PRINT_BEGIN_TO_VIRTUAL_PDF',flush=True)
        ext.PrintOut4('Microsoft Print to PDF',str(out),spec)
        print('PRINT_RETURNED',out.exists(),flush=True)
        if out.exists():
            f=pymupdf.open(out);print('PRINT_TEXT',f[0].get_text()[:1000],flush=True)
            f[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(str(ROOT/'previews/drawings/L01_打印PDF.png'))
        view=cast(d.ActiveView,'IModelView');print('VIEW_FRAME',view.FrameWidth,view.FrameHeight,'SCALE',view.Scale2)
        d.ViewZoomtofit2();view.Scale2=view.Scale2*.75;d.GraphicsRedraw2()
        print('BMP',d.SaveBMP(str(ROOT/'previews/drawings/L01_完整图纸.bmp'),2400,1697),flush=True)
    finally:sw.CloseDoc(d.GetTitle());sw.CommandInProgress=False
