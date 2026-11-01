from pathlib import Path
import vtk,json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]/'labeled-bases-20261101';(ROOT/'preview').mkdir(exist_ok=True)
records=json.loads((ROOT/'checks/labels.json').read_text(encoding='utf-8'))['labels']
canvas=Image.new('RGB',(1800,1800),'white');font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',25)
for i,r in enumerate(records):
 reader=vtk.vtkSTLReader();reader.SetFileName(str(ROOT/'parts'/(r['id']+'.stl')));reader.Update()
 mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(reader.GetOutputPort());actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(.28,.56,.69);actor.GetProperty().SetAmbient(.15);actor.GetProperty().SetDiffuse(.85)
 renderer=vtk.vtkRenderer();renderer.SetBackground(1,1,1);renderer.AddActor(actor)
 b=reader.GetOutput().GetBounds();cx=(b[0]+b[1])/2;cy=(b[2]+b[3])/2;cz=(b[4]+b[5])/2
 camera=renderer.GetActiveCamera();camera.SetPosition(cx,cy-50,cz+160);camera.SetFocalPoint(cx,cy,cz);camera.SetViewUp(0,1,0);camera.ParallelProjectionOn();renderer.ResetCamera();camera.Zoom(1.1)
 win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(600,410);win.AddRenderer(renderer);win.Render()
 filt=vtk.vtkWindowToImageFilter();filt.SetInput(win);filt.Update();file=ROOT/'preview'/f"{r['id']}.png";writer=vtk.vtkPNGWriter();writer.SetFileName(str(file));writer.SetInputConnection(filt.GetOutputPort());writer.Write();win.Finalize()
 x=(i%3)*600;y=(i//3)*450;canvas.paste(Image.open(file),(x,y+35));ImageDraw.Draw(canvas).text((x+15,y+5),r['label']+(' (optional)' if not r['in_current_jobs'] else ''),font=font,fill='black')
canvas.save(ROOT/'preview/labels_overview.png')
