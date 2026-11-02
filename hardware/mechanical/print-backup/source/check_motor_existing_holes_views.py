"""Four-view QA of actual carrier/seat assemblies; not a fabrication drawing."""
from pathlib import Path
import cadquery as cq
import vtk,json
from PIL import Image,ImageDraw,ImageFont
B=Path(__file__).resolve().parents[1];O=B/'motor-existing-holes-20261102'
def actor(shape,color):
    vertices,faces=shape.tessellate(.14);pts=vtk.vtkPoints();cells=vtk.vtkCellArray()
    for v in vertices:pts.InsertNextPoint(v.x,v.y,v.z)
    for f in faces:
        t=vtk.vtkTriangle()
        for i,j in enumerate(f):t.GetPointIds().SetId(i,j)
        cells.InsertNextCell(t)
    poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells);mp=vtk.vtkPolyDataMapper();mp.SetInputData(poly)
    a=vtk.vtkActor();a.SetMapper(mp);a.GetProperty().SetColor(*color);return a
for name in ['LEFT','RIGHT']:
    carrier=cq.importers.importStep(str(O/'step'/f'D06_CARRIER_{name}_ASSEMBLY.step')).val();seat=cq.importers.importStep(str(O/'step'/f'D06_SEAT_{name}_ASSEMBLY.step')).val()
    bb=carrier.BoundingBox();cx=(bb.xmin+bb.xmax)/2;cy=(bb.ymin+bb.ymax)/2
    canvas=Image.new('RGB',(1500,1100),'white');draw=ImageDraw.Draw(canvas)
    for i,(view,delta,up) in enumerate([('TOP',(0,0,180),(0,1,0)),('FRONT',(0,-180,0),(0,0,1)),('RIGHT',(180,0,0),(0,0,1)),('ISOMETRIC',(-100,-140,-110),(0,0,1))]):
        ren=vtk.vtkRenderer();ren.SetBackground(1,1,1);ren.AddActor(actor(carrier,(.29,.58,.69)));ren.AddActor(actor(seat,(.88,.62,.26)))
        cam=ren.GetActiveCamera();cam.SetPosition(cx+delta[0],cy+delta[1],4+delta[2]);cam.SetFocalPoint(cx,cy,4);cam.SetViewUp(*up);cam.ParallelProjectionOn();ren.ResetCamera()
        win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(730,510);win.AddRenderer(ren);win.Render()
        f=vtk.vtkWindowToImageFilter();f.SetInput(win);f.Update();p=O/'checks'/f'{name}_{view}.png';wr=vtk.vtkPNGWriter();wr.SetFileName(str(p));wr.SetInputConnection(f.GetOutputPort());wr.Write();win.Finalize()
        x=(i%2)*750;y=(i//2)*550;canvas.paste(Image.open(p),(x,y+30));draw.text((x+20,y),f'{name} {view}',font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25),fill='#243c48')
    canvas.save(O/'checks'/f'{name}_four_views.png')
print('Four-view geometry QA contact sheets created')
